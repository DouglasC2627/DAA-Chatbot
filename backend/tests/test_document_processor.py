"""
Tests for document processor service.

This test suite tests the document processing functionality for various file formats.
"""

import pytest
import io
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.document_processor import (
    DocumentProcessor,
    DocumentProcessorResult,
    DocumentProcessingError,
    UnsupportedDocumentTypeError,
    document_processor
)
from models.document import DocumentType


class TestDocumentTypeDetection:
    """Test document type detection from filenames."""

    @pytest.mark.parametrize("filename,expected_type,should_succeed", [
        ("document.pdf", DocumentType.PDF, True),
        ("document.docx", DocumentType.DOCX, True),
        ("document.txt", DocumentType.TXT, True),
        ("document.md", DocumentType.MD, True),
        ("document.csv", DocumentType.CSV, True),
        ("document.xlsx", DocumentType.XLSX, True),
        ("document.unknown", None, False),
    ])
    def test_get_document_type(self, filename, expected_type, should_succeed):
        """Test document type detection for various file types."""
        if should_succeed:
            doc_type = DocumentProcessor.get_document_type(filename)
            is_supported = DocumentProcessor.is_supported(filename)
            assert doc_type == expected_type
            assert is_supported is True
        else:
            with pytest.raises(UnsupportedDocumentTypeError):
                DocumentProcessor.get_document_type(filename)


class TestMimeTypeDetection:
    """Test MIME type detection."""

    @pytest.mark.parametrize("filename,expected_mime", [
        ("document.pdf", "application/pdf"),
        ("document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("document.txt", "text/plain"),
        ("document.csv", "text/csv"),
    ])
    def test_get_mime_type(self, filename, expected_mime):
        """Test MIME type detection for various file types."""
        mime_type = DocumentProcessor.get_mime_type(filename)
        assert mime_type == expected_mime


class TestTextProcessing:
    """Test plain text document processing."""

    def test_process_text_file(self):
        """Test processing a plain text file."""
        text_content = """This is a test document.
It contains multiple lines of text.
This is used to test the document processor.

The processor should extract all this text correctly."""

        file_content = io.BytesIO(text_content.encode('utf-8'))

        result = document_processor.process_document(
            file_content,
            "test.txt"
        )

        assert result.text.strip() == text_content.strip()
        assert result.word_count > 0
        assert result.metadata is not None

    def test_process_markdown_file(self):
        """Test processing a markdown file."""
        markdown_content = """# Test Document

This is a **markdown** document with _formatting_.

## Section 1
- Item 1
- Item 2
- Item 3

## Section 2
```python
def hello():
    print("Hello, World!")
```
"""

        file_content = io.BytesIO(markdown_content.encode('utf-8'))

        result = document_processor.process_document(
            file_content,
            "test.md"
        )

        assert len(result.text) > 0
        assert result.word_count > 0
        assert result.metadata.get('type') == 'markdown'


class TestCSVProcessing:
    """Test CSV document processing."""

    def test_process_csv_file(self):
        """Test processing a CSV file."""
        csv_content = """Name,Age,City,Country
John Doe,30,New York,USA
Jane Smith,25,London,UK
Bob Johnson,35,Toronto,Canada
Alice Williams,28,Sydney,Australia"""

        file_content = io.BytesIO(csv_content.encode('utf-8'))

        result = document_processor.process_document(
            file_content,
            "test.csv"
        )

        assert len(result.text) > 0
        assert result.word_count > 0
        assert result.metadata.get('row_count') == 5  # Including header
        assert result.metadata.get('column_count') == 4
        assert result.metadata.get('columns') == ['Name', 'Age', 'City', 'Country']


class TestFileSizeValidation:
    """Test file size validation."""

    @pytest.mark.parametrize("file_size,max_size,should_pass", [
        (1024, 2048, True),           # 1KB < 2KB
        (2048, 2048, True),           # 2KB = 2KB
        (3072, 2048, False),          # 3KB > 2KB
        (10485760, 10485760, True),   # 10MB = 10MB (exact limit)
        (10485761, 10485760, False),  # 10MB + 1 byte > 10MB
    ])
    def test_validate_file_size(self, file_size, max_size, should_pass):
        """Test file size validation with various sizes."""
        result = document_processor.validate_file_size(file_size, max_size)
        assert result == should_pass


class TestTextPreview:
    """Test text preview extraction."""

    def test_short_text_preview(self):
        """Test preview extraction for short text."""
        short_text = "This is a short text."
        preview = document_processor.extract_text_preview(short_text, 100)

        assert preview == short_text

    def test_long_text_preview(self):
        """Test preview extraction for long text."""
        long_text = "This is a very long text. " * 50
        preview = document_processor.extract_text_preview(long_text, 100)

        assert len(preview) <= 103  # 100 + "..."
        assert preview.endswith("...")


class TestErrorHandling:
    """Test error handling for invalid files."""

    def test_unsupported_file_type(self):
        """Test handling of unsupported file type."""
        with pytest.raises(UnsupportedDocumentTypeError):
            DocumentProcessor.get_document_type("document.xyz")

    def test_empty_file(self):
        """Test handling of empty file."""
        empty_content = io.BytesIO(b"")

        with pytest.raises(DocumentProcessingError):
            document_processor.process_document(empty_content, "empty.txt")

    def test_corrupted_pdf(self):
        """Test handling of corrupted PDF file."""
        corrupted_content = io.BytesIO(b"Not a valid PDF file")

        with pytest.raises(DocumentProcessingError):
            document_processor.process_document(
                corrupted_content,
                "corrupted.pdf",
                DocumentType.PDF
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
