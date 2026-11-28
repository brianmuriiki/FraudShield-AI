from tests.utils import MODEL_PRESENT

API = "/api/v1"


def test_health_reports_components_honestly(client):
    r = client.get(f"{API}/health")
    body = r.json()
    assert body["database"] == "connected"
    if MODEL_PRESENT:
        assert r.status_code == 200 and body["status"] == "healthy"
        assert body["model"] == "loaded" and body["model_name"] == "FraudShield XGBoost"
    else:  # must never claim to be healthy without a model
        assert r.status_code == 503 and body["status"] == "unhealthy" and body["model"] == "unavailable"


def test_ready_matches_health(client):
    assert client.get(f"{API}/ready").status_code == client.get(f"{API}/health").status_code
