import uuid
from datetime import datetime
from typing import Literal

from pydantic import EmailStr, Field

from hiretrack_api.schemas.common import ReadModel, WriteModel


class RegisterRequest(WriteModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=120)


class LoginRequest(WriteModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(ReadModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"  # noqa: S105 - OAuth2 token type, not a secret
    expires_in: int


class UserRead(ReadModel):
    id: uuid.UUID
    email: str
    full_name: str
    created_at: datetime
