from fastapi import APIRouter

from app.api.endpoints import (
    analytics, auth, dashboard, investigations, model, predictions, reports, transactions, users,
)

api_router = APIRouter()
for module in (auth, predictions, transactions, investigations, dashboard, analytics, model, users, reports):
    api_router.include_router(module.router)
