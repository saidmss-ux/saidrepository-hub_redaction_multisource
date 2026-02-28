import time

import pytest

from backend.services.auth_service import create_access_token, decode_access_token
from backend.services.errors import ServiceError


def test_create_and_decode_token() -> None:
    token = create_access_token(sub="user-1", role="user", ttl_seconds=120)
    ctx = decode_access_token(token)
    assert ctx.user_id == "user-1"
    assert ctx.role == "user"
    assert ctx.tenant_id == "default"


def test_expired_token_rejected() -> None:
    token = create_access_token(sub="user-1", role="user", ttl_seconds=1)
    time.sleep(1.1)
    with pytest.raises(ServiceError) as err:
        decode_access_token(token)
    assert err.value.code == "auth_token_expired"


def test_create_token_with_tenant() -> None:
    token = create_access_token(sub="user-2", role="admin", tenant_id="tenant-42")
    ctx = decode_access_token(token)
    assert ctx.tenant_id == "tenant-42"
