"""
Unit tests for document parsers (PDF, DOCX, TXT).

These tests verify parser behavior with various file types and edge cases.
"""

import os
import tempfile

import pytest

from backend.parsers import DOCXParser, PDFParser, ParserError, ParserFactory, TXTParser


class TestTXTParser:
    """Tests for TXTParser."""

    def test_parse_utf8_text(self):
        """Test parsing a basic UTF-8 text file."""
        parser = TXTParser()
        assert parser.supports("txt")
        assert parser.supports("text")
        assert not parser.supports("pdf")

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write("Hello, World!\nThis is a test.")
            f.flush()
            temp_path = f.name

        try:
            result = parser.parse(temp_path)
            assert result["text"] == "Hello, World!\nThis is a test."
            assert result["metadata"]["encoding"] == "utf-8"
            assert result["metadata"]["file_type"] == "txt"
        finally:
            os.unlink(temp_path)

    def test_parse_latin1_text(self):
        """Test parsing a Latin-1 encoded text file."""
        parser = TXTParser()
        
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".txt", delete=False) as f:
            # Write Latin-1 encoded text with special characters
            f.write("Café\nÑoño".encode("latin-1"))
            f.flush()
            temp_path = f.name

        try:
            result = parser.parse(temp_path)
            # Should successfully decode (might not be perfect if UTF-8 expected, but no error)
            assert result["text"] is not None
            assert result["metadata"]["file_type"] == "txt"
        finally:
            os.unlink(temp_path)

    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        parser = TXTParser()
        with pytest.raises(ParserError, match="File not found"):
            parser.parse("/nonexistent/path/file.txt")

    def test_parse_empty_file(self):
        """Test parsing an empty text file."""
        parser = TXTParser()
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("")
            f.flush()
            temp_path = f.name

        try:
            result = parser.parse(temp_path)
            assert result["text"] == ""
            assert result["metadata"]["file_type"] == "txt"
        finally:
            os.unlink(temp_path)


class TestPDFParser:
    """Tests for PDFParser."""

    def test_supports_pdf(self):
        """Test that PDFParser supports PDF file type."""
        parser = PDFParser()
        assert parser.supports("pdf")
        assert parser.supports("PDF")
        assert not parser.supports("txt")

    def test_parse_nonexistent_file(self):
        """Test parsing a PDF that doesn't exist."""
        parser = PDFParser()
        with pytest.raises(ParserError, match="File not found"):
            parser.parse("/nonexistent/path/file.pdf")

    def test_parse_corrupted_pdf(self):
        """Test parsing a corrupted PDF file."""
        parser = PDFParser()
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pdf", delete=False) as f:
            f.write("This is not a valid PDF")
            f.flush()
            temp_path = f.name

        try:
            with pytest.raises(ParserError):
                parser.parse(temp_path)
        finally:
            os.unlink(temp_path)


class TestDOCXParser:
    """Tests for DOCXParser."""

    def test_supports_docx(self):
        """Test that DOCXParser supports DOCX and DOC file types."""
        parser = DOCXParser()
        assert parser.supports("docx")
        assert parser.supports("doc")
        assert parser.supports("DOCX")
        assert not parser.supports("txt")

    def test_parse_nonexistent_file(self):
        """Test parsing a DOCX that doesn't exist."""
        parser = DOCXParser()
        with pytest.raises(ParserError, match="File not found"):
            parser.parse("/nonexistent/path/file.docx")

    def test_parse_corrupted_docx(self):
        """Test parsing a corrupted DOCX file."""
        parser = DOCXParser()
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".docx", delete=False) as f:
            f.write("This is not a valid DOCX")
            f.flush()
            temp_path = f.name

        try:
            with pytest.raises(ParserError):
                parser.parse(temp_path)
        finally:
            os.unlink(temp_path)


