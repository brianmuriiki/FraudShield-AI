import joblib
import pytest

from app.core.config import settings
from app.schemas.transaction import TransactionInput
from app.services.ml_service import REQUIRED_FILES, ml_service
from app.utils.feature_processing import FEATURE_ORDER, SUPPORTED_TYPES, build_feature_dict, build_feature_frame, one_hot_type
from app.utils.helpers import risk_level_for
from tests.utils import PAYMENT_PAYLOAD, TRANSFER_PAYLOAD, requires_model

API = "/api/v1"


# ------------------------- pure unit tests (no model needed) -------------------------
def test_feature_order_is_exact():
    assert FEATURE_ORDER == ["step", "amount", "oldbalanceOrg", "oldbalanceDest", "type_CASH_IN",
                             "type_CASH_OUT", "type_DEBIT", "type_PAYMENT", "type_TRANSFER"]
    frame = build_feature_frame(1, 2.0, 3.0, 4.0, "DEBIT")
    assert list(frame.columns) == FEATURE_ORDER and frame.shape == (1, 9)


@pytest.mark.parametrize("ttype", SUPPORTED_TYPES)
def test_one_hot_exactly_one_active(ttype):
    enc = one_hot_type(ttype)
    assert sum(enc.values()) == 1 and enc[f"type_{ttype}"] == 1
    assert list(build_feature_dict(1, 1.0, 1.0, 1.0, ttype)) == FEATURE_ORDER


def test_unsupported_type_rejected():
    with pytest.raises(ValueError):
        one_hot_type("WIRE")


def test_risk_levels_and_threshold_boundaries():
    t = 0.468
    assert [risk_level_for(s, t) for s in (0.0, 0.0999, 0.10, 0.2999, 0.30, 0.4679, 0.468, 1.0)] == [
        "Low", "Low", "Moderate", "Moderate", "Elevated", "Elevated", "High", "High"]


@pytest.mark.parametrize("score,expected", [(0.467, "Not Flagged"), (0.468, "Suspicious"), (0.469, "Suspicious")])
def test_prediction_decision_uses_full_precision_at_threshold(score, expected):
    class FixedModel:
        def predict_proba(self, _frame):
            return [[1.0 - score, score]]

    original = (ml_service.loaded, ml_service.calibrated_model, ml_service.threshold)
    try:
        ml_service.loaded = True
        ml_service.calibrated_model = FixedModel()
        ml_service.threshold = 0.468
        result = ml_service.predict_transaction(TransactionInput(**PAYMENT_PAYLOAD))
        assert result["fraud_score"] == score
        assert result["prediction"] == expected
        assert result["requires_investigation"] == (expected == "Suspicious")
    finally:
        ml_service.loaded, ml_service.calibrated_model, ml_service.threshold = original


def test_input_schema_normalises_and_rejects():
    assert TransactionInput(**{**PAYMENT_PAYLOAD, "transaction_type": "cash out"}).transaction_type.value == "CASH_OUT"
    for bad in ({"amount": -1.0}, {"oldbalanceOrg": -5.0}, {"step": -1}, {"step": 1.5},
                {"amount": "100"}, {"transaction_type": "WIRE"}):
        with pytest.raises(Exception):
            TransactionInput(**{**PAYMENT_PAYLOAD, **bad})


def test_exact_nine_feature_request_maps_to_supported_transaction_type():
    payload = {key: value for key, value in PAYMENT_PAYLOAD.items() if key != "transaction_type"}
    payload.update({f"type_{name}": int(name == "PAYMENT") for name in SUPPORTED_TYPES})
    parsed = TransactionInput(**payload)
    assert parsed.transaction_type.value == "PAYMENT"


@pytest.mark.parametrize("indicators", [
    {"type_CASH_IN": 1, "type_CASH_OUT": 1, "type_DEBIT": 0, "type_PAYMENT": 0, "type_TRANSFER": 0},
    {"type_CASH_IN": 0, "type_CASH_OUT": 0, "type_DEBIT": 0, "type_PAYMENT": 0, "type_TRANSFER": 0},
    {"type_CASH_IN": 0, "type_CASH_OUT": 0, "type_DEBIT": 0, "type_PAYMENT": 0, "type_TRANSFER": 2},
])
def test_invalid_one_hot_feature_vectors_rejected(indicators):
    payload = {key: value for key, value in PAYMENT_PAYLOAD.items() if key != "transaction_type"}
    with pytest.raises(Exception):
        TransactionInput(**{**payload, **indicators})


def test_unauthenticated_predict_rejected(client):
    assert client.post(f"{API}/predictions/predict", json=TRANSFER_PAYLOAD).status_code == 401


