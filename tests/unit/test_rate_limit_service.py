import pytest

from backend.services.errors import ServiceError
from backend.services.rate_limit_service import _rate_windows, check_rate_limit


def test_rate_limit_blocks_when_threshold_reached(monkeypatch):
    monkeypatch.setattr("backend.services.rate_limit_service.settings.rate_limit_requests", 1)
    monkeypatch.setattr("backend.services.rate_limit_service.settings.rate_limit_window_s", 60)
    _rate_windows.clear()

    check_rate_limit("k1")
    with pytest.raises(ServiceError) as err:
        check_rate_limit("k1")
    assert err.value.code == "rate_limited"