class TestParserFactory:
    """Tests for ParserFactory."""

    def test_get_parser_txt(self):
        """Test getting TXT parser."""
        factory = ParserFactory()
        parser = factory.get_parser("txt")
        assert isinstance(parser, TXTParser)

    def test_get_parser_pdf(self):
        """Test getting PDF parser."""
        factory = ParserFactory()
        parser = factory.get_parser("pdf")
        assert isinstance(parser, PDFParser)

    def test_get_parser_docx(self):
        """Test getting DOCX parser."""
        factory = ParserFactory()
        parser = factory.get_parser("docx")
        assert isinstance(parser, DOCXParser)

    def test_get_parser_unsupported(self):
        """Test getting parser for unsupported file type."""
        factory = ParserFactory()
        parser = factory.get_parser("xyz")
        assert parser is None

    def test_parse_txt(self):
        """Test factory parse method with TXT file."""
        factory = ParserFactory()
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Factory test content")
            f.flush()
            temp_path = f.name

        try:
            result = factory.parse(temp_path, "txt")
            assert result["text"] == "Factory test content"
            assert result["metadata"]["file_type"] == "txt"
        finally:
            os.unlink(temp_path)

    def test_parse_unsupported_type(self):
        """Test factory parse with unsupported file type."""
        factory = ParserFactory()
        
        with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
            f.flush()
            temp_path = f.name

        try:
            with pytest.raises(ParserError, match="Unsupported file type"):
                factory.parse(temp_path, "xyz")
        finally:
            os.unlink(temp_path)

    def test_parse_with_dot_prefix(self):
        """Test factory parse with file type that has a dot prefix."""
        factory = ParserFactory()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("Dot test content")
            f.flush()
            temp_path = f.name

        try:
            result = factory.parse(temp_path, ".txt")
            assert result["text"] == "Dot test content"
        finally:
            os.unlink(temp_path)


class TestVideoParser:
    """Tests for VideoParser."""

    def test_supports_video_formats(self):
        """Test that VideoParser recognizes video formats."""
        from backend.parsers import VideoParser
        parser = VideoParser()
        assert parser.supports("mp4")
        assert parser.supports("mp3")
        assert parser.supports("webm")
        assert parser.supports("wav")
        assert not parser.supports("txt")

    def test_parse_nonexistent_video(self):
        """Test parsing a video that doesn't exist."""
        from backend.parsers import VideoParser
        parser = VideoParser()
        with pytest.raises(ParserError, match="File not found"):
            parser.parse("/nonexistent/path/video.mp4")


class TestContentDeduplication:
    """Tests for content deduplication functionality."""

    def test_hash_content(self):
        """Test content hashing."""
        from backend.db import hash_content

        content1 = "Hello, World!"
        content2 = "Hello, World!"
        content3 = "Different content"

        hash1 = hash_content(content1)
        hash2 = hash_content(content2)
        hash3 = hash_content(content3)

        # Same content should have same hash
        assert hash1 == hash2
        # Different content should have different hash
        assert hash1 != hash3

        # Hash should be 64 characters (SHA-256)
        assert len(hash1) == 64

    def test_check_duplicate(self):
        """Test duplicate detection."""
        from backend.db import hash_content, check_duplicate, Source, Base, engine

        # Setup test database
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        from backend.db import SessionLocal
        db = SessionLocal()

        try:
            content = "Duplicate test content"
            content_hash = hash_content(content)

            # No duplicate should exist initially
            existing = check_duplicate(db, content_hash)
            assert existing is None

            # Create a source
            source = Source(
                file_id="test-id-1",
                file_name="test.txt",
                file_type="txt",
                full_content=content,
                content_hash=content_hash,
            )
            db.add(source)
            db.commit()

            # Now duplicate should be found
            existing = check_duplicate(db, content_hash)
            assert existing is not None
            assert existing.file_id == "test-id-1"
        finally:
            db.close()
            Base.metadata.drop_all(bind=engine)
