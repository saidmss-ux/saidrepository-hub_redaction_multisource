from sqlalchemy import text

from backend.db.session import Base


def bootstrap_schema(engine) -> None:
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version TEXT PRIMARY KEY,
                    applied_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT OR IGNORE INTO schema_migrations(version)
                VALUES ('2026_product_layer_v1')
                """
            )
        )
