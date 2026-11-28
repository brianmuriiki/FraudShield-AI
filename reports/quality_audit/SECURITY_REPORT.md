# FraudShield AI security report — Phase 3

**Scope:** source review, 66 backend tests, frontend unit tests, production-build Playwright/axe checks, real local response probes, dependency advisory scans, and a disposable SQLite database. No production target or real financial data was accessed.

## Verified controls

- **Authentication and sessions — PASS.** JWT expiry/signature checks, server-side `jti` revocation, memory-only browser token, logout invalidation, shared-database login throttling, and generic login failure behavior are covered by regression tests.
- **Authorization — PASS locally.** API role checks gate investigations, analytics, and admin user routes. Browser navigation hides restricted surfaces; BI API attempts to access `/users` are denied. Navigation is only a presentation control; backend checks remain authoritative.
- **Request body limits — PASS locally.** A streaming ASGI wrapper enforces `MAX_REQUEST_BYTES` without accumulating the full body. It handles oversized declared lengths and chunked bodies with no `Content-Length`; the real Uvicorn probe returned HTTP 413, `Cache-Control: no-store`, and a JSON error.
- **API headers — PASS locally.** API responses include `nosniff`, no-referrer, frame denial, restrictive API CSP, and no-store for `/api/v1`. HSTS is only returned by the ASGI app when production mode sees HTTPS; production TLS termination is expected to set it at ingress.
- **Frontend document CSP — PASS in production-build preview.** Actual preview responses included `script-src 'self'` without script `unsafe-inline` or `unsafe-eval`, exact API `connect-src`, `object-src 'none'`, frame denial, and the other configured headers. The policy uses `style-src-attr 'unsafe-inline'` for current dynamic data-bar styles only. The provider-facing Nginx configuration was not run here.
- **CORS — PASS locally.** Exact configured origins are used and wildcard origins are rejected in production settings. Credentials are not enabled because auth uses bearer headers and no cookies. Production origins have to be provider-configured and re-probed.
- **Sensitive caching — PASS locally.** API paths return `Cache-Control: no-store` and `Pragma: no-cache`. Authentication does not use browser cookies; there is no cookie attribute to configure.
- **Dependencies — PASS at scan time.** The full pinned backend lock installed from scratch; `pip-audit` and `pnpm audit` found no known vulnerabilities. This is a point-in-time advisory result, not an ongoing monitoring service.
- **Data presentation — PASS.** Model metrics, versions, and calibration notes come from the trusted loaded model artifact; absent confusion-matrix metadata remains null. No frontend-simulated drift or retraining status is presented.

## Open findings

| ID | Severity | Affected area and impact | Required action | Deployment blocker? |
|---|---|---|---|---|
| FS-11 | High | HTTPS ingress, TLS certificates, HSTS, browser CSP, reverse-proxy headers, and trusted proxy addresses have only a local template/preview verification. Incorrect proxy trust can expose spoofed client scheme/IP data or omit transport controls. | Deploy the rendered Nginx/provider equivalent to staging; restrict `--forwarded-allow-ips`; externally probe redirects, TLS, HSTS, CSP, CORS, and chunked 413 behavior. | Yes |
| FS-12 | High | Target PostgreSQL connection, migration behavior, and multi-instance revocation/throttle persistence are not proven against production infrastructure. | Exercise the exact PostgreSQL version and provider config in staging; verify migrations, connection TLS, shared state, and concurrent behavior. | Yes |
| FS-13 | High | No verified backup restore/recovery operation. | Configure encrypted backups and perform a restore rehearsal with documented RPO/RTO. | Yes |
| FS-14 | High | Model uses synthetic PaySim data and offline evaluation; actual payment distribution, fairness, calibration, and business impact are unvalidated. | Model-risk owner must validate representative real data and approve the intended use before real payment decisions. | Yes for live scoring decisions |
| FS-15 | Medium | Login attempt count/insert is not strictly atomic under heavy simultaneous bursts. | Load test expected concurrency; adopt an atomic shared limiter if hard thresholds are required. | Conditional |
| FS-16 | Medium | No OWASP DAST, sustained load/multi-worker, screen-reader, or provider ingress scan. | Complete in a staging environment and track findings. | Yes under acceptance criteria |
| FS-17 | Low | PDF export returns 501; CSV is functional. | Implement only if PDF is a deployment requirement. | No |

## Risk notes

- SQLite is a test/development backend; production guidance requires TLS-enabled PostgreSQL and shared state across workers.
- Public registration remains disabled by default. If enabled, add a registration-specific abuse quota.
- CSP intentionally permits inline style attributes, but not inline scripts. Remove the style exception if the frontend is updated to avoid dynamic inline styles.
- Local API security-header probes used HTTP; production HSTS and certificate behavior remain ingress responsibilities.
- Dashboard and analytics report historical stored data accurately. `Suspicious` remains a model flag, while `Confirmed Fraud` requires an analyst outcome.

## Conclusion

No known critical/high dependency advisories were reported by the final scans. Several **high-severity operational and model-risk findings remain open**, so FraudShield is **not production-ready** until the listed provider, recovery, and model-validation gates are evidenced.
