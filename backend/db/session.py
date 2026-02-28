from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from backend.core.config import settings


class Base(DeclarativeBase):
    pass


engine_kwargs = {"future": True}
if settings.database_url.startswith("postgresql"):
    engine_kwargs.update({"pool_pre_ping": True})

engine = create_engine(settings.database_url, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
