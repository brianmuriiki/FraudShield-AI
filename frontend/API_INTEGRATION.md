# FraudShield frontend API integration

The browser API client is in `src/api.ts`. Set `VITE_API_BASE_URL` to the FastAPI origin; when omitted, requests use the current origin. The client prefixes routes with `/api/v1` and returns API errors to the page for display.

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

The five type fields are one-hot encoded and exactly one must be `1`. The current UI validates non-negative amount and balances and a non-negative whole-number step. A successful response must include `risk_score` as a finite number from 0 through 1. Optional fields are `threshold`, `prediction`, `status`, `transaction_id`, and SHAP `explanation` entries (`feature`, `value`, `contribution`, optional `relative_influence`). The UI defaults the threshold to `0.468` and flags scores greater than or equal to it as suspicious.

The API module also defines the proposed transaction, dashboard, model metadata, SHAP explanation, and investigation routes so their contracts can be adjusted as the FastAPI implementation is finalized. Pages without a live backend data contract currently display unavailable states; retained dashboard and transaction examples are explicitly marked as demonstration data.
