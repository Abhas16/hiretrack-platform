"""The application status state machine.

    WISHLIST -> APPLIED -> INTERVIEW -> OFFER
    APPLIED  -> WISHLIST               (undo "applied")
    WISHLIST/APPLIED/INTERVIEW/OFFER -> REJECTED
Everything else is invalid (the API answers 409 Conflict).
"""

from hiretrack_common.domain.enums import ApplicationStatus

S = ApplicationStatus

ALLOWED_TRANSITIONS: dict[ApplicationStatus, frozenset[ApplicationStatus]] = {
    S.WISHLIST: frozenset({S.APPLIED, S.REJECTED}),
    S.APPLIED: frozenset({S.INTERVIEW, S.WISHLIST, S.REJECTED}),
    S.INTERVIEW: frozenset({S.OFFER, S.REJECTED}),
    S.OFFER: frozenset({S.REJECTED}),
    S.REJECTED: frozenset(),
}

# Board column order.
STATUS_ORDER: tuple[ApplicationStatus, ...] = (
    S.WISHLIST,
    S.APPLIED,
    S.INTERVIEW,
    S.OFFER,
    S.REJECTED,
)

# Statuses that mean the application was actually sent.
SENT_STATUSES = frozenset({S.APPLIED, S.INTERVIEW, S.OFFER})


def can_transition(current: ApplicationStatus, target: ApplicationStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]


def allowed_targets(current: ApplicationStatus) -> list[ApplicationStatus]:
    """Allowed next statuses, in board order (handy for the UI to enable/disable buttons)."""
    return [status for status in STATUS_ORDER if status in ALLOWED_TRANSITIONS[current]]
