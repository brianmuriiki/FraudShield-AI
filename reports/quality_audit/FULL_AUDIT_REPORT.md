# FraudShield AI — Phase 3 production-readiness audit

**Audit date:** 28 November 2026
**Branch:** `qa/full-stack-security-audit`
**Disposition:** **Not production-ready.** Phase 3 application gaps are implemented and verified locally. Production TLS/ingress, PostgreSQL operation, backup recovery, and operational security/load checks still lack environment evidence.

## Scope and environment

Verification used a newly created Python 3.12 environment installed from `backend/requirements.lock`, the included trusted model artifacts, a disposable SQLite database under `/tmp`, a local Uvicorn API, and the Vite production build served at localhost. No production service, real credentials, or financial data was used. The browser build received a Vite preview CSP and security headers; the provider-facing Nginx template was not executed because Nginx is not installed in this workspace.

## Phase 3 changes

- Pinned direct Python dependencies and the complete tested transitive graph. Artifact metadata records XGBoost 3.4.1 and scikit-learn 1.9.1, matching the lock. The clean install, runtime startup, prediction, SHAP, and all backend tests pass.
- Added production configuration checks for a long secret, explicit HTTPS CORS origins, production migrations, and request limits. Added a static-host CSP/header setup and an Nginx TLS/reverse-proxy template with HSTS, request size, and proxy headers.
- Added streamed ASGI request-byte enforcement that stops after the configured cap, including missing `Content-Length`. A chunked request over 1 MiB returned 413 through both the ASGI stack regression test and actual local Uvicorn.
- Connected dashboard totals, transaction list/detail/filtering, investigation CRUD/assignment/status/outcomes/notes/history, analytics/date filtering, CSV report generation/download, model metadata, and admin user operations to real API data.
- Removed sample transaction records and hard-coded drift/performance claims. Model metrics and training versions are displayed only when present in the loaded artifact metadata.
- Added role-aware navigation, regression tests, and production-build Playwright coverage.

## Verification results

- Backend: **66 passed, 0 failed, 0 skipped** using the fresh lock-installed environment; one upstream Starlette/httpx deprecation warning.
- Frontend API unit tests: **3 passed**.
- Playwright Chromium: **8 passed** against the production build and isolated backend. This includes auth/revocation, model prediction/SHAP, transactions, investigation CRUD and closing, CSV download, model metadata, user role/deactivation, BI access restrictions, error handling, mobile navigation, and axe checks.
- Axe: **zero violations** across sign-in and seven authenticated surfaces; keyboard focus and a 375 px viewport were checked.
- Total automated tests: **77 passed, 0 failed, 0 skipped**.
- TypeScript check, Vite production build, clean `pip install -r backend/requirements.lock`, `pip check`, SQLite migration upgrade/downgrade/upgrade, `pnpm audit`, and `pip-audit -r backend/requirements.lock` passed. Both advisory scans reported no known vulnerabilities at scan time.
- Actual localhost response probes confirmed frontend CSP/security headers, backend API no-store/security headers, and streamed 413 behavior. Production HTTPS/HSTS through ingress was not tested.

See [TEST_RESULTS.md](TEST_RESULTS.md), [SECURITY_REPORT.md](SECURITY_REPORT.md), and [FEATURE_TEST_MATRIX.md](FEATURE_TEST_MATRIX.md). Browser evidence: [prediction and SHAP](screenshots/prediction-and-shap.png), [connected workflow surfaces](screenshots/connected-pages.png).

## Remaining issues and deployment gates

| Severity | Impact / affected feature | Required action | Blocks deployment? |
|---|---|---|---|
| High | TLS, HSTS, frontend CSP, reverse proxy, and trusted forwarded headers are not verified at a real HTTPS ingress. | Render and externally probe `deploy/nginx.conf.template`; restrict Uvicorn forwarded IPs to actual proxy addresses; verify TLS 1.2/1.3, redirects, CORS, CSP, HSTS, and chunked body handling. | Yes |
| High | PostgreSQL connectivity, production migrations, and database-specific behavior have not been exercised against a provider or staging PostgreSQL instance. | Run migrations and auth/investigation/analytics/load smoke tests on the target PostgreSQL version with TLS and least-privilege credentials. | Yes |
| High | Backup, point-in-time recovery, and restore are hosting-provider responsibilities and have not been performed. | Configure encrypted backups and demonstrate an isolated restore against the agreed RPO/RTO. | Yes |
| High | Model training data is synthetic PaySim; evaluation metrics are offline and no live drift monitoring is implemented. | Obtain model-risk approval and validate representative real-world data before relying on scores in payment operations. | Yes for real-money fraud decisions |
| Medium | Database-backed login throttling can slightly exceed limits during a concurrent burst. | Load test expected concurrency; use an atomic shared limiter if strict quotas are required. | Conditional on threat/load requirements |
| Medium | No external DAST, multi-worker/load, screen-reader, or production-database test was run. | Complete these checks in staging and record results. | Yes under final acceptance criteria |
| Low | PDF report export is not implemented. | Use CSV or authorize and implement PDF if a product requirement. | No; CSV works |
| Low | Current styling uses inline style attributes for data bars; CSP allows only `style-src-attr 'unsafe-inline'`, with script inline execution disallowed. | Keep this narrow policy or replace style attributes with classes/CSS variables if a stricter style policy is required. | No |

## Readiness decision

**Do not call this production-ready or deploy it for live payment decisions yet.** Application-level features, dependency reproducibility, local security headers, streamed body enforcement, and browser/API regressions pass. The outstanding high-severity gates concern real hosting, database recovery, and whether the synthetic-data model is suitable for production decisions; local tests cannot establish those facts.
