from typing import List, Optional, Tuple, Union

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.constants import (
    CLOSED_STATUSES,
    OPEN_STATUSES,
    REVIEWER_ROLES,
    TX_AWAITING,
    InvestigationOutcome,
    Role,
)
from app.core.exceptions import BadRequestError, ConflictError, NotFoundError, PermissionDeniedError
from app.models.audit_log import AuditLog
from app.models.investigation import Investigation, InvestigationNote
from app.models.user import User
from app.schemas.investigation import InvestigationCreate, InvestigationUpdate
from app.services.audit_service import log_action
from app.services.transaction_service import get_transaction_or_404
from app.utils.helpers import new_reference, utcnow

_REVIEWERS = {r.value for r in REVIEWER_ROLES}
_ASSIGNABLE = {Role.ADMINISTRATOR.value, Role.SENIOR_ANALYST.value, Role.FRAUD_ANALYST.value}
_PRIORITY_BY_RISK = {"High": "High", "Elevated": "Medium", "Moderate": "Low", "Low": "Low"}


def _is_reviewer(user: User) -> bool:
    return user.role in _REVIEWERS


def get_investigation_or_404(db: Session, ident: Union[str, int]) -> Investigation:
    inv = db.scalar(select(Investigation).where(Investigation.investigation_reference == str(ident)))
    if inv is None and str(ident).isdigit():
        inv = db.get(Investigation, int(ident))
    if inv is None:
        raise NotFoundError("Investigation not found")
    return inv


def _validate_assignee(db: Session, analyst_id: int) -> User:
    analyst = db.get(User, analyst_id)
    if analyst is None or not analyst.is_active:
        raise BadRequestError("Assigned analyst does not exist or is inactive")
    if analyst.role not in _ASSIGNABLE:
        raise BadRequestError("Investigations can only be assigned to fraud analysts, senior analysts or administrators")
    return analyst


def create_investigation(db: Session, payload: InvestigationCreate, user: User, ip: Optional[str]) -> Investigation:
    tx = get_transaction_or_404(db, str(payload.transaction_id))
    active = db.scalar(
        select(Investigation.id).where(
            Investigation.transaction_id == tx.id, Investigation.status.in_(OPEN_STATUSES)
        )
    )
    if active:
        raise ConflictError("An open investigation already exists for this transaction")

    if payload.assigned_analyst_id is not None:
        if not _is_reviewer(user):
            raise PermissionDeniedError("Only senior analysts and administrators can assign investigations")
        _validate_assignee(db, payload.assigned_analyst_id)

    reference = new_reference("INV")
    while db.scalar(select(Investigation.id).where(Investigation.investigation_reference == reference)):
        reference = new_reference("INV")

    inv = Investigation(
        investigation_reference=reference,
        transaction_id=tx.id,
        assigned_analyst_id=payload.assigned_analyst_id,
        created_by_id=user.id,
        status="New",
        outcome=InvestigationOutcome.PENDING.value,
        priority=(payload.priority.value if payload.priority else _PRIORITY_BY_RISK.get(tx.risk_level, "Medium")),
    )
    inv.transaction = tx
    tx.investigation_status = "New"
    db.add(inv)
    db.flush()
    if payload.notes:
        db.add(InvestigationNote(investigation_id=inv.id, author_id=user.id, content=payload.notes))
    log_action(db, action="investigation_created", entity_type="investigation", entity_id=reference,
               description=f"Investigation opened for transaction {tx.transaction_reference}",
               user_id=user.id, ip_address=ip)
    if payload.assigned_analyst_id is not None:
        log_action(db, action="investigation_assigned", entity_type="investigation", entity_id=reference,
                   description=f"Assigned to user {payload.assigned_analyst_id}", user_id=user.id, ip_address=ip)
    db.commit()
    db.refresh(inv)
    return inv


