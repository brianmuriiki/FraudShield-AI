# Phase 3 test and verification results

**Date:** 28 November 2026
**Environment:** fresh Python 3.12 environment from `backend/requirements.lock`; disposable SQLite database under `/tmp`; included model artifacts; local Uvicorn and Vite production build. No production data or services were used.

## Final automated results

| Suite | Command | Passed | Failed | Skipped | Result |
|---|---|---:|---:|---:|---|
| Backend API/model/security/database pytest | `/tmp/fs-phase3-final/bin/python -m pytest -q` | 66 | 0 | 0 | PASS; one upstream Starlette/httpx deprecation warning |
| Frontend API unit tests | `corepack pnpm test:unit` | 3 | 0 | 0 | PASS |
| Playwright Chromium, production build | `corepack pnpm exec playwright test` with `FS_BASE_URL=http://127.0.0.1:4173` and isolated API | 8 | 0 | 0 | PASS |
| **Combined** | Above suites | **77** | **0** | **0** | **PASS** |

## Additional verification

- Fresh lock install: `python3.12 -m venv /tmp/fs-phase3-final`, `pip install -r backend/requirements.lock`, then `pip check` — PASS.
- `pip-audit -r backend/requirements.lock` — no known vulnerabilities found.
- `corepack pnpm audit --audit-level moderate` — no known vulnerabilities found.
- `corepack pnpm exec tsc --noEmit` — PASS.
- `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1 corepack pnpm build` — PASS; JS 240.58 kB (72.42 kB gzip), CSS 58.05 kB (13.92 kB gzip).
- Alembic upgrade to head, downgrade to the initial revision, then upgrade to head on disposable SQLite — PASS.
- `pip check` — no broken requirements.
- `git diff --check` — run after final report edits (see final status).

## Browser coverage and evidence

The final 8 browser tests covered real login failures/success, dashboard data, token revocation, refresh behavior, transaction search/filter/detail, model scoring and SHAP, investigation create/assignment/priority/status/outcome/notes/history/resolve/close, analytics, CSV download, model metadata, admin user create/role update/deactivation, BI access restrictions, error handling, keyboard focus, and mobile navigation.

One intermediate rerun reported a 401 while multiple leftover local Uvicorn processes shared the test port. Process inspection found an older server still bound to port 8000. After stopping stale processes and resetting the disposable database, the prediction scenario passed alone and the complete final 8-test suite passed against one fresh server. The final 66-test backend suite also passed after the final CORS/body-limit edits.

Axe reported zero violations on sign-in, overview, transactions, fraud detection, investigations, analytics/reports, model intelligence, and team/system. The production-build preview returned a real CSP header containing `script-src 'self'` with no script `unsafe-inline`/`unsafe-eval`. The backend returned API no-store and security headers.

Screenshots: [prediction and SHAP](screenshots/prediction-and-shap.png) and [connected application surfaces](screenshots/connected-pages.png).

## Request body evidence

Tests cover normal, exactly-at-limit, oversized declared length, missing `Content-Length`, and streamed chunks. An actual local Uvicorn request using HTTP chunked transfer encoding with no `Content-Length` and a body over 1 MiB returned **413 Request Entity Too Large**, `Cache-Control: no-store`, and `{"detail":"Request body too large"}`. Ingress behavior has not been exercised because Nginx/provider ingress is not available locally.

## Remaining limits

The preview used local HTTP and therefore did not emit HSTS. TLS certificates, externally served HSTS, provider Nginx rendering, production CORS origins, trusted proxy addresses, PostgreSQL connectivity, database restore, load/concurrency behavior, DAST, and screen-reader checks remain unverified. The local test database is SQLite. These are deployment gates, not successful test results.
