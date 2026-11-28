from datetime import date
from typing import Any, Dict, Optional

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.constants import CLOSED_STATUSES, PRED_SUSPICIOUS, InvestigationOutcome
from app.models.investigation import Investigation
from app.models.transaction import Transaction
from app.services.ml_service import ml_service
from app.utils.helpers import date_bounds

CONFIRMED = InvestigationOutcome.CONFIRMED_FRAUD.value
LEGIT = InvestigationOutcome.LEGITIMATE.value
_SUSP = case((Transaction.prediction == PRED_SUSPICIOUS, 1), else_=0)


def _tx_conds(date_from: Optional[date], date_to: Optional[date]):
    start, end = date_bounds(date_from, date_to)
    conds = []
    if start:
        conds.append(Transaction.created_at >= start)
    if end:
        conds.append(Transaction.created_at < end)
    return conds


def _where(stmt, conds):
    return stmt.where(*conds) if conds else stmt


def overview(db: Session, date_from=None, date_to=None) -> Dict[str, Any]:
    conds = _tx_conds(date_from, date_to)
    total, susp, avg_amount, avg_score = db.execute(
        _where(select(func.count(Transaction.id), func.coalesce(func.sum(_SUSP), 0),
                      func.avg(Transaction.amount), func.avg(Transaction.fraud_score)), conds)
    ).one()
    total, susp = int(total), int(susp)
    inv_total = int(db.scalar(select(func.count(Investigation.id))) or 0)
    confirmed = int(db.scalar(select(func.count(Investigation.id)).where(Investigation.outcome == CONFIRMED)) or 0)
    return {
        "period": {"date_from": date_from, "date_to": date_to},
        "total_transactions": total,
        "suspicious_transactions": susp,
        "suspicious_rate": (susp / total) if total else None,
        "average_amount": float(avg_amount) if avg_amount is not None else None,
        "average_fraud_score": float(avg_score) if avg_score is not None else None,
        "total_investigations": inv_total,
        "confirmed_fraud_cases": confirmed,
        "model_offline_metrics": historical_metrics(),
        "verified_performance": verified_performance(db),
    }


def historical_metrics() -> Dict[str, Any]:
    if not ml_service.loaded:
        return {"available": False, "metrics": None, "source": "unavailable"}
    d = ml_service.describe()
    return {"available": d["metrics"] is not None, "metrics": d["metrics"], "source": d["metrics_source"], "note": d["metrics_note"]}


def transactions_analytics(db: Session, date_from=None, date_to=None) -> Dict[str, Any]:
    conds = _tx_conds(date_from, date_to)
    day = func.date(Transaction.created_at)
    volume = db.execute(
        _where(select(day, func.count(Transaction.id), func.coalesce(func.sum(_SUSP), 0),
                      func.coalesce(func.sum(Transaction.amount), 0.0)), conds)
        .group_by(day).order_by(day)
    ).all()
    buckets = [("< 1,000", None, 1_000), ("1,000 - 9,999", 1_000, 10_000), ("10,000 - 99,999", 10_000, 100_000),
               ("100,000 - 999,999", 100_000, 1_000_000), (">= 1,000,000", 1_000_000, None)]
    dist = []
    for label, lo, hi in buckets:
        c = list(conds)
        if lo is not None:
            c.append(Transaction.amount >= lo)
        if hi is not None:
            c.append(Transaction.amount < hi)
        dist.append({"range": label, "count": int(db.scalar(_where(select(func.count(Transaction.id)), c)) or 0)})
    return {
        "volume_over_time": [
            {"date": str(d), "total": int(n), "suspicious": int(s), "amount": float(a)} for d, n, s, a in volume
        ],
        "amount_distribution": dist,
    }


