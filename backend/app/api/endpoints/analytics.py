from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.constants import ANALYTICS_ROLES
from app.core.dependencies import require_roles
from app.database.session import get_db
from app.models.user import User
from app.services import analytics_service as svc

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class _Range:
    def __init__(self, date_from: Optional[date] = Query(None), date_to: Optional[date] = Query(None)):
        if date_from and date_to and date_from > date_to:
            raise HTTPException(400, "date_from must not be after date_to")
        self.date_from, self.date_to = date_from, date_to


_guard = require_roles(*ANALYTICS_ROLES)


@router.get("/overview")
def overview(r: _Range = Depends(), db: Session = Depends(get_db), _: User = Depends(_guard)):
    return svc.overview(db, r.date_from, r.date_to)


@router.get("/transactions")
def transactions(r: _Range = Depends(), db: Session = Depends(get_db), _: User = Depends(_guard)):
    return svc.transactions_analytics(db, r.date_from, r.date_to)


@router.get("/fraud-trends")
def fraud_trends(r: _Range = Depends(), db: Session = Depends(get_db), _: User = Depends(_guard)):
    return svc.fraud_trends(db, r.date_from, r.date_to)


@router.get("/transaction-types")
def transaction_types(r: _Range = Depends(), db: Session = Depends(get_db), _: User = Depends(_guard)):
    return svc.transaction_types(db, r.date_from, r.date_to)


@router.get("/investigations")
def investigations(r: _Range = Depends(), db: Session = Depends(get_db), _: User = Depends(_guard)):
    return svc.investigations_analytics(db, r.date_from, r.date_to)
