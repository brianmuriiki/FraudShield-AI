# Phase 3 feature and verification matrix

Statuses: **PASS** verified locally; **PARTIAL** has explicit unverified deployment/product work; **NOT IMPLEMENTED** unavailable by design/product scope.

| Feature | Implemented behavior | Verification | Status |
|---|---|---|---|
| Authentication | Backend login/logout, in-memory token, logout revocation, refresh returns to sign-in | Pytest + production-build browser login/logout/old-token rejection | PASS |
| Authorization | Backend role enforcement and role-aware navigation | Pytest role cases; Playwright confirms BI cannot access admin route and does not see admin nav | PASS locally |
| Dashboard | Real stored transaction totals, suspicious flags, confirmed cases, amount and risk distribution | Dashboard fixture/API consistency tests and browser page/API | PASS |
| Transaction monitoring | Live paginated list, text/type/prediction filters, score, timestamp, and detail drawer | Backend list/detail tests and production browser filter/detail tests | PASS |
| Fraud prediction / SHAP | Real loaded calibrated model, unchanged 0.468 threshold and feature order, stored prediction, nine-feature explanation | Direct model parity, boundary/SHAP tests and browser prediction/explanation | PASS |
| Investigations | List/search/create/detail, assignment, priority, status, outcome, notes, history, resolve and close | Role/persistence pytest plus browser workflow that creates, assigns, notes, resolves, closes and rereads | PASS |
| Analytics | Real database totals, daily volume, flagged/confirmed trends, type distribution, outcome and verified performance | Fixture comparison against known inserted transaction; date-range/API tests and browser rendering | PASS |
| Transaction type filtering | Backend transaction list filters by supported transaction type; analytics view filters its type breakdown | API and browser filter controls | PASS |
| Reports | Summary endpoint and CSV download with optional date range | API content/record tests and browser download assertion | PASS |
| PDF export | Not implemented by existing backend; endpoint returns 501 | Backend response test | NOT IMPLEMENTED; CSV available |
| Model intelligence | Loaded status, name, unspecified version when artifact omits it, threshold, feature order, dataset, trained library versions, verified offline metrics and artifact notes | Model metadata pytest plus browser checks against loaded artifact | PASS |
| Model live monitoring | No operational drift/retraining service is present; UI no longer simulates it | Source inspection and browser content review | NOT IMPLEMENTED; not misrepresented |
| User management | Admin user list/create, role update, deactivate, audit log; no password hash in response | API authorization/security tests and browser create/role/deactivate/reject login flow | PASS |
| Request size | Content-Length early rejection plus streamed receive-byte cap; 413 with no-store/security headers | Boundary/missing-length/chunked ASGI tests and real Uvicorn chunked request >1 MiB | PASS locally |
| Security headers/CSP | API headers and production-build frontend CSP; script unsafe directives absent; exact API connect origin | Header pytest, browser header assertion, actual local HTTP probes | PASS locally; production TLS ingress unverified |
| CORS / proxy / HTTPS | Exact origin configuration; production rejects local/HTTP/wildcard origins; proxy template and trusted proxy command documented | Settings regression tests; dev CORS browser/API; template reviewed | PARTIAL: staging/prod ingress not available |
| Database / migrations | ORM persistence, Alembic schema, login revocation and investigation persistence | Complete SQLite suite and upgrade/downgrade/upgrade cycle | PARTIAL: production PostgreSQL and backup restore unverified |
| Dependency reproducibility | Exact direct pins and full transitive lock, model-compatible ML versions | Fresh Python 3.12 lock install, pip check, pip-audit; pnpm audit | PASS at scan time |
| Accessibility/mobile | Labels, keyboard focus, dialog focus handling, mobile nav; current connected pages | Axe zero violations on eight surfaces, keyboard tests, 375 px Playwright test | PASS for tested surfaces/viewports |
| Operations | Health/ready, deployment checklist, ingress template, log/monitor/backup guidance | Local health probe; checklist review | PARTIAL: provider logging/monitoring and recovery not exercised |

**Overall production acceptance:** **NOT MET.** See open deployment gates in [FULL_AUDIT_REPORT.md](FULL_AUDIT_REPORT.md) and [PRODUCTION_DEPLOYMENT_CHECKLIST.md](PRODUCTION_DEPLOYMENT_CHECKLIST.md).