def test_validation_errors_return_422(client, analyst_headers):
    for bad in ({"amount": -1.0}, {"transaction_type": "WIRE"}, {"step": -3}, {"step": 1.5}):
        r = client.post(f"{API}/predictions/predict", json={**PAYMENT_PAYLOAD, **bad}, headers=analyst_headers)
        assert r.status_code == 422, bad
    missing = {k: v for k, v in PAYMENT_PAYLOAD.items() if k != "amount"}
    assert client.post(f"{API}/predictions/predict", json=missing, headers=analyst_headers).status_code == 422
    one_hot = {f"type_{name}": int(name == "PAYMENT") for name in SUPPORTED_TYPES}
    invalid_one_hot = {**{k: v for k, v in PAYMENT_PAYLOAD.items() if k != "transaction_type"},
                       **{**one_hot, "type_CASH_OUT": 1}}
    assert client.post(f"{API}/predictions/predict", json=invalid_one_hot, headers=analyst_headers).status_code == 422


# ------------------------------ tests needing the real model ------------------------------
@requires_model
def test_model_artifacts_load():
    assert ml_service.loaded, ml_service.error
    assert ml_service.threshold == pytest.approx(0.468, abs=5e-4)
    assert ml_service.describe()["feature_count"] == 9


@requires_model
def test_api_prediction_matches_direct_model(client, analyst_headers):
    direct_model = joblib.load(settings.MODEL_DIR / REQUIRED_FILES["calibrated"])
    for payload in (TRANSFER_PAYLOAD, PAYMENT_PAYLOAD):
        frame = build_feature_frame(payload["step"], payload["amount"], payload["oldbalanceOrg"],
                                    payload["oldbalanceDest"], payload["transaction_type"])
        expected = float(direct_model.predict_proba(frame)[0][1])
        r = client.post(f"{API}/predictions/predict", json=payload, headers=analyst_headers)
        assert r.status_code == 200, r.text
        body = r.json()
        assert 0.0 <= body["fraud_score"] <= 1.0
        assert body["fraud_score"] == pytest.approx(expected, abs=1e-6)
        assert body["threshold"] == pytest.approx(0.468, abs=5e-4)
        assert (body["prediction"] == "Suspicious") == (body["fraud_score"] >= body["threshold"])
        assert body["requires_investigation"] == (body["prediction"] == "Suspicious")
        assert body["transaction_id"].startswith("TXN-")


@requires_model
def test_nine_feature_frontend_request_is_scored_and_persisted(client, analyst_headers):
    one_hot = {f"type_{name}": int(name == "PAYMENT") for name in SUPPORTED_TYPES}
    payload = {**{k: v for k, v in PAYMENT_PAYLOAD.items() if k != "transaction_type"}, **one_hot}
    response = client.post(f"{API}/predictions/predict", json=payload, headers=analyst_headers)
    assert response.status_code == 200, response.text
    result = response.json()
    assert set(("fraud_score", "threshold", "prediction", "transaction_id")) <= result.keys()
    assert result["transaction_type"] == "PAYMENT"
    stored = client.get(f"{API}/transactions/{result['transaction_id']}", headers=analyst_headers)
    assert stored.status_code == 200 and stored.json()["fraud_score"] == result["fraud_score"]


@requires_model
@pytest.mark.parametrize("ttype", SUPPORTED_TYPES)
def test_all_five_types_accepted(client, analyst_headers, ttype):
    r = client.post(f"{API}/predictions/predict", json={**PAYMENT_PAYLOAD, "transaction_type": ttype},
                    headers=analyst_headers)
    assert r.status_code == 200 and r.json()["transaction_type"] == ttype


@requires_model
def test_shap_explanation_is_consistent_with_xgboost(client, analyst_headers):
    r = client.post(f"{API}/predictions/explain", json=TRANSFER_PAYLOAD, headers=analyst_headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert {f["feature"] for f in body["features"]} == set(FEATURE_ORDER) and len(body["features"]) == 9
    assert body["explanation_method"] == "SHAP"
    # SHAP additivity: base value + contributions == raw XGBoost margin
    xgb = joblib.load(settings.MODEL_DIR / REQUIRED_FILES["xgboost"])
    frame = build_feature_frame(379, 36942.13, 36942.13, 0, "TRANSFER")
    margin = float(xgb.predict(frame, output_margin=True)[0])
    assert body["raw_output"] == pytest.approx(margin, abs=1e-3)


@requires_model
def test_model_metadata_endpoint(client, analyst_headers):
    r = client.get(f"{API}/model/metadata", headers=analyst_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["threshold"] == pytest.approx(0.468, abs=5e-4) and body["feature_count"] == 9
    assert "calibration_warning" in body and "offline" in body["metrics_note"].lower()
    assert body["metrics_source"] == "model metadata"
    assert body["metrics"]["precision"] == pytest.approx(0.967628)
    assert body["confusion_matrix"] is None  # the artifact contains none; never substitute a specification example