def list_investigations(
    db: Session, *, page: int, page_size: int, status: Optional[str] = None, outcome: Optional[str] = None,
    priority: Optional[str] = None, assigned_analyst_id: Optional[int] = None,
    transaction_id: Optional[str] = None, search: Optional[str] = None,
) -> Tuple[List[Investigation], int]:
    conds = []
    if status:
        conds.append(Investigation.status == status)
    if outcome:
        conds.append(Investigation.outcome == outcome)
    if priority:
        conds.append(Investigation.priority == priority)
    if assigned_analyst_id is not None:
        conds.append(Investigation.assigned_analyst_id == assigned_analyst_id)
    if search:
        conds.append(func.upper(Investigation.investigation_reference).contains(search.upper(), autoescape=True))
    count_stmt = select(func.count()).select_from(Investigation)
    stmt = select(Investigation)
    if transaction_id:
        tx = get_transaction_or_404(db, transaction_id)
        conds.append(Investigation.transaction_id == tx.id)
    if conds:
        count_stmt, stmt = count_stmt.where(*conds), stmt.where(*conds)
    total = db.scalar(count_stmt) or 0
    rows = db.scalars(
        stmt.order_by(Investigation.created_at.desc(), Investigation.id.desc())
        .offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(rows), total


def update_investigation(
    db: Session, inv: Investigation, payload: InvestigationUpdate, user: User, ip: Optional[str]
) -> Investigation:
    data = payload.model_dump(exclude_unset=True)
    if not data:
        raise BadRequestError("No fields provided to update")
    reviewer = _is_reviewer(user)
    ref = inv.investigation_reference

    if inv.status in CLOSED_STATUSES and not reviewer:
        raise PermissionDeniedError("Only senior analysts and administrators can modify a resolved or closed investigation")

    new_status = data["status"].value if data.get("status") else inv.status
    new_outcome = data["outcome"].value if data.get("outcome") else inv.outcome

    if "outcome" in data and new_outcome != inv.outcome and not reviewer:
        raise PermissionDeniedError("Only senior analysts and administrators can record investigation outcomes")
    if "priority" in data and not reviewer and data["priority"].value != inv.priority:
        raise PermissionDeniedError("Only senior analysts and administrators can change priority")
    if "assigned_analyst_id" in data and data["assigned_analyst_id"] != inv.assigned_analyst_id and not reviewer:
        raise PermissionDeniedError("Only senior analysts and administrators can assign investigations")
    if new_status in CLOSED_STATUSES and new_status != inv.status and not reviewer:
        raise PermissionDeniedError("Only senior analysts and administrators can resolve or close investigations")
    if new_status in CLOSED_STATUSES and new_outcome == InvestigationOutcome.PENDING.value:
        raise BadRequestError("An outcome other than 'Pending' is required to resolve or close an investigation")

    changed = False
    if "assigned_analyst_id" in data and data["assigned_analyst_id"] != inv.assigned_analyst_id:
        target = data["assigned_analyst_id"]
        if target is not None:
            _validate_assignee(db, target)
        log_action(db, action="investigation_assigned", entity_type="investigation", entity_id=ref,
                   description=f"Assignee changed from {inv.assigned_analyst_id} to {target}",
                   user_id=user.id, ip_address=ip)
        inv.assigned_analyst_id = target
        changed = True
    if "priority" in data and data["priority"].value != inv.priority:
        log_action(db, action="investigation_priority_changed", entity_type="investigation", entity_id=ref,
                   description=f"Priority changed from {inv.priority} to {data['priority'].value}",
                   user_id=user.id, ip_address=ip)
        inv.priority = data["priority"].value
        changed = True
    if new_outcome != inv.outcome:
        log_action(db, action="investigation_outcome_changed", entity_type="investigation", entity_id=ref,
                   description=f"Outcome changed from {inv.outcome} to {new_outcome}",
                   user_id=user.id, ip_address=ip)
        inv.outcome = new_outcome
        changed = True
    if new_status != inv.status:
        log_action(db, action="investigation_status_changed", entity_type="investigation", entity_id=ref,
                   description=f"Status changed from {inv.status} to {new_status}",
                   user_id=user.id, ip_address=ip)
        inv.status = new_status
        inv.transaction.investigation_status = new_status
        if new_status in CLOSED_STATUSES:
            inv.resolved_at = inv.resolved_at or utcnow()
        else:
            inv.resolved_at = None
        changed = True

    if changed:
        inv.updated_at = utcnow()
        db.commit()
        db.refresh(inv)
    return inv


def add_note(db: Session, inv: Investigation, content: str, user: User, ip: Optional[str]) -> InvestigationNote:
    note = InvestigationNote(investigation_id=inv.id, author_id=user.id, content=content.strip())
    db.add(note)
    inv.updated_at = utcnow()
    log_action(db, action="investigation_note_added", entity_type="investigation",
               entity_id=inv.investigation_reference, description="Analyst note added",
               user_id=user.id, ip_address=ip)
    db.commit()
    db.refresh(note)
    return note


def get_history(db: Session, inv: Investigation) -> List[AuditLog]:
    return list(
        db.scalars(
            select(AuditLog)
            .where(AuditLog.entity_type == "investigation", AuditLog.entity_id == inv.investigation_reference)
            .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
        ).all()
    )
