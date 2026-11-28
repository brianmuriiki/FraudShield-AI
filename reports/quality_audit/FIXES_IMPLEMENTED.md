# Fixes implemented — Phase 3

| Area | Change | Verification |
|---|---|---|
| Reproducible backend dependencies | Exact direct pins plus full transitive `backend/requirements.lock`; includes psycopg3 for PostgreSQL. Model library pins match artifact versions: XGBoost 3.4.1, scikit-learn 1.9.1. | Fresh Python 3.12 lock install, `pip check`, complete 66-test suite, `pip-audit` clean. |
| Production configuration | Production requires a long secret, explicit HTTPS CORS origins, no local/wildcard origins, and Alembic-managed schemas. Documented proxy allowlist and no-cookie bearer auth. | Security settings tests; actual dev/preview response probes; provider ingress remains unverified. |
| Browser and API headers | Added restrictive frontend document CSP/security headers to production preview and Nginx template. Kept script policy free of unsafe directives; dynamic style attributes have a narrow exception. | Playwright asserts actual production-build response headers; API header tests/probes pass. |
| Request body limit | Added streamed ASGI byte counter, early Content-Length check, 413 handling for Starlette task-group propagation, security/no-store headers, and configured CORS reflection only for an allowed origin. | Normal/exact/declared-overlimit/no-length stream regression tests plus actual Uvicorn chunked >1 MiB probe. |
| Dashboard and transaction monitoring | Replaced illustrative dashboard figures and transaction feed with backend totals, list/search/type/prediction filtering, and persisted details. | API fixtures and production-build browser coverage. |
| Investigations | Added frontend case listing/search/create/details, analyst assignment, priority/status/outcome updates, notes, audit history, and resolve/close workflows. Serializes case mutations to avoid races. | Backend authorization/persistence tests and full Playwright workflow. |
| Analytics and reports | Connected live aggregates, trends, date range, type breakdown filter, verified outcomes, summary, and CSV download. | Known inserted transaction fixture comparison; browser CSV download. |
| Model intelligence | Fetches loaded metadata, artifact training versions, supported features, threshold, calibration note, and only metadata-backed offline metrics. Removed fallback/spec values and fake live drift claim. | Model endpoint and browser check against included artifact. |
| User management | Connected administrator-only user list/create/role/deactivation and audit history. Navigation now filters by role; API remains authoritative. | API role/password-exclusion tests and browser BI/admin scenarios. |
| Sign-out / role switch | Sign-out returns internal navigation to the dashboard so a newly authenticated lower-privilege user is not left on a hidden page. | Browser BI/admin role-switch flow. |
| Security scans | Audited exact Python and pnpm lock graphs. | No known vulnerabilities at scan time. |

## Remaining deployment gates

Configure and verify real TLS/ingress/HSTS/CSP/CORS/proxy headers; test PostgreSQL migrations and multi-worker state; rehearse encrypted database restore; complete model-risk validation on representative real data; perform staging DAST/load/screen-reader checks. See [SECURITY_REPORT.md](SECURITY_REPORT.md) and [PRODUCTION_DEPLOYMENT_CHECKLIST.md](PRODUCTION_DEPLOYMENT_CHECKLIST.md).
