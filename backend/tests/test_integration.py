from tests.utils import TRANSFER_PAYLOAD, requires_model

API = "/api/v1"
pytestmark = requires_model


def test_full_workflow(client, analyst_headers, senior_headers, bi_headers):
    before = client.get(f"{API}/dashboard/summary", headers=bi_headers).json()

    # 1-3: submit, predict, save
    pred = client.post(f"{API}/predictions/predict", json=TRANSFER_PAYLOAD, headers=analyst_headers)
    assert pred.status_code == 200
    ref, flagged = pred.json()["transaction_id"], pred.json()["prediction"] == "Suspicious"

    # 4: retrieve
    assert client.get(f"{API}/transactions/{ref}", headers=analyst_headers).json()["prediction"] == pred.json()["prediction"]

    # 5: SHAP explanation for the stored transaction
    exp = client.get(f"{API}/predictions/explain/{ref}", headers=analyst_headers)
    assert exp.status_code == 200 and exp.json()["transaction_id"] == ref

    # 6-7: create investigation and assign
    inv = client.post(f"{API}/investigations", json={"transaction_id": ref}, headers=analyst_headers).json()
    url = f"{API}/investigations/{inv['investigation_reference']}"
    analyst_id = client.get(f"{API}/auth/me", headers=analyst_headers).json()["id"]
    assert client.patch(url, json={"assigned_analyst_id": analyst_id}, headers=senior_headers).status_code == 200

    # 8-9: note + status update
    assert client.post(f"{url}/notes", json={"content": "Reviewed sender history."}, headers=analyst_headers).status_code == 201
    assert client.patch(url, json={"status": "Under Review"}, headers=analyst_headers).status_code == 200

    mid = client.get(f"{API}/dashboard/summary", headers=bi_headers).json()
    assert mid["open_investigations"] == before["open_investigations"] + 1

    # 10: outcome
    done = client.patch(url, json={"status": "Resolved", "outcome": "Confirmed Fraud"}, headers=senior_headers)
    assert done.status_code == 200 and done.json()["resolved_at"]

    # 11: dashboard reflects stored records
    after = client.get(f"{API}/dashboard/summary", headers=bi_headers).json()
    assert after["total_transactions"] == before["total_transactions"] + 1
    assert after["suspicious_transactions"] == before["suspicious_transactions"] + (1 if flagged else 0)
    assert after["confirmed_fraud_cases"] == before["confirmed_fraud_cases"] + 1
    assert after["open_investigations"] == before["open_investigations"]
    assert after["resolved_investigations"] == before["resolved_investigations"] + 1
    assert len(done.json()["history"]) >= 4
