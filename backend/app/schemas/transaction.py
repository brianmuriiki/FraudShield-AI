from typing import Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.constants import TransactionType
from app.schemas.common import ORMModel, UTCDatetime
from app.utils.validators import normalize_transaction_type


class TransactionInput(BaseModel):
    """Raw transaction as sent by the frontend. One-hot encoding happens in the backend.

    Numeric fields are strict: strings such as "100" are rejected. Unknown extra fields
    are ignored and never passed to the model (it supports only the nine listed features).
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    step: int = Field(strict=True, ge=0, le=10_000_000)
    amount: float = Field(strict=True, ge=0, allow_inf_nan=False)
    oldbalanceOrg: float = Field(
        strict=True,
        ge=0,
        allow_inf_nan=False,
        validation_alias=AliasChoices("oldbalanceOrg", "oldbalance_org", "old_balance_org"),
    )
    oldbalanceDest: float = Field(
        strict=True,
        ge=0,
        allow_inf_nan=False,
        validation_alias=AliasChoices("oldbalanceDest", "oldbalance_dest", "old_balance_dest"),
    )
    transaction_type: TransactionType = Field(
        validation_alias=AliasChoices("transaction_type", "transactionType", "type")
    )

    @model_validator(mode="before")
    @classmethod
    def _accept_model_feature_vector(cls, value):
        """Accept the frontend's exact nine model fields, or the compact human form.

        The model still receives a DataFrame built from the canonical feature order;
        this only maps an already one-hot encoded request to its supported type.
        """
        if not isinstance(value, dict):
            return value
        type_names = ("CASH_IN", "CASH_OUT", "DEBIT", "PAYMENT", "TRANSFER")
        keys = tuple(f"type_{name}" for name in type_names)
        present = [key in value for key in keys]
        if not any(present):
            return value
        if not all(present):
            raise ValueError("All five transaction type indicator fields are required")
        indicators = [value[key] for key in keys]
        if any(isinstance(bit, bool) or not isinstance(bit, (int, float)) or bit not in (0, 1) for bit in indicators):
            raise ValueError("Transaction type indicators must be numeric 0 or 1")
        if sum(indicators) != 1:
            raise ValueError("Exactly one transaction type indicator must be active")
        selected = type_names[indicators.index(1)]
        type_key = next((key for key in ("transaction_type", "transactionType", "type") if key in value), None)
        if type_key is not None and normalize_transaction_type(value[type_key]) != selected:
            raise ValueError("Transaction type does not match its one-hot indicators")
        return {**value, "transaction_type": selected}

    @field_validator("transaction_type", mode="before")
    @classmethod
    def _normalise_type(cls, v):
        return normalize_transaction_type(v)


class TransactionOut(ORMModel):
    id: int
    transaction_id: str = Field(validation_alias=AliasChoices("transaction_reference", "transaction_id"))
    step: int
    amount: float
    oldbalanceOrg: float
    oldbalanceDest: float
    transaction_type: str
    fraud_score: float
    prediction: str
    risk_level: str
    threshold: float
    requires_investigation: bool
    investigation_status: str
    created_at: UTCDatetime
    updated_at: UTCDatetime
