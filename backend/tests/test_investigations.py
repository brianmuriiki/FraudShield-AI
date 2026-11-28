from tests.utils import PAYMENT_PAYLOAD, requires_model

API = "/api/v1"
pytestmark = requires_model


def _tx(client, headers):
    return client.post(f"{API}/transactions", json=PAYMENT_PAYLOAD, headers=headers).json()["transaction_id"]


def _open(client, headers, tx_ref, **extra):
    return client.post(f"{API}/investigations", json={"transaction_id": tx_ref, **extra}, headers=headers)


def test_create_duplicate_and_bi_forbidden(client, analyst_headers, bi_headers):
    ref = _tx(client, analyst_headers)
    r = _open(client, analyst_headers, ref, notes="Initial concern")
    assert r.status_code == 201, r.text
    inv = r.json()
    assert inv["status"] == "New" and inv["outcome"] == "Pending" and len(inv["notes"]) == 1
    assert _open(client, analyst_headers, ref).status_code == 409
    assert _open(client, bi_headers, ref).status_code == 403
    assert client.get(f"{API}/investigations/{inv['investigation_reference']}", headers=bi_headers).status_code == 403
    assert _open(client, analyst_headers, "TXN-NOPE0000").status_code == 404


def test_fraud_analyst_cannot_set_outcome_or_resolve(client, analyst_headers, senior_headers):
    inv = _open(client, analyst_headers, _tx(client, analyst_headers)).json()
    url = f"{API}/investigations/{inv['investigation_reference']}"
    assert client.patch(url, json={"status": "Under Review"}, headers=analyst_headers).status_code == 200
    assert client.patch(url, json={"outcome": "Confirmed Fraud"}, headers=analyst_headers).status_code == 403
    assert client.patch(url, json={"status": "Resolved"}, headers=analyst_headers).status_code == 403
    assert client.patch(url, json={"outcome": "Confirmed Fraud"}, headers=senior_headers).status_code == 200


def test_resolve_requires_outcome_and_sets_timestamp(client, analyst_headers, senior_headers):
    inv = _open(client, analyst_headers, _tx(client, analyst_headers)).json()
    url = f"{API}/investigations/{inv['investigation_reference']}"
    assert client.patch(url, json={"status": "Resolved"}, headers=senior_headers).status_code == 400
    r = client.patch(url, json={"status": "Resolved", "outcome": "Legitimate Transaction"}, headers=senior_headers)
    assert r.status_code == 200 and r.json()["resolved_at"] is not None
    assert any(h["action"] == "investigation_outcome_changed" for h in r.json()["history"])


def test_prediction_never_sets_outcome(client, analyst_headers):
    ref = _tx(client, analyst_headers)
    tx = client.get(f"{API}/transactions/{ref}", headers=analyst_headers).json()
    assert tx["investigation_status"] in ("Awaiting Investigation", "Not Required")
    assert client.get(f"{API}/investigations", params={"transaction_id": ref}, headers=analyst_headers).json()["total"] == 0


def test_assignment_and_notes(client, analyst_headers, senior_headers, admin_headers):
    inv = _open(client, analyst_headers, _tx(client, analyst_headers)).json()
    url = f"{API}/investigations/{inv['investigation_reference']}"
    me = client.get(f"{API}/auth/me", headers=analyst_headers).json()
    assert client.patch(url, json={"assigned_analyst_id": me["id"]}, headers=analyst_headers).status_code == 403
    r = client.patch(url, json={"assigned_analyst_id": me["id"]}, headers=senior_headers)
    assert r.status_code == 200 and r.json()["assigned_analyst"]["id"] == me["id"]
    n = client.post(f"{url}/notes", json={"content": "Called the customer."}, headers=analyst_headers)
    assert n.status_code == 201 and n.json()["author_name"]
    assert client.post(f"{url}/notes", json={"content": ""}, headers=analyst_headers).status_code == 422
