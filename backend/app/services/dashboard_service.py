from datetime import timedelta
from typing import Any, Dict

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.constants import (
    CLOSED_STATUSES,
    OPEN_STATUSES,
    PRED_SUSPICIOUS,
    RISK_LEVELS,
    TX_AWAITING,
    InvestigationOutcome,
)
from app.models.investigation import Investigation
from app.models.transaction import Transaction
from app.utils.helpers import utcnow

CONFIRMED = InvestigationOutcome.CONFIRMED_FRAUD.value


def get_summary(db: Session, trend_days: int = 30) -> Dict[str, Any]:
    susp = case((Transaction.prediction == PRED_SUSPICIOUS, 1), else_=0)
    susp_amt = case((Transaction.prediction == PRED_SUSPICIOUS, Transaction.amount), else_=0.0)

    total, suspicious, total_amount, suspicious_amount = db.execute(
        select(
            func.count(Transaction.id),
            func.coalesce(func.sum(susp), 0),
            func.coalesce(func.sum(Transaction.amount), 0.0),
            func.coalesce(func.sum(susp_amt), 0.0),
        )
    ).one()

    def count_inv(*conds) -> int:
        return int(db.scalar(select(func.count(Investigation.id)).where(*conds)) or 0)

    confirmed = count_inv(Investigation.outcome == CONFIRMED)
    open_inv = count_inv(Investigation.status.in_(OPEN_STATUSES))
    resolved_inv = count_inv(Investigation.status.in_(CLOSED_STATUSES))
    pending = int(
        db.scalar(select(func.count(Transaction.id)).where(Transaction.investigation_status == TX_AWAITING)) or 0
    )

    risk = {level: 0 for level in RISK_LEVELS}
    risk.update({k: int(v) for k, v in db.execute(
        select(Transaction.risk_level, func.count(Transaction.id)).group_by(Transaction.risk_level)).all()})

    # Daily trend (zero-filled) for the last `trend_days` days
    now = utcnow()
    start = (now - timedelta(days=trend_days - 1)).replace(hour=0, minute=0, second=0, microsecond=0)
    day = func.date(Transaction.created_at)
    rows = db.execute(
        select(day, func.count(Transaction.id), func.coalesce(func.sum(susp), 0))
        .where(Transaction.created_at >= start)
        .group_by(day)
    ).all()
    by_day = {str(d): (int(t), int(s)) for d, t, s in rows}
    trend = []
    for i in range(trend_days):
        d = (start + timedelta(days=i)).date().isoformat()
        t, s = by_day.get(d, (0, 0))
        trend.append({"date": d, "total": t, "suspicious": s})

    # By type: model flags vs. analyst-confirmed fraud (kept separate on purpose)
    flagged = {
        t: (int(n), int(s or 0))
        for t, n, s in db.execute(
            select(Transaction.transaction_type, func.count(Transaction.id), func.sum(susp))
            .group_by(Transaction.transaction_type)
        ).all()
    }
    confirmed_by_type = dict(
        db.execute(
            select(Transaction.transaction_type, func.count(func.distinct(Transaction.id)))
            .join(Investigation, Investigation.transaction_id == Transaction.id)
            .where(Investigation.outcome == CONFIRMED)
            .group_by(Transaction.transaction_type)
        ).all()
    )
    fraud_by_type = [
        {"transaction_type": t, "total": n, "suspicious": s, "confirmed_fraud": int(confirmed_by_type.get(t, 0))}
        for t, (n, s) in sorted(flagged.items())
    ]

    return {
        "total_transactions": int(total),
        "suspicious_transactions": int(suspicious),
        "not_flagged_transactions": int(total) - int(suspicious),
        "confirmed_fraud_cases": confirmed,
        "pending_investigations": pending,
        "open_investigations": open_inv,
        "resolved_investigations": resolved_inv,
        "total_amount": float(total_amount),
        "suspicious_amount": float(suspicious_amount),
        "risk_level_distribution": risk,
        "suspicious_trend": trend,
        "fraud_by_type": fraud_by_type,
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "note": "suspicious_transactions are model flags awaiting human review. "
                "Only confirmed_fraud_cases reflect analyst-verified outcomes.",
    }
