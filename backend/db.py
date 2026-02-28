"""
Database models and session management for DocuHub.

Uses SQLAlchemy ORM with SQLite backend for MVP persistence.
"""

import hashlib
import os
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

# Database file path (SQLite)
DATABASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_PATH = os.path.join(DATABASE_DIR, "docuhub.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite-specific for concurrent access
    echo=False,  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for ORM models
Base = declarative_base()


def get_db():
    """Dependency injection for database sessions in FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class Source(Base):
    """Represents an uploaded or downloaded source document."""

    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(String(36), unique=True, index=True, nullable=False)  # UUID string
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=False)  # e.g., 'pdf', 'docx', 'txt'
    file_size = Column(Integer, nullable=True)  # Size in bytes
    upload_timestamp = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True)
    content_preview = Column(Text, nullable=True)  # First 1000 chars for quick display
    full_content = Column(Text, nullable=True)  # Full content for text-based sources
    content_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash for deduplication
    is_url_source = Column(Integer, default=0, nullable=False)  # Boolean stored as int

    # Relationships
    extractions = relationship("Extraction", back_populates="source", cascade="all, delete-orphan")
    projects = relationship("Project", secondary="project_sources", back_populates="sources")


class Extraction(Base):
    """Represents a text extraction from a source."""

    __tablename__ = "extractions"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    mode = Column(String(20), nullable=False)  # e.g., 'text', 'summary'
    extracted_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True)

    # Relationships
    source = relationship("Source", back_populates="extractions")


class Project(Base):
    """Represents a project/collection of sources."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False, index=True)

    # Relationships
    sources = relationship("Source", secondary="project_sources", back_populates="projects")


class ProjectSource(Base):
    """Join table for project-source many-to-many relationship."""

    __tablename__ = "project_sources"

    project_id = Column(Integer, ForeignKey("projects.id"), primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"), primary_key=True)


def init_db():
    """Initialize the database schema. Call this on app startup."""
    Base.metadata.create_all(bind=engine)


def hash_content(content: str) -> str:
    """Generate SHA-256 hash of content for deduplication."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def check_duplicate(db: sessionmaker, content_hash: str) -> Optional[Source]:
    """
    Check if content with this hash already exists.

    Args:
        db: Database session
        content_hash: SHA-256 hash of content

    Returns:
        Existing Source if found, None otherwise
    """
    return db.query(Source).filter(Source.content_hash == content_hash).first()
