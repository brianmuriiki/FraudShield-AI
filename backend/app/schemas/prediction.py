from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.transaction import TransactionInput


class PredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    transaction_id: str
    prediction: str
    fraud_score: float
    threshold: float
    risk_level: str
    requires_investigation: bool
    transaction_type: str
    model_name: str
    message: str
    score_note: str = (
        "fraud_score is an estimated risk score, not a guaranteed probability of fraud. "
        "A Suspicious result is not confirmed fraud."
    )


class ExplainRequest(TransactionInput):
    transaction_id: Optional[str] = None


class FeatureContribution(BaseModel):
    feature: str
    value: float
    contribution: float
    influence: str
    description: str


class ExplainResponse(BaseModel):
    transaction_id: Optional[str]
    explanation_method: str = "SHAP"
    output_space: str
    base_value: float
    raw_output: float
    features: List[FeatureContribution]
    warning: str
