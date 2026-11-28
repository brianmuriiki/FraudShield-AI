# FraudShield frontend API integration

The browser API client is in `src/api.ts`. Set `VITE_API_BASE_URL` to the FastAPI origin, with or without `/api/v1`; when omitted, requests use the current origin. The client normalizes the base path and returns API errors to the page for display. Login uses the backend bearer-token endpoint; the token is held in memory and discarded on sign out or page reload.

For local development, copy `.env.example` to `.env.local` so Vite sends requests to the backend on port 8000. The backend must separately be configured and started as described in `../backend/README.md`.

## Prediction request

`POST /api/v1/predictions/predict` accepts exactly these nine model inputs:

```json
{
  "step": 1,
  "amount": 125.5,
  "oldbalanceOrg": 500,
  "oldbalanceDest": 20,
  "type_CASH_IN": 0,
  "type_CASH_OUT": 0,
  "type_DEBIT": 0,
  "type_PAYMENT": 1,
  "type_TRANSFER": 0
}
```

The five type fields are one-hot encoded and exactly one must be `1`. The backend maps those inputs to the selected supported type and reconstructs the model frame in canonical order. The current UI validates non-negative amount and balances and a non-negative whole-number step. The backend prediction response includes `fraud_score` (finite, in `[0, 1]`), `threshold`, `prediction`, `transaction_id`, and related model fields. The UI applies the returned threshold (the configured value is `0.468`). It requests a stored explanation from `GET /api/v1/predictions/explain/{transaction_id}`; the backend returns SHAP `features` with contribution, influence, and description. If SHAP is unavailable, a successful prediction remains visible with the explanation unavailable state.

The frontend uses implemented endpoints for transaction search/detail, dashboard totals, investigation creation/assignment/status/outcomes/notes/history, analytics date ranges, CSV export, model metadata, and administrator user listing/creation/role changes/deactivation/audit logs. Role restrictions are enforced by the backend; navigation hides pages that the signed-in role cannot use but is not an authorization boundary.

## Production build and response headers

Set `VITE_API_BASE_URL` at build time to the API origin (or same-origin reverse-proxy path). The reverse-proxy example is `../deploy/nginx.conf.template`; render it with the provider host, certificate paths, and API origin. The frontend security headers must be set by that hosting layer because the backend API CSP does not cover `index.html` or static assets.

CSV reports download from `/api/v1/reports/export`. PDF is not implemented. Model intelligence displays metrics only when present in loaded model metadata and labels them as offline; it does not report live drift monitoring.
