from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import PRED_SUSPICIOUS
from app.models.database import Base
from app.utils.helpers import utcnow


class Transaction(Base):
    """Stores only the nine model inputs (as raw fields) plus the model output."""

    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_reference: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    step: Mapped[int] = mapped_column(Integer)
    amount: Mapped[float] = mapped_column(Float, index=True)
    oldbalanceOrg: Mapped[float] = mapped_column(Float)
    oldbalanceDest: Mapped[float] = mapped_column(Float)
    transaction_type: Mapped[str] = mapped_column(String(16), index=True)
    fraud_score: Mapped[float] = mapped_column(Float, index=True)
    prediction: Mapped[str] = mapped_column(String(16), index=True)
    risk_level: Mapped[str] = mapped_column(String(16), index=True)
    threshold: Mapped[float] = mapped_column(Float)
    investigation_status: Mapped[str] = mapped_column(String(32), index=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    @property
    def requires_investigation(self) -> bool:
        return self.prediction == PRED_SUSPICIOUS
