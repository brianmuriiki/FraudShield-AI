import os
import tempfile
from pathlib import Path

# Configure BEFORE the app is imported.
_tmp = tempfile.mkdtemp(prefix="fraudshield_tests_")
os.environ["DATABASE_URL"] = f"sqlite:///{Path(_tmp) / 'test.db'}"
os.environ["SECRET_KEY"] = "test-secret-key-not-for-production-0123456789abcdef"
os.environ["ENVIRONMENT"] = "testing"
os.environ["INITIAL_ADMIN_EMAIL"] = "admin@test.local"
os.environ["INITIAL_ADMIN_PASSWORD"] = "Admin#Pass12345"
os.environ["ALLOW_PUBLIC_REGISTRATION"] = "false"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

API = "/api/v1"
ADMIN = ("admin@test.local", "Admin#Pass12345")


@pytest.fixture(scope="session")
def client():
    # The host's default asyncio selector loop does not wake reliably for callbacks
    # scheduled from TestClient's AnyIO worker thread; uvloop handles the portal correctly.
    with TestClient(app, backend_options={"use_uvloop": True}) as c:
        yield c


def _login(client, email, password):
    r = client.post(f"{API}/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


@pytest.fixture(scope="session")
def admin_headers(client):
    return _login(client, *ADMIN)


def _make_user(client, admin_headers, role):
    email, pw = f"{role}@test.local", "Analyst#Pass123"
    r = client.post(f"{API}/auth/register", headers=admin_headers,
                    json={"email": email, "password": pw, "full_name": role.replace("_", " ").title(), "role": role})
    assert r.status_code in (201, 409), r.text
    return _login(client, email, pw)


@pytest.fixture(scope="session")
def senior_headers(client, admin_headers):
    return _make_user(client, admin_headers, "senior_analyst")


@pytest.fixture(scope="session")
def analyst_headers(client, admin_headers):
    return _make_user(client, admin_headers, "fraud_analyst")


@pytest.fixture(scope="session")
def bi_headers(client, admin_headers):
    return _make_user(client, admin_headers, "bi_analyst")
