import pytest

from app.core.config import Settings


def test_production_requires_exact_https_origins_and_migrations():
    base = {
        "ENVIRONMENT": "production",
        "SECRET_KEY": "production-secret-" + "x" * 40,
        "CORS_ORIGINS": "https://fraud.example.com",
        "AUTO_CREATE_TABLES": False,
    }
    assert Settings(_env_file=None, **base).is_production
    for change in (
        {"CORS_ORIGINS": "*"},
        {"CORS_ORIGINS": "http://fraud.example.com"},
        {"CORS_ORIGINS": "https://localhost:5173"},
        {"AUTO_CREATE_TABLES": True},
        {"SECRET_KEY": "short"},
    ):
        with pytest.raises(ValueError):
            Settings(_env_file=None, **(base | change))
