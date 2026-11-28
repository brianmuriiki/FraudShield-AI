from datetime import date
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.constants import ANALYTICS_ROLES
from app.core.dependencies import require_roles
from app.database.session import get_db
from app.models.user import User
from app.services import report_service as svc

router = APIRouter(prefix="/reports", tags=["Reports"])
_guard = require_roles(*ANALYTICS_ROLES)


def _check(date_from: Optional[date], date_to: Optional[date]) -> None:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(400, "date_from must not be after date_to")


@router.get("/summary")
def summary(date_from: Optional[date] = None, date_to: Optional[date] = None,
            db: Session = Depends(get_db), _: User = Depends(_guard)):
    _check(date_from, date_to)
    return svc.summary_report(db, date_from, date_to)


@router.get("/export")
def export(format: Literal["csv", "pdf"] = Query("csv"), date_from: Optional[date] = None,
           date_to: Optional[date] = None, db: Session = Depends(get_db), _: User = Depends(_guard)):
    _check(date_from, date_to)
    if format == "pdf":
        raise HTTPException(501, "PDF export is not implemented yet")
    return Response(
        content=svc.transactions_csv(db, date_from, date_to),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="fraudshield_transactions.csv"'},
    )
