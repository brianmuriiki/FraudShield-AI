import logging

from sqlalchemy import select

import app.models  # noqa: F401  (register all tables)
from app.core.config import settings
from app.core.constants import Role
from app.core.security import hash_password
from app.database.session import SessionLocal, engine
from app.models.database import Base
from app.models.user import User

logger = logging.getLogger(__name__)


def init_db() -> None:
    """Create missing tables only. Never drops or overwrites existing data."""
    Base.metadata.create_all(bind=engine)


def ensure_initial_admin() -> None:
    email = (settings.INITIAL_ADMIN_EMAIL or "").strip().lower()
    password = settings.INITIAL_ADMIN_PASSWORD or ""
    with SessionLocal() as db:
        if email and password:
            if db.scalar(select(User).where(User.email == email)) is None:
                db.add(
                    User(
                        email=email,
                        full_name=settings.INITIAL_ADMIN_NAME,
                        hashed_password=hash_password(password),
                        role=Role.ADMINISTRATOR.value,
                    )
                )
                db.commit()
                logger.info("Initial administrator created: %s", email)
        elif db.scalar(select(User.id).limit(1)) is None:
            logger.warning(
                "No users exist and INITIAL_ADMIN_EMAIL / INITIAL_ADMIN_PASSWORD are not set. "
                "Nobody will be able to log in."
            )
