import uuid

from hiretrack_api.core.database import UnitOfWork
from hiretrack_api.core.exceptions import AuthenticationError, ConflictError, ForbiddenError
from hiretrack_api.core.security import (
    TokenService,
    burn_password_check,
    hash_password,
    verify_password,
)
from hiretrack_api.models import User
from hiretrack_api.repositories.user_repository import UserRepository
from hiretrack_api.schemas.auth import RegisterRequest

INVALID_CREDENTIALS = "Invalid email or password"


class AuthService:
    def __init__(
        self,
        users: UserRepository,
        uow: UnitOfWork,
        tokens: TokenService,
        allow_registration: bool = True,
    ) -> None:
        self._users = users
        self._uow = uow
        self._tokens = tokens
        self._allow_registration = allow_registration

    def register(self, data: RegisterRequest) -> User:
        if not self._allow_registration:
            raise ForbiddenError("Registration is disabled")
        email = data.email.lower()
        if self._users.get_by_email(email):
            raise ConflictError("Email is already registered")
        user = User(
            email=email, password_hash=hash_password(data.password), full_name=data.full_name
        )
        self._users.add(user)
        self._uow.commit()
        return user

    def login(self, email: str, password: str) -> tuple[str, int]:
        """Return (access token, expires_in seconds). Same error for unknown email and bad
        password, so the response doesn't reveal which emails exist."""
        user = self._users.get_by_email(email.lower())
        if user is None:
            burn_password_check(password)
            raise AuthenticationError(INVALID_CREDENTIALS)
        if not verify_password(user.password_hash, password) or not user.is_active:
            raise AuthenticationError(INVALID_CREDENTIALS)
        return self._tokens.create_access_token(user.id)

    def authenticate(self, token: str) -> User:
        user_id: uuid.UUID = self._tokens.decode_user_id(token)
        user = self._users.get(user_id)
        if user is None or not user.is_active:
            raise AuthenticationError("Invalid or expired token")
        return user
