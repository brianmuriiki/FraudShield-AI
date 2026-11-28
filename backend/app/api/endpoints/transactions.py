from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.constants import INVESTIGATION_ROLES, TransactionType
from app.core.dependencies import get_client_ip, get_current_user, require_roles
from app.database.session import get_db
from app.models.user import User
from app.schemas.common import Page, build_page
from app.schemas.transaction import TransactionInput, TransactionOut
from app.services import transaction_service as svc

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=Page[TransactionOut])
def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=settings.MAX_PAGE_SIZE),
    search: Optional[str] = Query(None, max_length=64, description="Match on transaction reference"),
    transaction_type: Optional[TransactionType] = None,
    prediction: Optional[Literal["Suspicious", "Not Flagged"]] = None,
    risk_level: Optional[Literal["Low", "Moderate", "Elevated", "High"]] = None,
    investigation_status: Optional[str] = Query(None, max_length=32),
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_amount: Optional[float] = Query(None, ge=0),
    max_amount: Optional[float] = Query(None, ge=0),
    sort_by: Literal["created_at", "amount", "fraud_score", "step"] = "created_at",
    sort_order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    rows, total = svc.list_transactions(
        db, page=page, page_size=page_size, search=search,
        transaction_type=transaction_type.value if transaction_type else None,
        prediction=prediction, risk_level=risk_level, investigation_status=investigation_status,
        date_from=date_from, date_to=date_to, min_amount=min_amount, max_amount=max_amount,
        sort_by=sort_by, sort_order=sort_order,
    )
    return build_page(rows, total, page, page_size)


# "/stats" MUST be declared before "/{transaction_id}" or it would be captured as an id.
@router.get("/stats")
def stats(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.transaction_stats(db)


@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionInput,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(*INVESTIGATION_ROLES)),
):
    """Scores and stores a transaction (same scoring path as /predictions/predict)."""
    tx, _ = svc.create_scored_transaction(db, payload, user, get_client_ip(request))
    return tx


@router.get("/{transaction_id}", response_model=TransactionOut)
def get_transaction(transaction_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return svc.get_transaction_or_404(db, transaction_id)
