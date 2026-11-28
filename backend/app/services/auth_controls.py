"""Shared-database authentication throttling and JWT revocation helpers."""
from datetime import datetime, timedelta, timezone
import hashlib
import hmac

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.security import LoginAttempt, RevokedToken


def _digest(namespace: str, value: str) -> str:
    return hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        f"{namespace}:{value}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def login_keys(email: str, source_ip: str | None) -> tuple[str, str]:
    account_key = _digest("account", email.strip().lower())
    source_key = _digest("source", source_ip or "unknown")
    return account_key, source_key


def login_is_limited(db: Session, email: str, source_ip: str | None) -> bool:
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=settings.LOGIN_RATE_WINDOW_MINUTES)
    account_key, source_key = login_keys(email, source_ip)
    db.execute(delete(LoginAttempt).where(LoginAttempt.created_at < now - timedelta(days=1)))
    account_count = db.scalar(
        select(func.count()).select_from(LoginAttempt).where(
            LoginAttempt.account_key == account_key, LoginAttempt.created_at >= window_start
        )
    ) or 0
    source_count = db.scalar(
        select(func.count()).select_from(LoginAttempt).where(
            LoginAttempt.source_key == source_key, LoginAttempt.created_at >= window_start
        )
    ) or 0
    return account_count >= settings.LOGIN_RATE_ACCOUNT_LIMIT or source_count >= settings.LOGIN_RATE_SOURCE_LIMIT


def record_login_failure(db: Session, email: str, source_ip: str | None) -> None:
    account_key, source_key = login_keys(email, source_ip)
    db.add(LoginAttempt(account_key=account_key, source_key=source_key))


def token_is_revoked(db: Session, jti: str) -> bool:
    token = db.get(RevokedToken, jti)
    if token is None:
        return False
    expires_at = token.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at <= datetime.now(timezone.utc):
        db.delete(token)
        db.commit()
        return False
    return True


def revoke_token(db: Session, *, jti: str, user_id: int, expires_at: datetime) -> None:
    now = datetime.now(timezone.utc)
    db.execute(delete(RevokedToken).where(RevokedToken.expires_at < now))
    db.merge(RevokedToken(jti=jti, user_id=user_id, expires_at=expires_at))
