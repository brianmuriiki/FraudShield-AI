from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.core.dependencies import get_client_ip, get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.prediction import ExplainRequest, ExplainResponse, PredictionResponse
from app.schemas.transaction import TransactionInput
from app.services.shap_service import shap_service
from app.services.transaction_service import create_scored_transaction, get_transaction_or_404

router = APIRouter(prefix="/predictions", tags=["Predictions"])


@router.post("/predict", response_model=PredictionResponse)
def predict(
    payload: TransactionInput,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Scores a transaction with the saved calibrated model and stores the result."""
    tx, result = create_scored_transaction(db, payload, user, get_client_ip(request))
    return PredictionResponse(transaction_id=tx.transaction_reference, **result)


@router.post("/explain", response_model=ExplainResponse)
def explain(payload: ExplainRequest, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """SHAP explanation for a submitted transaction (not stored)."""
    reference = None
    if payload.transaction_id:
        reference = get_transaction_or_404(db, payload.transaction_id).transaction_reference
    return shap_service.explain(
        payload.step, payload.amount, payload.oldbalanceOrg, payload.oldbalanceDest,
        payload.transaction_type.value, transaction_id=reference,
    )


@router.get("/explain/{transaction_id}", response_model=ExplainResponse)
def explain_stored(transaction_id: str, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    """SHAP explanation for an already stored transaction, using its stored inputs."""
    tx = get_transaction_or_404(db, transaction_id)
    return shap_service.explain(
        tx.step, tx.amount, tx.oldbalanceOrg, tx.oldbalanceDest, tx.transaction_type,
        transaction_id=tx.transaction_reference,
    )
