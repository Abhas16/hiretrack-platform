import json
import logging

import pytest
from pydantic import SecretStr

from hiretrack_common.config import DatabaseSettings
from hiretrack_common.domain.enums import ApplicationStatus as S
from hiretrack_common.domain.status import ALLOWED_TRANSITIONS, allowed_targets, can_transition
from hiretrack_common.logging import JsonFormatter, request_id_var

EXPECTED_ALLOWED = {
    (S.WISHLIST, S.APPLIED),
    (S.WISHLIST, S.REJECTED),
    (S.APPLIED, S.INTERVIEW),
    (S.APPLIED, S.WISHLIST),
    (S.APPLIED, S.REJECTED),
    (S.INTERVIEW, S.OFFER),
    (S.INTERVIEW, S.REJECTED),
    (S.OFFER, S.REJECTED),
}


@pytest.mark.parametrize("current", list(S))
@pytest.mark.parametrize("target", list(S))
def test_status_state_machine_matches_spec(current: S, target: S) -> None:
    assert can_transition(current, target) is ((current, target) in EXPECTED_ALLOWED)


def test_every_status_has_an_entry() -> None:
    assert set(ALLOWED_TRANSITIONS) == set(S)


def test_allowed_targets_are_in_board_order() -> None:
    assert allowed_targets(S.APPLIED) == [S.WISHLIST, S.INTERVIEW, S.REJECTED]
    assert allowed_targets(S.REJECTED) == []


def test_json_formatter_includes_extra_fields_and_request_id() -> None:
    formatter = JsonFormatter(service="api")
    record = logging.LogRecord("test", logging.INFO, __file__, 1, "hello %s", ("world",), None)
    record.route = "/api/v1/applications"
    token = request_id_var.set("req-123")
    try:
        line = json.loads(formatter.format(record))
    finally:
        request_id_var.reset(token)

    assert line["message"] == "hello world"
    assert line["service"] == "api"
    assert line["request_id"] == "req-123"
    assert line["route"] == "/api/v1/applications"


def test_database_url_never_prints_password() -> None:
    settings = DatabaseSettings(db_password=SecretStr("s3cret"), db_sslmode="require")
    url = settings.database_url()
    assert "s3cret" not in str(url)  # SQLAlchemy masks it in repr/str
    assert url.password == "s3cret"
    assert url.query["sslmode"] == "require"
