from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import INVESTIGATION_ROLES, InvestigationOutcome, InvestigationStatus, Priority
from app.core.dependencies import get_client_ip, require_roles
from app.database.session import get_db
from app.models.user import User
from app.schemas.common import Page, build_page
from app.schemas.investigation import (
    HistoryEntry, InvestigationCreate, InvestigationDetail, InvestigationOut, InvestigationUpdate,
    NoteCreate, NoteOut,
)
from app.services import investigation_service as svc

router = APIRouter(prefix="/investigations", tags=["Investigations"])
analyst = require_roles(*INVESTIGATION_ROLES)


def _detail(db: Session, inv) -> InvestigationDetail:
    detail = InvestigationDetail.model_validate(inv)
    detail.history = [HistoryEntry.model_validate(h) for h in svc.get_history(db, inv)]
    return detail


@router.get("", response_model=Page[InvestigationOut])
def list_investigations(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
    status_: Optional[InvestigationStatus] = Query(None, alias="status"),
    outcome: Optional[InvestigationOutcome] = None,
    priority: Optional[Priority] = None,
    assigned_analyst_id: Optional[int] = None,
    transaction_id: Optional[str] = Query(None, max_length=32),
    search: Optional[str] = Query(None, max_length=64),
    db: Session = Depends(get_db),
    _: User = Depends(analyst),
):
    rows, total = svc.list_investigations(
        db, page=page, page_size=page_size,
        status=status_.value if status_ else None, outcome=outcome.value if outcome else None,
        priority=priority.value if priority else None, assigned_analyst_id=assigned_analyst_id,
        transaction_id=transaction_id, search=search,
    )
    return build_page(rows, total, page, page_size)


@router.post("", response_model=InvestigationDetail, status_code=status.HTTP_201_CREATED)
def create_investigation(
    payload: InvestigationCreate, request: Request, db: Session = Depends(get_db), user: User = Depends(analyst)
):
    inv = svc.create_investigation(db, payload, user, get_client_ip(request))
    return _detail(db, inv)


@router.get("/{investigation_id}", response_model=InvestigationDetail)
def get_investigation(investigation_id: str, db: Session = Depends(get_db), _: User = Depends(analyst)):
    return _detail(db, svc.get_investigation_or_404(db, investigation_id))


@router.patch("/{investigation_id}", response_model=InvestigationDetail)
def update_investigation(
    investigation_id: str, payload: InvestigationUpdate, request: Request,
    db: Session = Depends(get_db), user: User = Depends(analyst),
):
    inv = svc.get_investigation_or_404(db, investigation_id)
    inv = svc.update_investigation(db, inv, payload, user, get_client_ip(request))
    return _detail(db, inv)


@router.post("/{investigation_id}/notes", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def add_note(
    investigation_id: str, payload: NoteCreate, request: Request,
    db: Session = Depends(get_db), user: User = Depends(analyst),
):
    inv = svc.get_investigation_or_404(db, investigation_id)
    return svc.add_note(db, inv, payload.content, user, get_client_ip(request))
