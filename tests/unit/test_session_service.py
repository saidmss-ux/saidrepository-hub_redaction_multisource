import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.migrations import bootstrap_schema
from backend.services.errors import ServiceError
from backend.services.session_service import issue_token_pair, refresh_token_pair, revoke_user_sessions


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    bootstrap_schema(engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_issue_and_refresh_token_pair(db_session, monkeypatch):
    monkeypatch.setattr("backend.services.session_service.settings.refresh_rotation_enabled", True)
    pair = issue_token_pair(db_session, user_id="u1", role="admin", tenant_id="t1")
    refreshed = refresh_token_pair(db_session, refresh_token=pair["refresh_token"])

    assert refreshed["token_type"] == "bearer"
    assert refreshed["tenant_id"] == "t1"
    assert refreshed["refresh_token"] != pair["refresh_token"]


def test_reuse_revoked_token_rejected(db_session, monkeypatch):
    monkeypatch.setattr("backend.services.session_service.settings.refresh_rotation_enabled", True)
    monkeypatch.setattr("backend.services.session_service.settings.refresh_reuse_detection", True)

    pair = issue_token_pair(db_session, user_id="u2", role="user", tenant_id="t2")
    refresh_token_pair(db_session, refresh_token=pair["refresh_token"])

    with pytest.raises(ServiceError) as err:
        refresh_token_pair(db_session, refresh_token=pair["refresh_token"])
    assert err.value.code == "auth_refresh_revoked"


def test_revoke_user_sessions(db_session):
    issue_token_pair(db_session, user_id="u3", role="user", tenant_id="t3")
    result = revoke_user_sessions(db_session, tenant_id="t3", user_id="u3")
    assert result["revoked"] >= 1
