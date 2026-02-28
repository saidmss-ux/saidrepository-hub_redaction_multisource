"""
Database migration and initialization for DocuHub MVP.

For MVP, we use simple schema creation. In production, consider Alembic for version control.
"""

import logging

from backend.db import Base, engine, init_db

logger = logging.getLogger(__name__)


def setup_database():
    """Initialize the database schema on app startup."""
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as exc:
        logger.error(f"Failed to initialize database: {exc}")
        raise


if __name__ == "__main__":
    setup_database()
    print("Database setup complete.")
