"""
Shared pytest fixtures and configuration.

Provides reusable test database and sample file fixtures.
"""

import os
import tempfile

import pytest

from backend.db import Base, engine


@pytest.fixture(scope="function")
def test_db():
    """Create a fresh test database for each test."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def temp_txt_file():
    """Create a temporary text file with sample content."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write("Sample text file content.\nLine 2 of the file.")
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_empty_txt_file():
    """Create a temporary empty text file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_multiline_txt_file():
    """Create a temporary text file with multiple lines."""
    content = "\n".join([f"Line {i}" for i in range(1, 101)])
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as f:
        f.write(content)
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_corrupted_pdf():
    """Create a temporary file with invalid PDF content."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".pdf", delete=False) as f:
        f.write("This is not a valid PDF file")
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_corrupted_docx():
    """Create a temporary file with invalid DOCX content."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".docx", delete=False) as f:
        f.write("This is not a valid DOCX file")
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)
