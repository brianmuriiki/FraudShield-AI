import csv
import io
from datetime import date
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.services import analytics_service as an
from app.utils.helpers import date_bounds, utcnow

MAX_EXPORT_ROWS = 50_000


def summary_report(db: Session, date_from: Optional[date], date_to: Optional[date]) -> Dict[str, Any]:
    return {
        "generated_at": utcnow().isoformat().replace("+00:00", "Z"),
        "period": {"date_from": date_from, "date_to": date_to},
        "overview": an.overview(db, date_from, date_to),
        "transaction_types": an.transaction_types(db, date_from, date_to)["types"],
        "investigations": an.investigations_analytics(db, date_from, date_to),
        "exports_available": ["csv"],
        "exports_planned": ["pdf"],
    }


def transactions_csv(db: Session, date_from: Optional[date], date_to: Optional[date]) -> str:
    start, end = date_bounds(date_from, date_to)
    stmt = select(Transaction).order_by(Transaction.created_at.desc()).limit(MAX_EXPORT_ROWS)
    if start:
        stmt = stmt.where(Transaction.created_at >= start)
    if end:
        stmt = stmt.where(Transaction.created_at < end)
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["transaction_id", "created_at_utc", "step", "transaction_type", "amount", "oldbalanceOrg",
                "oldbalanceDest", "fraud_score", "threshold", "prediction", "risk_level", "investigation_status"])
    for t in db.scalars(stmt):
        w.writerow([t.transaction_reference, t.created_at.isoformat(), t.step, t.transaction_type, t.amount,
                    t.oldbalanceOrg, t.oldbalanceDest, t.fraud_score, t.threshold, t.prediction,
                    t.risk_level, t.investigation_status])
    return buf.getvalue()
