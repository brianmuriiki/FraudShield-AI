# Production deployment checklist

This is an operator checklist, not deployment authorization. No production infrastructure has been changed.

## Verified locally in Phase 3

- [x] Full dependency lock installed into a fresh Python 3.12 virtual environment; `pip check` passed.
- [x] 66 backend tests, 3 frontend unit tests, and 8 Playwright tests passed against the built frontend and isolated backend.
- [x] SQLite migration cycle, local API/frontend headers, model loading/prediction/SHAP, and chunked 413 behavior passed.
- [x] `pip-audit` and `pnpm audit` reported no known vulnerabilities at scan time.
- [ ] Production TLS/ingress, PostgreSQL, provider backups/restore, load, DAST, and screen-reader checks remain unverified.

## Required configuration

- [ ] Set `ENVIRONMENT=production`, a unique `SECRET_KEY` of at least 32 characters, and `AUTO_CREATE_TABLES=false`.
- [ ] Set `DATABASE_URL` to a managed PostgreSQL database with TLS and least-privilege credentials. SQLite is for local development only.
- [ ] Set `CORS_ORIGINS` to exact HTTPS frontend origins. Do not include local hosts or wildcards.
- [ ] Provide `MODEL_DIR` with the three trusted, version-controlled artifact files. Verify them with the checked-in `models/fraudshield-artifacts.sha256` manifest (`sha256sum -c models/fraudshield-artifacts.sha256` from the repository root), then sign the release manifest in the release process.
- [ ] Set login throttling values appropriate to expected traffic; all app workers must share the same database.
- [ ] Configure `MAX_REQUEST_BYTES` consistently with ingress (default 1 MiB).
- [ ] Do not enable public registration without a separate registration abuse limit and operational review.
- [ ] Do not configure session cookies: authentication uses bearer tokens kept in frontend memory. Cookies are not used.

## TLS, proxy, and browser policy

- [ ] Install certificates and private keys in the ingress secret store; mount them read-only at configured paths.
- [ ] Render `deploy/nginx.conf.template` with `PUBLIC_HOST`, `TLS_CERTIFICATE_PATH`, `TLS_PRIVATE_KEY_PATH`, and `API_ORIGIN`. Restrict substitution to template variables so Nginx variables such as `$host` and `$request_uri` remain intact:

  ```bash
  envsubst '${PUBLIC_HOST} ${TLS_CERTIFICATE_PATH} ${TLS_PRIVATE_KEY_PATH} ${API_ORIGIN}' \
    < deploy/nginx.conf.template > /etc/nginx/conf.d/fraudshield.conf
  ```
- [ ] Verify port 80 redirects to HTTPS, TLS 1.2/1.3 works, HSTS is present, and unknown origins receive no CORS permission.
- [ ] Allow only the actual ingress addresses in Uvicorn `--forwarded-allow-ips`; never trust `*` on an internet-facing listener. Run `uvicorn app.main:app --proxy-headers --forwarded-allow-ips="$TRUSTED_PROXY_ALLOW_IPS"` behind the proxy.
- [ ] The Nginx CSP has no script `unsafe-inline` or `unsafe-eval`. It allows inline style attributes because current React components use dynamic width styles; replace these with classes/CSS variables if the policy must forbid inline styles.
- [ ] Browser bearer tokens are not persisted. API responses carry `Cache-Control: no-store`.

## Database lifecycle and recovery

- [ ] Back up the production database before migration; run `alembic upgrade head` as a one-off release step.
- [ ] Verify automated encrypted backups, retention, point-in-time recovery, and restore into an isolated database before launch.
- [ ] Document restore owner, recovery point objective, recovery time objective, and rollback steps. These procedures have not been exercised against provider infrastructure.

## Operations

- [ ] Configure structured application logs, redaction for authorization headers/passwords, retention, alerting, and an error-reporting destination.
- [ ] Probe `/api/v1/health` and `/api/v1/ready`; alert on non-200 status and database/model/explainer failures.
- [ ] Monitor login 429 rates, 413 responses, 5xx rates, request latency, database pool pressure, and disk/storage availability.
- [ ] Ensure upload/request limits at ingress and application are aligned; retain proxy buffering safeguards and test chunked requests through the actual ingress.
- [ ] Scan the pinned backend and frontend dependencies for advisories during every release and on a scheduled cadence.
- [ ] Validate model artifacts, dependency compatibility, prediction parity, and SHAP explanations in the deployment image before rollout.
- [ ] Deploy to staging first, run migration and end-to-end smoke checks, and retain a rollback image.

## Release decision gates

- [ ] Production-origin header and TLS probes pass from an external test client.
- [ ] Database backup/restore and failover procedures are tested by the hosting operator.
- [ ] Concurrency, load, DAST, and screen-reader checks are completed for the target environment.
- [ ] Product/security owners accept limitations of synthetic PaySim training data and offline-only model metrics.
