# FraudShield AI – Backend

FastAPI backend that connects the React frontend to the trained FraudShield XGBoost model
(calibrated, threshold 0.468), with SHAP explanations, transaction storage, investigation
workflow, dashboard/analytics, JWT auth with role-based access control, and audit logging.

> **Status:** local checks and the backend test suite have been executed against the included
> model artifacts. The backend is not production-ready until the documented deployment controls
> and remaining frontend integrations are completed.

## Stack
Python 3.12 · FastAPI · Uvicorn · Pydantic v2 · SQLAlchemy 2 (SQLite → PostgreSQL) · Alembic ·
Pandas/NumPy/scikit-learn/XGBoost/SHAP/Joblib · PyJWT · bcrypt · Pytest

## Layout
```
fraudshield-ai/
├── models/                       # <- put the 3 .pkl artifacts here (NOT included)
│   ├── fraudshield_xgboost_model.pkl
│   ├── fraudshield_calibrated_model.pkl
│   └── fraudshield_metadata.pkl
├── frontend/
└── backend/                      # this folder
    ├── app/ (core, api/endpoints, schemas, models, services, utils, database, main.py)
    ├── alembic/  tests/  requirements.txt  .env.example
```

## Setup
```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.lock
cp .env.example .env     # then set SECRET_KEY and the initial admin credentials
uvicorn app.main:app --reload --port 8000
```
Swagger UI: http://127.0.0.1:8000/docs · Health: `GET /api/v1/health`

### Environment variables (see `.env.example`)
`ENVIRONMENT`, `DATABASE_URL`, `SECRET_KEY` (at least 32 characters in production), `AUTO_CREATE_TABLES` (false in production), `MAX_REQUEST_BYTES`, `ACCESS_TOKEN_EXPIRE_MINUTES`,
`CORS_ORIGINS`, `MODEL_DIR` (default `<repo>/models`), `INITIAL_ADMIN_EMAIL/PASSWORD/NAME`,
`ALLOW_PUBLIC_REGISTRATION`, `LOGIN_RATE_WINDOW_MINUTES`, `LOGIN_RATE_ACCOUNT_LIMIT`,
`LOGIN_RATE_SOURCE_LIMIT`, and `HSTS_MAX_AGE_SECONDS`.

### Database
SQLite by default. For PostgreSQL set `DATABASE_URL=postgresql+psycopg://...`; Psycopg 3 is pinned in `requirements.lock`.
In development tables are created automatically (never dropped). For production use Alembic:
```bash
alembic upgrade head
```
(set `AUTO_CREATE_TABLES=false` when using Alembic).

## Model behaviour
* Artifacts are loaded **once at startup**. If any is missing/invalid, `/health` returns 503 and
  prediction/explanation/metadata endpoints return 503 – the API never fakes a prediction.
* Startup validates feature names/order (9 features), positive class, and that the metadata threshold equals 0.468.
* `fraud_score >= 0.468` → `Suspicious`, else `Not Flagged`. Risk levels (Low <0.10, Moderate <0.30,
  Elevated <0.468, High ≥0.468) are presentation only.
* SHAP runs on the underlying XGBoost estimator in **raw log-odds space** (not calibrated probabilities).
* Scores are *estimated risk scores*; a Suspicious flag is never confirmed fraud. Metrics are historical offline results.

## Endpoints (prefix `/api/v1`)
| Area | Endpoints | Access |
|---|---|---|
| System | `GET /health`, `GET /ready` | public |
| Auth | `POST /auth/login` (JSON), `POST /auth/token` (form), `POST /auth/register`, `GET /auth/me`, `POST /auth/logout` | register: admin only (unless `ALLOW_PUBLIC_REGISTRATION`) |
| Predictions | `POST /predictions/predict`, `POST /predictions/explain`, `GET /predictions/explain/{id}` | any authenticated |
| Transactions | `GET /transactions`, `GET /transactions/stats`, `GET /transactions/{id}`, `POST /transactions` | read: all · create: admin/senior/fraud |
| Investigations | `GET/POST /investigations`, `GET/PATCH /investigations/{id}`, `POST /investigations/{id}/notes` | admin/senior/fraud |
| Dashboard | `GET /dashboard/summary` | any authenticated |
| Analytics | `GET /analytics/{overview,transactions,fraud-trends,transaction-types,investigations}` | admin/senior/BI |
| Reports | `GET /reports/summary`, `GET /reports/export?format=csv` (pdf → 501) | admin/senior/BI |
| Model | `GET /model/metadata` | any authenticated |
| Users | `GET /users`, `GET /users/analysts`, `GET /users/audit-logs`, `GET/PATCH /users/{id}` | admin (analysts list: admin/senior) |

