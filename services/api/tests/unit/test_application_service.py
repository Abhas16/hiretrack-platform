import uuid

import pytest

from hiretrack_api.core.exceptions import (
    InvalidInputError,
    InvalidStatusTransitionError,
    NotFoundError,
)
from hiretrack_api.models import Application, Company
from hiretrack_api.repositories.application_repository import ApplicationFilters
from hiretrack_api.schemas.application import ApplicationCreate, ApplicationUpdate
from hiretrack_api.services.application_service import csv_safe
from hiretrack_common.domain.enums import ApplicationStatus as S

from .conftest import FIXED_NOW, AppServiceKit


def _create(
    kit: AppServiceKit, user_id: uuid.UUID, status: S = S.WISHLIST, company: str = "Atlassian"
) -> Application:
    return kit.service.create(
        user_id, ApplicationCreate(company_name=company, role="DevOps Engineer", status=status)
    )


def test_create_finds_or_creates_company_case_insensitively(
    kit: AppServiceKit, user_id: uuid.UUID
) -> None:
    first = _create(kit, user_id, company="Atlassian")
    second = _create(kit, user_id, company="atlassian")

    assert first.company is second.company
    assert len(kit.companies.items) == 1


def test_create_as_wishlist_has_no_applied_date(kit: AppServiceKit, user_id: uuid.UUID) -> None:
    application = _create(kit, user_id, status=S.WISHLIST)

    assert application.applied_at is None
    assert [(h.from_status, h.to_status) for h in kit.apps.history] == [(None, S.WISHLIST)]
    assert kit.uow.commits == 1


def test_create_as_applied_sets_applied_date(kit: AppServiceKit, user_id: uuid.UUID) -> None:
    assert _create(kit, user_id, status=S.APPLIED).applied_at == FIXED_NOW


def test_valid_status_change_records_history_and_applied_date(
    kit: AppServiceKit, user_id: uuid.UUID
) -> None:
    application = _create(kit, user_id)

    updated = kit.service.change_status(user_id, application.id, S.APPLIED)

    assert updated.status == S.APPLIED
    assert updated.applied_at == FIXED_NOW
    assert updated.status_changed_at == FIXED_NOW
    assert [(h.from_status, h.to_status) for h in kit.apps.history] == [
        (None, S.WISHLIST),
        (S.WISHLIST, S.APPLIED),
    ]


def test_invalid_status_change_is_rejected_without_side_effects(
    kit: AppServiceKit, user_id: uuid.UUID
) -> None:
    application = _create(kit, user_id, status=S.APPLIED)
    kit.service.change_status(user_id, application.id, S.INTERVIEW)
    commits_before, history_before = kit.uow.commits, len(kit.apps.history)

    with pytest.raises(InvalidStatusTransitionError) as error:
        kit.service.change_status(user_id, application.id, S.APPLIED)

    assert error.value.status_code == 409
    assert application.status == S.INTERVIEW
    assert kit.uow.commits == commits_before
    assert len(kit.apps.history) == history_before


def test_other_users_application_is_not_found(kit: AppServiceKit, user_id: uuid.UUID) -> None:
    application = _create(kit, user_id)

    with pytest.raises(NotFoundError):
        kit.service.change_status(uuid.uuid4(), application.id, S.APPLIED)


def test_create_with_unknown_company_id_is_not_found(
    kit: AppServiceKit, user_id: uuid.UUID
) -> None:
    with pytest.raises(NotFoundError):
        kit.service.create(user_id, ApplicationCreate(company_id=uuid.uuid4(), role="SRE"))


def test_update_cannot_null_a_required_field(kit: AppServiceKit, user_id: uuid.UUID) -> None:
    application = _create(kit, user_id)

    with pytest.raises(InvalidInputError):
        kit.service.update(user_id, application.id, ApplicationUpdate(role=None))


def test_update_can_move_application_to_another_company(
    kit: AppServiceKit, user_id: uuid.UUID
) -> None:
    application = _create(kit, user_id, company="Atlassian")
    other = Company(user_id=user_id, name="Postman")
    kit.companies.add(other)

    kit.service.update(user_id, application.id, ApplicationUpdate(company_id=other.id))

    assert application.company is other


def test_board_groups_by_status_in_board_order(kit: AppServiceKit, user_id: uuid.UUID) -> None:
    _create(kit, user_id, status=S.OFFER)
    _create(kit, user_id, status=S.WISHLIST)

    columns = kit.service.board(user_id, q=None)

    assert [c.status for c in columns] == list(S)
    assert [len(c.items) for c in columns] == [1, 0, 0, 1, 0]


@pytest.mark.parametrize(
    ("raw", "safe"),
    [("=HYPERLINK(1)", "'=HYPERLINK(1)"), ("+1", "'+1"), ("@cmd", "'@cmd"), ("SRE", "SRE")],
)
def test_csv_cells_are_protected_against_formula_injection(raw: str, safe: str) -> None:
    assert csv_safe(raw) == safe


def test_export_csv_has_header_and_one_row_per_application(
    kit: AppServiceKit, user_id: uuid.UUID
) -> None:
    _create(kit, user_id, company="=EVIL()")

    lines = kit.service.export_csv(user_id, ApplicationFilters()).strip().splitlines()

    assert lines[0].startswith("company,role,location,source,status")
    assert lines[1].startswith("'=EVIL(),DevOps Engineer")
