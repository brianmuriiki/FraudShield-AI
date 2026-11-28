from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.constants import InvestigationOutcome, InvestigationStatus, Priority
from app.models.database import Base
from app.models.transaction import Transaction
from app.models.user import User
from app.utils.helpers import utcnow


class Investigation(Base):
    __tablename__ = "investigations"

    id: Mapped[int] = mapped_column(primary_key=True)
    investigation_reference: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE"), index=True
    )
    assigned_analyst_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), index=True, default=InvestigationStatus.NEW.value)
    outcome: Mapped[str] = mapped_column(
        String(32), index=True, default=InvestigationOutcome.PENDING.value
    )
    priority: Mapped[str] = mapped_column(String(16), default=Priority.MEDIUM.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    transaction: Mapped[Transaction] = relationship(lazy="joined")
    assigned_analyst: Mapped[Optional[User]] = relationship(
        foreign_keys=[assigned_analyst_id], lazy="joined"
    )
    notes: Mapped[List["InvestigationNote"]] = relationship(
        back_populates="investigation",
        order_by="InvestigationNote.created_at",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def transaction_reference(self) -> str:
        return self.transaction.transaction_reference


class InvestigationNote(Base):
    __tablename__ = "investigation_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    investigation_id: Mapped[int] = mapped_column(
        ForeignKey("investigations.id", ondelete="CASCADE"), index=True
    )
    author_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    investigation: Mapped[Investigation] = relationship(back_populates="notes")
    author: Mapped[Optional[User]] = relationship(lazy="joined")

    @property
    def author_name(self) -> Optional[str]:
        return self.author.full_name if self.author else None
