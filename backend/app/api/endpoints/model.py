from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.user import User
from app.services.ml_service import ml_service

router = APIRouter(prefix="/model", tags=["Model"])


@router.get("/metadata")
def model_metadata(_: User = Depends(get_current_user)):
    """Model description, historical offline metrics and limitations (raises 503 if not loaded)."""
    return ml_service.describe()
