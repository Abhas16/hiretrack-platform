import uuid
from datetime import timedelta

import jwt
import pytest

from hiretrack_api.core.exceptions import AuthenticationError, ConflictError, ForbiddenError
from hiretrack_api.core.security import TokenService, hash_password, verify_password
from hiretrack_api.schemas.auth import RegisterRequest
from hiretrack_api.services.auth_service import AuthService
from hiretrack_common.clock import utcnow

from .conftest import FIXED_NOW, FakeUnitOfWork, FakeUserRepository

SECRET = "unit-test-secret-0123456789abcdefghij"


# PyJWT validates exp/iat against the real clock, so tokens are issued with the real clock too.
def tokens(now=utcnow) -> TokenService:  # type: ignore[no-untyped-def]
    return TokenService(secret=SECRET, issuer="hiretrack-api", ttl_minutes=60, now=now)


def auth_service(allow_registration: bool = True) -> AuthService:
    return AuthService(FakeUserRepository(), FakeUnitOfWork(), tokens(), allow_registration)  # type: ignore[arg-type]


REGISTRATION = RegisterRequest(email="Abhas@Example.com", password="correct-horse", full_name="A")


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("correct-horse")
    assert hashed != "correct-horse"
    assert verify_password(hashed, "correct-horse")
    assert not verify_password(hashed, "wrong")
    assert not verify_password("not-a-hash", "anything")


def test_token_roundtrip() -> None:
    user_id = uuid.uuid4()
    token, expires_in = tokens().create_access_token(user_id)
    assert expires_in == 3600
    assert tokens().decode_user_id(token) == user_id


def test_expired_token_is_rejected() -> None:
    issued_long_ago = tokens(now=lambda: utcnow() - timedelta(days=2))
    token, _ = issued_long_ago.create_access_token(uuid.uuid4())
    with pytest.raises(AuthenticationError):
        tokens().decode_user_id(token)


def test_token_signed_with_another_secret_is_rejected() -> None:
    forged = jwt.encode(
        {"sub": str(uuid.uuid4()), "iss": "hiretrack-api", "iat": FIXED_NOW, "exp": FIXED_NOW},
        "attacker-secret-attacker-secret-attacker",
        algorithm="HS256",
    )
    with pytest.raises(AuthenticationError):
        tokens().decode_user_id(forged)


def test_register_normalizes_email_and_rejects_duplicates() -> None:
    service = auth_service()
    user = service.register(REGISTRATION)
    assert user.email == "abhas@example.com"
    with pytest.raises(ConflictError):
        service.register(REGISTRATION)


def test_register_can_be_disabled() -> None:
    with pytest.raises(ForbiddenError):
        auth_service(allow_registration=False).register(REGISTRATION)


def test_login_success_and_failure_messages_do_not_leak_which_part_was_wrong() -> None:
    service = auth_service()
    user = service.register(REGISTRATION)

    token, _ = service.login("ABHAS@example.com", "correct-horse")
    assert service.authenticate(token).id == user.id

    with pytest.raises(AuthenticationError) as wrong_password:
        service.login("abhas@example.com", "wrong-password")
    with pytest.raises(AuthenticationError) as unknown_email:
        service.login("nobody@example.com", "correct-horse")
    assert wrong_password.value.message == unknown_email.value.message


def test_inactive_user_cannot_log_in() -> None:
    service = auth_service()
    user = service.register(REGISTRATION)
    user.is_active = False
    with pytest.raises(AuthenticationError):
        service.login("abhas@example.com", "correct-horse")
