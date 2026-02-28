from backend.db.session import Base


def bootstrap_schema(engine) -> None:
    # Local bootstrap safety for developer environments.
    # Formal schema evolution is governed by Alembic migrations.
    Base.metadata.create_all(bind=engine)
