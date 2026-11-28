from tests.utils import PAYMENT_PAYLOAD, requires_model

API = "/api/v1"


def test_dashboard_requires_auth(client):
    assert client.get(f"{API}/dashboard/summary").status_code == 401


def test_dashboard_structure_and_consistency(client, bi_headers):
    r = client.get(f"{API}/dashboard/summary", headers=bi_headers)
    assert r.status_code == 200
    d = r.json()
    for key in ("total_transactions", "suspicious_transactions", "not_flagged_transactions", "confirmed_fraud_cases",
                "pending_investigations", "open_investigations", "resolved_investigations", "suspicious_trend"):
        assert key in d
    assert d["total_transactions"] == d["suspicious_transactions"] + d["not_flagged_transactions"]
    assert len(d["suspicious_trend"]) == 30


def test_analytics_access_control(client, analyst_headers, bi_headers):
    assert client.get(f"{API}/analytics/overview", headers=bi_headers).status_code == 200
    assert client.get(f"{API}/analytics/overview", headers=analyst_headers).status_code == 403
    assert client.get(f"{API}/analytics/overview", params={"date_from": "2026-02-01", "date_to": "2026-01-01"},
                      headers=bi_headers).status_code == 400
    for p in ("transactions", "fraud-trends", "transaction-types", "investigations"):
        assert client.get(f"{API}/analytics/{p}", headers=bi_headers).status_code == 200, p
    assert client.get(f"{API}/reports/summary", headers=bi_headers).status_code == 200
    assert client.get(f"{API}/reports/export", params={"format": "pdf"}, headers=bi_headers).status_code == 501


def test_verified_performance_never_uses_unverified_predictions(client, bi_headers):
    perf = client.get(f"{API}/analytics/overview", headers=bi_headers).json()["verified_performance"]
    assert perf["verified_cases"] == perf["true_positives"] + perf["false_positives"] + perf["false_negatives"] + perf["true_negatives"]
    assert "caveat" in perf


@requires_model
def test_analytics_and_csv_report_reflect_persisted_fixture(client, analyst_headers, bi_headers):
    before = client.get(f"{API}/analytics/overview", headers=bi_headers).json()
    tx = client.post(f"{API}/transactions", json=PAYMENT_PAYLOAD, headers=analyst_headers)
    assert tx.status_code == 201, tx.text
    after = client.get(f"{API}/analytics/overview", headers=bi_headers).json()
    assert after["total_transactions"] == before["total_transactions"] + 1
    assert after["average_amount"] is not None
    types = client.get(f"{API}/analytics/transaction-types", headers=bi_headers).json()["types"]
    assert sum(item["total"] for item in types) == after["total_transactions"]
    report = client.get(f"{API}/reports/export?format=csv", headers=bi_headers)
    assert report.status_code == 200 and report.headers["content-type"].startswith("text/csv")
    assert tx.json()["transaction_id"] in report.text
