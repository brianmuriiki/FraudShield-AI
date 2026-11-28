from typing import List, Optional, Union

from pydantic import AliasChoices, BaseModel, Field

from app.core.constants import InvestigationOutcome, InvestigationStatus, Priority
from app.schemas.common import ORMModel, UTCDatetime
from app.schemas.user import AnalystOut


class NoteCreate(BaseModel):
    content: str = Field(min_length=1, max_length=5000)


class NoteOut(ORMModel):
    id: int
    author_id: Optional[int]
    author_name: Optional[str]
    content: str
    created_at: UTCDatetime


class InvestigationCreate(BaseModel):
    transaction_id: Union[int, str]  # transaction reference (TXN-...) or numeric id
    priority: Optional[Priority] = None
    assigned_analyst_id: Optional[int] = None
    notes: Optional[str] = Field(default=None, max_length=5000)


class InvestigationUpdate(BaseModel):
    status: Optional[InvestigationStatus] = None
    outcome: Optional[InvestigationOutcome] = None
    priority: Optional[Priority] = None
    assigned_analyst_id: Optional[int] = None  # explicit null un-assigns


class InvestigationOut(ORMModel):
    id: int
    investigation_reference: str
    transaction_id: str = Field(validation_alias=AliasChoices("transaction_reference", "transaction_id"))
    assigned_analyst_id: Optional[int]
    assigned_analyst: Optional[AnalystOut] = None
    created_by_id: Optional[int] = None
    status: str
    outcome: str
    priority: str
    notes: List[NoteOut] = []
    created_at: UTCDatetime
    updated_at: UTCDatetime
    resolved_at: Optional[UTCDatetime] = None


class HistoryEntry(ORMModel):
    id: int
    user_id: Optional[int]
    user_name: Optional[str]
    action: str
    description: str
    created_at: UTCDatetime


class InvestigationDetail(InvestigationOut):
    history: List[HistoryEntry] = []
