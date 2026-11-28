"""Password hashing (bcrypt) and JWT helpers (PyJWT)."""
from datetime import datetime, timedelta, timezone
import uuid
from typing import Any, Dict

import bcrypt
import jwt

from app.core.config import settings

_MAX_BCRYPT_BYTES = 72


def hash_password(password: str) -> str:
    raw = password.encode("utf-8")
    if len(raw) > _MAX_BCRYPT_BYTES:
        raise ValueError("Password must be at most 72 bytes")
    return bcrypt.hashpw(raw, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:_MAX_BCRYPT_BYTES], hashed.encode("utf-8"))
    except ValueError:
        return False


# Used to keep login timing similar when the account does not exist.
DUMMY_HASH = hash_password("not-a-real-password")


def create_access_token(user_id: int, role: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "role": role,
        "jti": uuid.uuid4().hex,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Dict[str, Any]:
    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["exp", "sub", "jti"]},
    )
