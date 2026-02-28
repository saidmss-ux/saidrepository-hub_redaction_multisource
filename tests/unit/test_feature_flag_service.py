import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.migrations import bootstrap_schema
from backend.services.errors import ServiceError
from backend.services.feature_flag_service import get_effective_flag, set_feature_flag


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


def test_set_and_resolve_tenant_flag(db_session):
    created = set_feature_flag(
        db_session,
        key="batch.async.enabled",
        enabled=True,
        scope="tenant",
        scope_id="tenant-a",
        actor_id="admin-1",
        actor_tenant_id="tenant-a",
    )
    assert created["enabled"] is True
    assert get_effective_flag(db_session, key="batch.async.enabled", tenant_id="tenant-a") is True


def test_invalid_scope_rejected(db_session):
    with pytest.raises(ServiceError) as err:
        set_feature_flag(
            db_session,
            key="x",
            enabled=True,
            scope="user",
            scope_id="u1",
            actor_id="admin-1",
            actor_tenant_id="tenant-a",
        )
    assert err.value.code == "feature_flag_scope_invalid"
