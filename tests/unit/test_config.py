import pytest

from backend.core.config import Settings


def test_settings_from_env_success() -> None:
    config = Settings.from_env({"API_PREFIX": "/api/v1", "CONCURRENCY_LIMIT": "5"})
    assert config.api_prefix == "/api/v1"
    assert config.concurrency_limit == 5


def test_settings_invalid_prefix() -> None:
    with pytest.raises(ValueError):
        Settings.from_env({"API_PREFIX": "/v1"})


def test_settings_invalid_int_value() -> None:
    with pytest.raises(ValueError):
        Settings.from_env({"URL_DOWNLOAD_TIMEOUT_S": "zero"})