Request body for prediction (also accepts `type`/`transactionType`, snake_case balance names; unknown fields ignored):
```json
{"step": 379, "amount": 36942.13, "oldbalanceOrg": 36942.13, "oldbalanceDest": 0, "transaction_type": "TRANSFER"}
```
Numeric fields are strict (strings like `"100"` are rejected with 422). Transaction/investigation `{id}` may be the
reference (`TXN-…`, `INV-…`) or the numeric id.

### Roles
* **administrator** – everything, user management, audit logs.
* **senior_analyst** – create/assign investigations, record outcomes, resolve/close, analytics.
* **fraud_analyst** – create investigations, add notes, set status New/Under Review/Escalated. Cannot set outcomes, assign, or resolve/close.
* **bi_analyst** – dashboard, analytics, reports. No access to investigations.

### Authentication
`POST /auth/login` → `{access_token, token_type, expires_in, user}`; send `Authorization: Bearer <token>`.
Roles are read from the database on each request. JWTs include a unique `jti`; logout stores that
identifier in `revoked_tokens`, and protected requests check the shared database before accepting
the token. Expired revocation rows are removed opportunistically. Every worker must use the same
database for logout revocation to apply across workers.

Failed JSON and OAuth-form logins share a database-backed 15-minute sliding window by default:
10 failures per normalized account and 40 failures per source IP. Account and source identifiers
are HMACed with `SECRET_KEY`; raw IPs and email addresses are not stored in the throttle table.
Attempts expire from the active window and old rows are purged during login checks, so this does
not permanently lock accounts. Source IP uses the direct ASGI client address; configure a trusted
proxy correctly rather than accepting arbitrary forwarded headers. The database must be shared by
all workers/instances. Public self-registration is disabled by default; no password-reset endpoint
exists. If public registration is enabled, add a separate registration quota before exposing it.

API responses include `nosniff`, referrer, frame, CSP, and no-store headers. HSTS is emitted only
for production requests whose ASGI scheme is HTTPS. TLS-terminating ingress should set HSTS and a
frontend document CSP itself when the backend sees HTTP; configure trusted proxy scheme handling.
The backend API CSP applies to API responses, not the separately hosted React document. A frontend
hosting CSP must allow only deployed script/style/font sources and the configured API origin.

## Tests
```bash
cd backend && pytest -v
```
Pure unit tests always run. Tests that need the real model are skipped (with a printed reason) if the `.pkl`
files are not in `MODEL_DIR`. They include a parity test (API score == direct `predict_proba`) and a SHAP additivity test.

## Frontend integration
Vite dev origin `http://localhost:5173` is allowed by default; set `CORS_ORIGINS` for others. Point the frontend's API base URL
at `http://127.0.0.1:8000/api/v1`. The frontend connects transactions, investigations, dashboard,
analytics/CSV export, model metadata, and administrator user operations. See `../frontend/API_INTEGRATION.md`.

## Known limitations
* Verified-performance analytics use only analyst-confirmed outcomes and carry a selection-bias caveat.
* PDF export is not implemented; CSV is the supported report format.
* Relational attempt counting is shared across workers using one database, but concurrent bursts can
  slightly exceed the configured threshold. Use a shared rate-limit service if strict atomic quotas
  are required at higher scale.
* `requirements.lock` pins the complete tested Python 3.12/Linux dependency graph. Model metadata records XGBoost 3.4.1 and scikit-learn 1.9.1, matching this lock. Regenerate and retest deliberately when changing it.
