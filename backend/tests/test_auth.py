from sqlalchemy import select
from datetime import datetime, timedelta, timezone
import uuid

import jwt
import pytest

from app.database.session import SessionLocal
from app.models.audit_log import AuditLog
from app.models.user import User
from tests.conftest import ADMIN
from app.core.config import settings
from app.core.security import create_access_token
from app.models.security import RevokedToken
from app.services.auth_controls import token_is_revoked

API = "/api/v1"


def test_login_success_and_me(client):
    r = client.post(f"{API}/auth/login", json={"email": ADMIN[0], "password": ADMIN[1]})
    assert r.status_code == 200
    body = r.json()
    assert body["token_type"] == "bearer" and "hashed_password" not in body["user"]
    me = client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200 and me.json()["role"] == "administrator"


def test_form_login_for_swagger(client):
    r = client.post(f"{API}/auth/token", data={"username": ADMIN[0], "password": ADMIN[1]})
    assert r.status_code == 200


def test_invalid_credentials_rejected_and_audited(client):
    r = client.post(f"{API}/auth/login", json={"email": ADMIN[0], "password": "wrong-password"})
    assert r.status_code == 401
    assert client.post(f"{API}/auth/login", json={"email": "nobody@test.local", "password": "x"}).status_code == 401
    with SessionLocal() as db:
        assert db.scalar(select(AuditLog).where(AuditLog.action == "login_failed")) is not None


def test_protected_endpoints_require_token(client):
    for path in ("/auth/me", "/transactions", "/investigations", "/dashboard/summary", "/model/metadata"):
        assert client.get(f"{API}{path}").status_code == 401, path
    assert client.get(f"{API}/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_password_not_stored_in_plaintext(client, admin_headers):
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == ADMIN[0]))
        assert user.hashed_password != ADMIN[1] and user.hashed_password.startswith("$2")


def test_register_is_admin_only(client, analyst_headers, admin_headers):
    body = {"email": "new.user@test.local", "password": "Another#Pass123", "full_name": "New User"}
    assert client.post(f"{API}/auth/register", json=body).status_code == 401           # anonymous
    forbidden = client.post(f"{API}/auth/register", json=body, headers=analyst_headers)
    assert forbidden.status_code == 403, forbidden.text
    created = client.post(f"{API}/auth/register", json=body, headers=admin_headers)
    assert created.status_code == 201, created.text
    assert client.post(f"{API}/auth/register", json=body, headers=admin_headers).status_code == 409


def test_short_password_rejected(client, admin_headers):
    r = client.post(f"{API}/auth/register", headers=admin_headers,
                    json={"email": "weak@test.local", "password": "short", "full_name": "Weak"})
    assert r.status_code == 422, r.text


def test_logout_and_audit_log_access(client, admin_headers, analyst_headers):
    forbidden = client.get(f"{API}/users/audit-logs", headers=analyst_headers)
    assert forbidden.status_code == 403, forbidden.text
    r = client.get(f"{API}/users/audit-logs", headers=admin_headers)
    assert r.status_code == 200 and r.json()["total"] > 0, r.text
    assert all("password" not in e["description"].lower() for e in r.json()["items"])


def test_logout_revokes_token_but_new_login_works(client):
    first = client.post(f"{API}/auth/login", json={"email": ADMIN[0], "password": ADMIN[1]})
    assert first.status_code == 200
    token = first.json()["access_token"]
    auth = {"Authorization": f"Bearer {token}"}
    assert client.get(f"{API}/auth/me", headers=auth).status_code == 200
    assert client.post(f"{API}/auth/logout", headers=auth).status_code == 200
    assert client.get(f"{API}/auth/me", headers=auth).status_code == 401
    assert client.get(f"{API}/users", headers=auth).status_code == 401

    second = client.post(f"{API}/auth/login", json={"email": ADMIN[0], "password": ADMIN[1]})
    assert second.status_code == 200
    assert second.json()["access_token"] != token
    assert client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {second.json()['access_token']}"}).status_code == 200


