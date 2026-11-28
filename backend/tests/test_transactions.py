from tests.utils import PAYMENT_PAYLOAD, TRANSFER_PAYLOAD, requires_model

API = "/api/v1"
pytestmark = requires_model


def _create(client, headers, payload):
    r = client.post(f"{API}/transactions", json=payload, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()


def test_create_and_retrieve(client, analyst_headers):
    created = _create(client, analyst_headers, TRANSFER_PAYLOAD)
    assert created["transaction_id"].startswith("TXN-") and created["created_at"].endswith("Z")
    got = client.get(f"{API}/transactions/{created['transaction_id']}", headers=analyst_headers)
    assert got.status_code == 200 and got.json()["fraud_score"] == created["fraud_score"]
    assert client.get(f"{API}/transactions/TXN-DOESNOTEXIST", headers=analyst_headers).status_code == 404


def test_search_treats_sql_metacharacters_as_literal_text(client, analyst_headers):
    response = client.get(f"{API}/transactions", params={"search": "%' OR 1=1 --"}, headers=analyst_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 0


def test_bi_analyst_cannot_create_but_can_read(client, bi_headers, analyst_headers):
    assert client.post(f"{API}/transactions", json=PAYMENT_PAYLOAD, headers=bi_headers).status_code == 403
    assert client.get(f"{API}/transactions", headers=bi_headers).status_code == 200


def test_listing_pagination_filters_and_stats_route(client, analyst_headers):
    for _ in range(3):
        _create(client, analyst_headers, PAYMENT_PAYLOAD)
    page = client.get(f"{API}/transactions", params={"page": 1, "page_size": 2}, headers=analyst_headers).json()
    assert len(page["items"]) == 2 and page["total"] >= 3 and page["pages"] >= 2
    by_type = client.get(f"{API}/transactions", params={"transaction_type": "PAYMENT"}, headers=analyst_headers).json()
    assert by_type["total"] >= 3 and all(t["transaction_type"] == "PAYMENT" for t in by_type["items"])
    ref = by_type["items"][0]["transaction_id"]
    found = client.get(f"{API}/transactions", params={"search": ref[:8]}, headers=analyst_headers).json()
    assert any(t["transaction_id"] == ref for t in found["items"])
    big = client.get(f"{API}/transactions", params={"min_amount": 1_000_000_000}, headers=analyst_headers).json()
    assert big["total"] == 0
    stats = client.get(f"{API}/transactions/stats", headers=analyst_headers)
    assert stats.status_code == 200 and stats.json()["total"] == stats.json()["suspicious"] + stats.json()["not_flagged"]
    assert client.get(f"{API}/transactions", params={"page_size": 10_000}, headers=analyst_headers).status_code == 422
