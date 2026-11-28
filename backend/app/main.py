import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import AppError
from app.database.init_db import ensure_initial_admin, init_db
from app.database.session import SessionLocal
from app.services.ml_service import load_models, ml_service
from app.services.shap_service import shap_service
from app.middleware.request_size import RequestBodyLimitMiddleware

logger = logging.getLogger("fraudshield")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    if settings.AUTO_CREATE_TABLES:
        init_db()
    ensure_initial_admin()
    load_models()
    shap_service.init()
    if not ml_service.loaded:
        logger.error("Model NOT loaded: %s. Prediction endpoints will return 503.", ml_service.error)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Backend for FraudShield AI: fraud-risk scoring, explanations and investigation workflow.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def limit_request_size(request: Request, call_next):
    length = request.headers.get("content-length")
    if length and length.isdigit() and int(length) > settings.MAX_REQUEST_BYTES:
        response = JSONResponse(status_code=413, content={"detail": "Request body too large"})
    else:
        response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"
    if request.url.path.startswith(settings.API_V1_PREFIX):
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
    # Only emit HSTS when the application itself sees HTTPS. TLS-terminating proxies
    # should set this header at ingress and must not forward untrusted scheme headers.
    if settings.is_production and request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = f"max-age={settings.HSTS_MAX_AGE_SECONDS}"
    return response


# ---------------------------------------------------------------- error handling
@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=getattr(exc, "headers", None))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, exc: RequestValidationError):
    errors = [{"loc": list(e.get("loc", [])), "msg": e.get("msg", ""), "type": e.get("type", "")} for e in exc.errors()]
    return JSONResponse(status_code=422, content={"detail": errors, "message": "Validation failed"})


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(_: Request, exc: SQLAlchemyError):
    logger.exception("Database error")
    return JSONResponse(status_code=500, content={"detail": "A database error occurred"})


@app.exception_handler(Exception)
async def unhandled_error_handler(_: Request, exc: Exception):
    logger.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ------------------------------------------------------------------------ health
def _health_payload():
    db_ok = True
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001
        db_ok = False
        logger.exception("Health check: database unreachable")
    model_ok = ml_service.loaded
    healthy = db_ok and model_ok
    body = {
        "status": "healthy" if healthy else "unhealthy",
        "database": "connected" if db_ok else "unavailable",
        "model": "loaded" if model_ok else "unavailable",
        "model_metadata": "available" if model_ok and ml_service.metadata else "unavailable",
        "explainer": "ready" if shap_service.ready else "unavailable",
    }
    if model_ok:
        body["model_name"] = "FraudShield XGBoost"
    else:
        body["model_error"] = ml_service.error
    return (200 if healthy else 503), body


@app.get(f"{settings.API_V1_PREFIX}/health", tags=["System"])
def health():
    code, body = _health_payload()
    return JSONResponse(status_code=code, content=body)


@app.get(f"{settings.API_V1_PREFIX}/ready", tags=["System"])
def ready():
    code, body = _health_payload()
    return JSONResponse(status_code=code, content=body)


app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Wrap the completed ASGI application so streamed bodies are counted as the server
# delivers them, including requests that omit Content-Length (for example chunked).
app = RequestBodyLimitMiddleware(
    app,
    max_bytes=settings.MAX_REQUEST_BYTES,
    allowed_origins=settings.cors_origin_list,
    production=settings.is_production,
    hsts_seconds=settings.HSTS_MAX_AGE_SECONDS,
)
