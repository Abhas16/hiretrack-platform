"""Password hashing (Argon2) and JWT access tokens (HS256)."""

import uuid
from datetime import timedelta

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from hiretrack_api.core.exceptions import AuthenticationError
from hiretrack_common.clock import Clock, utcnow

_hasher = PasswordHasher()

# Verifying against this when the email doesn't exist makes "unknown email" and
# "wrong password" take the same time, so attackers can't probe which emails are registered.
_DUMMY_HASH = _hasher.hash("timing-equaliser-not-a-real-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def burn_password_check(password: str) -> None:
    verify_password(_DUMMY_HASH, password)


class TokenService:
    algorithm = "HS256"

    def __init__(self, secret: str, issuer: str, ttl_minutes: int, now: Clock = utcnow) -> None:
        self._secret = secret
        self._issuer = issuer
        self._ttl = timedelta(minutes=ttl_minutes)
        self._now = now

    def create_access_token(self, user_id: uuid.UUID) -> tuple[str, int]:
        """Return (token, seconds until it expires)."""
        issued_at = self._now()
        claims = {
            "sub": str(user_id),
            "iss": self._issuer,
            "iat": issued_at,
            "exp": issued_at + self._ttl,
            "type": "access",
        }
        token = jwt.encode(claims, self._secret, algorithm=self.algorithm)
        return token, int(self._ttl.total_seconds())

    def decode_user_id(self, token: str) -> uuid.UUID:
        try:
            claims = jwt.decode(
                token,
                self._secret,
                algorithms=[self.algorithm],  # never trust the token's own "alg" header
                issuer=self._issuer,
                options={"require": ["sub", "exp", "iat", "iss"]},
            )
            if claims.get("type") != "access":
                raise AuthenticationError("Invalid token type")
            return uuid.UUID(claims["sub"])
        except (jwt.PyJWTError, ValueError) as exc:
            raise AuthenticationError("Invalid or expired token") from exc
