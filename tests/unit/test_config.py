import pytest

from backend.core.config import Settings


def test_settings_from_env_success_local() -> None:
    config = Settings.from_env(
        {
            "APP_ENV": "local",
            "API_PREFIX": "/api/v1",
            "DATABASE_URL": "sqlite:///./test.db",
            "CONCURRENCY_LIMIT": "5",
            "DEBUG": "true",
        }
    )
    assert config.api_prefix == "/api/v1"
    assert config.concurrency_limit == 5


def test_settings_invalid_prefix() -> None:
    with pytest.raises(ValueError):
        Settings.from_env({"APP_ENV": "local", "API_PREFIX": "/v1", "DATABASE_URL": "sqlite:///./test.db"})


def test_settings_invalid_int_value() -> None:
    with pytest.raises(ValueError):
        Settings.from_env({"APP_ENV": "local", "DATABASE_URL": "sqlite:///./test.db", "URL_DOWNLOAD_TIMEOUT_S": "zero"})


def test_settings_staging_requires_postgres() -> None:
    with pytest.raises(ValueError):
        Settings.from_env({"APP_ENV": "staging", "DATABASE_URL": "sqlite:///./test.db", "DEBUG": "false"})


def test_settings_production_requires_debug_false() -> None:
    with pytest.raises(ValueError):
        Settings.from_env(
            {
                "APP_ENV": "production",
                "DATABASE_URL": "postgresql://x:y@z:5432/db",
                "DEBUG": "true",
            }
        )


def test_settings_production_requires_custom_jwt_secret() -> None:
    with pytest.raises(ValueError):
        Settings.from_env(
            {
                "APP_ENV": "production",
                "DATABASE_URL": "postgresql://x:y@z:5432/db",
                "DEBUG": "false",
                "JWT_SECRET": "change-me-local-secret",
            }
        )
