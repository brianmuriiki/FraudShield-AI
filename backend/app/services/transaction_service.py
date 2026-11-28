from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.constants import PRED_SUSPICIOUS, TX_AWAITING, TX_NOT_REQUIRED
from app.core.exceptions import NotFoundError
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionInput
from app.services import ml_service as ml
from app.services.audit_service import log_action
from app.utils.helpers import date_bounds, new_reference

_SORTABLE = {
    "created_at": Transaction.created_at,
    "amount": Transaction.amount,
    "fraud_score": Transaction.fraud_score,
    "step": Transaction.step,
}


def create_scored_transaction(
    db: Session, data: TransactionInput, user: Optional[User], ip: Optional[str]
) -> Tuple[Transaction, Dict[str, Any]]:
    """Scores with the real model (raises if unavailable) and persists the result."""
    result = ml.predict_transaction(data)

    reference = new_reference("TXN")
    while db.scalar(select(Transaction.id).where(Transaction.transaction_reference == reference)):
        reference = new_reference("TXN")

    tx = Transaction(
        transaction_reference=reference,
        step=data.step,
        amount=data.amount,
        oldbalanceOrg=data.oldbalanceOrg,
        oldbalanceDest=data.oldbalanceDest,
        transaction_type=result["transaction_type"],
        fraud_score=result["fraud_score"],
        prediction=result["prediction"],
        risk_level=result["risk_level"],
        threshold=result["threshold"],
        investigation_status=TX_AWAITING if result["requires_investigation"] else TX_NOT_REQUIRED,
        created_by_id=user.id if user else None,
    )
    db.add(tx)
    log_action(
        db,
        action="transaction_prediction",
        entity_type="transaction",
        entity_id=reference,
        description=f"{result['transaction_type']} scored {result['fraud_score']} -> {result['prediction']}",
        user_id=user.id if user else None,
        ip_address=ip,
    )
    db.commit()
    db.refresh(tx)
    return tx, result


def get_transaction_or_404(db: Session, ident: str) -> Transaction:
    tx = db.scalar(select(Transaction).where(Transaction.transaction_reference == ident))
    if tx is None and str(ident).isdigit():
        tx = db.get(Transaction, int(ident))
    if tx is None:
        raise NotFoundError("Transaction not found")
    return tx


def list_transactions(
    db: Session,
    *,
    page: int,
    page_size: int,
    search: Optional[str] = None,
    transaction_type: Optional[str] = None,
    prediction: Optional[str] = None,
    risk_level: Optional[str] = None,
    investigation_status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> Tuple[List[Transaction], int]:
    conds = []
    if search:
        conds.append(func.upper(Transaction.transaction_reference).contains(search.upper(), autoescape=True))
    if transaction_type:
        conds.append(Transaction.transaction_type == transaction_type)
    if prediction:
        conds.append(Transaction.prediction == prediction)
    if risk_level:
        conds.append(Transaction.risk_level == risk_level)
    if investigation_status:
        conds.append(Transaction.investigation_status == investigation_status)
    start, end = date_bounds(date_from, date_to)
    if start:
        conds.append(Transaction.created_at >= start)
    if end:
        conds.append(Transaction.created_at < end)
    if min_amount is not None:
        conds.append(Transaction.amount >= min_amount)
    if max_amount is not None:
        conds.append(Transaction.amount <= max_amount)

    count_stmt = select(func.count()).select_from(Transaction)
    stmt = select(Transaction)
    if conds:
        count_stmt, stmt = count_stmt.where(*conds), stmt.where(*conds)
    total = db.scalar(count_stmt) or 0

    col = _SORTABLE.get(sort_by, Transaction.created_at)
    order = col.asc() if sort_order == "asc" else col.desc()
    rows = db.scalars(
        stmt.order_by(order, Transaction.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()
    return list(rows), total


def transaction_stats(db: Session) -> Dict[str, Any]:
    suspicious_case = case((Transaction.prediction == PRED_SUSPICIOUS, 1), else_=0)
    total, suspicious, total_amount, avg_score = db.execute(
        select(
            func.count(Transaction.id),
            func.coalesce(func.sum(suspicious_case), 0),
            func.coalesce(func.sum(Transaction.amount), 0.0),
            func.avg(Transaction.fraud_score),
        )
    ).one()
    by_type = db.execute(
        select(Transaction.transaction_type, func.count(Transaction.id), func.sum(suspicious_case))
        .group_by(Transaction.transaction_type)
        .order_by(Transaction.transaction_type)
    ).all()
    by_risk = dict(
        db.execute(select(Transaction.risk_level, func.count(Transaction.id)).group_by(Transaction.risk_level)).all()
    )
    return {
        "total": int(total),
        "suspicious": int(suspicious),
        "not_flagged": int(total) - int(suspicious),
        "total_amount": float(total_amount),
        "average_fraud_score": float(avg_score) if avg_score is not None else None,
        "by_type": [{"transaction_type": t, "total": int(n), "suspicious": int(s or 0)} for t, n, s in by_type],
        "by_risk_level": {k: int(v) for k, v in by_risk.items()},
        "note": "Suspicious means flagged by the model; it is not confirmed fraud.",
    }