def test_expired_invalid_and_tampered_tokens_rejected(client):
    expired = jwt.encode({"sub": "1", "role": "administrator", "jti": uuid.uuid4().hex,
                          "iat": datetime.now(timezone.utc) - timedelta(minutes=3),
                          "exp": datetime.now(timezone.utc) - timedelta(minutes=1)},
                         settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    tampered = create_access_token(1, "administrator")[:-1] + "x"
    for token in (expired, "not-a-jwt", tampered):
        assert client.get(f"{API}/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_expired_revocation_record_is_cleaned_up():
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == ADMIN[0]))
        jti = uuid.uuid4().hex
        db.add(RevokedToken(jti=jti, user_id=user.id,
                            expires_at=datetime.now(timezone.utc) - timedelta(minutes=1)))
        db.commit()
        assert token_is_revoked(db, jti) is False
        assert db.get(RevokedToken, jti) is None


def test_login_rate_limits_account_and_source_without_enumeration(client, monkeypatch):
    from app.api.endpoints import auth as auth_endpoint

    monkeypatch.setattr(settings, "LOGIN_RATE_ACCOUNT_LIMIT", 2)
    monkeypatch.setattr(settings, "LOGIN_RATE_SOURCE_LIMIT", 1000)
    monkeypatch.setattr(settings, "LOGIN_RATE_WINDOW_MINUTES", 15)
    source = f"198.51.100.{uuid.uuid4().int % 200 + 1}"
    monkeypatch.setattr(auth_endpoint, "get_client_ip", lambda _request: source)
    email = f"unknown-{uuid.uuid4().hex}@test.local"
    first = client.post(f"{API}/auth/login", json={"email": email, "password": "wrong"})
    second = client.post(f"{API}/auth/login", json={"email": email, "password": "wrong"})
    limited = client.post(f"{API}/auth/login", json={"email": email, "password": "wrong"})
    assert first.status_code == second.status_code == 401
    assert first.json()["detail"] == second.json()["detail"]
    assert limited.status_code == 429 and limited.headers["retry-after"]

    monkeypatch.setattr(settings, "LOGIN_RATE_ACCOUNT_LIMIT", 1000)
    monkeypatch.setattr(settings, "LOGIN_RATE_SOURCE_LIMIT", 2)
    source = f"203.0.113.{uuid.uuid4().int % 200 + 1}"
    monkeypatch.setattr(auth_endpoint, "get_client_ip", lambda _request: source)
    for index in range(2):
        response = client.post(f"{API}/auth/login", json={"email": f"rotate-{uuid.uuid4().hex}@test.local", "password": "wrong"})
        assert response.status_code == 401
    bypass = client.post(f"{API}/auth/login", json={"email": f"different-{uuid.uuid4().hex}@test.local", "password": "wrong"})
    assert bypass.status_code == 429


def test_security_headers_and_hsts_policy(client, monkeypatch):
    response = client.get(f"{API}/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["referrer-policy"] == "no-referrer"
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert response.headers["cache-control"] == "no-store"
    assert "strict-transport-security" not in response.headers

    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    https_response = client.get(f"https://testserver{API}/health")
    assert https_response.headers["strict-transport-security"].startswith("max-age=")


def test_cors_allows_configured_origin_and_rejects_untrusted_origin(client):
    allowed = client.options(f"{API}/predictions/predict", headers={
        "Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    })
    denied = client.options(f"{API}/predictions/predict", headers={
        "Origin": "https://attacker.invalid", "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization,content-type",
    })
    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert "access-control-allow-origin" not in denied.headers


def test_deactivated_user_cannot_log_in(client, admin_headers):
    email, pw = "temp.user@test.local", "Temporary#Pass1"
    uid = client.post(f"{API}/auth/register", headers=admin_headers,
                      json={"email": email, "password": pw, "full_name": "Temp", "role": "fraud_analyst"}).json()["id"]
    assert client.patch(f"{API}/users/{uid}", headers=admin_headers, json={"is_active": False}).status_code == 200
    assert client.post(f"{API}/auth/login", json={"email": email, "password": pw}).status_code == 401
