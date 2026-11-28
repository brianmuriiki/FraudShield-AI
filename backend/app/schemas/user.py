from typing import Optional

from pydantic import BaseModel, Field

from app.core.constants import Role
from app.schemas.common import ORMModel, UTCDatetime


class UserOut(ORMModel):
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: UTCDatetime
    last_login_at: Optional[UTCDatetime] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    role: Optional[Role] = None
    is_active: Optional[bool] = None


class AnalystOut(ORMModel):
    id: int
    full_name: str
    email: str
    role: str


class AuditLogOut(ORMModel):
    id: int
    user_id: Optional[int]
    user_name: Optional[str]
    action: str
    entity_type: str
    entity_id: Optional[str]
    description: str
    ip_address: Optional[str]
    created_at: UTCDatetime
