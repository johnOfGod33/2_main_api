"""JWT and password hashing (aligned with FastAPI OAuth2 + JWT tutorial)."""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError
from pwdlib import PasswordHash

from .config import settings

BCRYPT_MAX_PASSWORD_BYTES = 72

password_hash = PasswordHash.recommended()

# Constant-time path when email is unknown (mitigates login timing attacks).
DUMMY_PASSWORD_HASH = password_hash.hash("dummypassword")


def get_password_hash(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    if expires_delta is not None:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.JWT_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except InvalidTokenError:
        return None
