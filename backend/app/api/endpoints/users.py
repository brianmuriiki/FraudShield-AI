from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import Role
from app.core.dependencies import get_client_ip, require_roles
from app.database.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.common import Page, build_page
from app.schemas.user import AnalystOut, AuditLogOut, UserOut, UserUpdate
from app.services.audit_service import log_action
from app.utils.helpers import date_bounds

router = APIRouter(prefix="/users", tags=["Users"])
admin_only = require_roles(Role.ADMINISTRATOR)


@router.get("", response_model=Page[UserOut])
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
):
    total = db.scalar(select(func.count(User.id))) or 0
    rows = db.scalars(select(User).order_by(User.id).offset((page - 1) * page_size).limit(page_size)).all()
    return build_page(list(rows), total, page, page_size)


# NOTE: fixed paths are declared before "/{user_id}"
@router.get("/analysts", response_model=list[AnalystOut])
def assignable_analysts(
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(Role.ADMINISTRATOR, Role.SENIOR_ANALYST)),
):
    """Active users an investigation can be assigned to."""
    roles = [Role.FRAUD_ANALYST.value, Role.SENIOR_ANALYST.value, Role.ADMINISTRATOR.value]
    return db.scalars(select(User).where(User.is_active.is_(True), User.role.in_(roles)).order_by(User.full_name)).all()


@router.get("/audit-logs", response_model=Page[AuditLogOut])
def audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=settings.MAX_PAGE_SIZE),
    action: Optional[str] = Query(None, max_length=64),
    entity_type: Optional[str] = Query(None, max_length=32),
    user_id: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
):
    conds = []
    if action:
        conds.append(AuditLog.action == action)
    if entity_type:
        conds.append(AuditLog.entity_type == entity_type)
    if user_id is not None:
        conds.append(AuditLog.user_id == user_id)
    start, end = date_bounds(date_from, date_to)
    if start:
        conds.append(AuditLog.created_at >= start)
    if end:
        conds.append(AuditLog.created_at < end)
    count_stmt, stmt = select(func.count(AuditLog.id)), select(AuditLog)
    if conds:
        count_stmt, stmt = count_stmt.where(*conds), stmt.where(*conds)
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(
        stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return build_page(list(rows), total, page, page_size)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(admin_only)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only),
):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, "User not found")
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(400, "No fields provided to update")
    ip = get_client_ip(request)
    if user.id == admin.id and (
        ("role" in data and data["role"] != Role.ADMINISTRATOR) or data.get("is_active") is False
    ):
        raise HTTPException(400, "Administrators cannot demote or deactivate their own account")
    if "role" in data and data["role"].value != user.role:
        log_action(db, action="user_role_changed", entity_type="user", entity_id=str(user.id),
                   description=f"Role changed from {user.role} to {data['role'].value}", user_id=admin.id, ip_address=ip)
        user.role = data["role"].value
    if "is_active" in data and data["is_active"] != user.is_active:
        log_action(db, action="user_activation_changed", entity_type="user", entity_id=str(user.id),
                   description=f"is_active set to {data['is_active']}", user_id=admin.id, ip_address=ip)
        user.is_active = data["is_active"]
    if "full_name" in data and data["full_name"].strip():
        user.full_name = data["full_name"].strip()
    db.commit()
    db.refresh(user)
    return user
