import math
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, Generic, List, TypeVar

from pydantic import BaseModel, ConfigDict, PlainSerializer

T = TypeVar("T")


def _iso_utc(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


UTCDatetime = Annotated[datetime, PlainSerializer(_iso_utc, return_type=str)]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    pages: int


def build_page(items: List[Any], total: int, page: int, page_size: int) -> Dict[str, Any]:
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": max(1, math.ceil(total / page_size)),
    }


class MessageResponse(BaseModel):
    message: str