def fraud_trends(db: Session, date_from=None, date_to=None) -> Dict[str, Any]:
    conds = _tx_conds(date_from, date_to)
    day = func.date(Transaction.created_at)
    flagged = db.execute(
        _where(select(day, func.coalesce(func.sum(_SUSP), 0), func.count(Transaction.id)), conds)
        .group_by(day).order_by(day)
    ).all()
    confirmed = dict(
        db.execute(
            _where(select(day, func.count(func.distinct(Transaction.id)))
                   .join(Investigation, Investigation.transaction_id == Transaction.id)
                   .where(Investigation.outcome == CONFIRMED), conds).group_by(day)
        ).all()
    )
    return {
        "trend": [
            {"date": str(d), "suspicious": int(s), "total": int(t), "confirmed_fraud": int(confirmed.get(d, 0))}
            for d, s, t in flagged
        ],
        "note": "'suspicious' = model flags; 'confirmed_fraud' = analyst-verified outcomes, by transaction date.",
    }


def transaction_types(db: Session, date_from=None, date_to=None) -> Dict[str, Any]:
    conds = _tx_conds(date_from, date_to)
    rows = db.execute(
        _where(select(Transaction.transaction_type, func.count(Transaction.id), func.coalesce(func.sum(_SUSP), 0),
                      func.avg(Transaction.amount), func.coalesce(func.sum(Transaction.amount), 0.0)), conds)
        .group_by(Transaction.transaction_type).order_by(Transaction.transaction_type)
    ).all()
    confirmed = dict(
        db.execute(
            _where(select(Transaction.transaction_type, func.count(func.distinct(Transaction.id)))
                   .join(Investigation, Investigation.transaction_id == Transaction.id)
                   .where(Investigation.outcome == CONFIRMED), conds).group_by(Transaction.transaction_type)
        ).all()
    )
    return {
        "types": [
            {"transaction_type": t, "total": int(n), "suspicious": int(s),
             "confirmed_fraud": int(confirmed.get(t, 0)),
             "average_amount": float(a) if a is not None else None, "total_amount": float(amt)}
            for t, n, s, a, amt in rows
        ]
    }


def investigations_analytics(db: Session, date_from=None, date_to=None) -> Dict[str, Any]:
    start, end = date_bounds(date_from, date_to)
    conds = []
    if start:
        conds.append(Investigation.created_at >= start)
    if end:
        conds.append(Investigation.created_at < end)

    def grouped(col):
        return {k: int(v) for k, v in db.execute(_where(select(col, func.count(Investigation.id)), conds).group_by(col)).all()}

    durations = db.execute(
        _where(select(Investigation.created_at, Investigation.resolved_at)
               .where(Investigation.resolved_at.is_not(None)), conds)
    ).all()
    hours = [(r - c).total_seconds() / 3600 for c, r in durations if c and r]
    return {
        "by_status": grouped(Investigation.status),
        "by_outcome": grouped(Investigation.outcome),
        "by_priority": grouped(Investigation.priority),
        "average_resolution_hours": (sum(hours) / len(hours)) if hours else None,
        "resolved_count": len(hours),
    }


def verified_performance(db: Session) -> Dict[str, Any]:
    """Operational metrics from analyst-verified outcomes ONLY (never from raw predictions)."""
    rows = db.execute(
        select(Transaction.prediction, Investigation.outcome, func.count(Investigation.id))
        .join(Investigation, Investigation.transaction_id == Transaction.id)
        .where(Investigation.outcome.in_([CONFIRMED, LEGIT]))
        .group_by(Transaction.prediction, Investigation.outcome)
    ).all()
    m = {(p, o): int(n) for p, o, n in rows}
    tp = m.get((PRED_SUSPICIOUS, CONFIRMED), 0)
    fp = m.get((PRED_SUSPICIOUS, LEGIT), 0)
    fn = m.get(("Not Flagged", CONFIRMED), 0)
    tn = m.get(("Not Flagged", LEGIT), 0)
    verified = tp + fp + fn + tn
    return {
        "verified_cases": verified,
        "true_positives": tp, "false_positives": fp, "false_negatives": fn, "true_negatives": tn,
        "precision": tp / (tp + fp) if (tp + fp) else None,
        "recall": tp / (tp + fn) if (tp + fn) else None,
        "caveat": (
            "Computed only from investigations with a verified outcome (Confirmed Fraud / Legitimate "
            "Transaction). Investigated cases are not a random sample, so recall in particular may be "
            "unreliable. Not comparable to the historical offline metrics."
        ),
    }
