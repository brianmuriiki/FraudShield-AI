from typing import Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def log_action(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: Optional[str] = None,
    description: str = "",
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
) -> AuditLog:
    """Adds an audit row to the session (caller commits). Never pass secrets in `description`."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        description=description[:1000],
        ip_address=ip_address,
    )
    db.add(entry)
    return entry
