"""
Test script for document processor service.

This script tests the document processing functionality for various file formats.
"""
import io
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from services.document_processor import (
    DocumentProcessor,
    DocumentProcessorResult,
    DocumentProcessingError,
    UnsupportedDocumentTypeError,
    document_processor
)
from models.document import DocumentType


def test_supported_extensions():
    """Test document type detection from filenames."""
    print("\n=== Testing Document Type Detection ===")

    test_cases = [
        ("document.pdf", DocumentType.PDF, True),
        ("document.docx", DocumentType.DOCX, True),
        ("document.txt", DocumentType.TXT, True),
        ("document.md", DocumentType.MD, True),
        ("document.csv", DocumentType.CSV, True),
        ("document.xlsx", DocumentType.XLSX, True),
        ("document.unknown", None, False),
    ]

    for filename, expected_type, should_succeed in test_cases:
        try:
            doc_type = DocumentProcessor.get_document_type(filename)
            is_supported = DocumentProcessor.is_supported(filename)

            status = "✓" if (doc_type == expected_type and is_supported == should_succeed) else "✗"
            print(f"{status} {filename}: {doc_type.value if doc_type else 'unsupported'}")

        except UnsupportedDocumentTypeError:
            status = "✓" if not should_succeed else "✗"
            print(f"{status} {filename}: correctly rejected")


def test_mime_type_detection():
    """Test MIME type detection."""
    print("\n=== Testing MIME Type Detection ===")

    test_cases = [
        ("document.pdf", "application/pdf"),
        ("document.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        ("document.txt", "text/plain"),
        ("document.csv", "text/csv"),
    ]

    for filename, expected_mime in test_cases:
        mime_type = DocumentProcessor.get_mime_type(filename)
        status = "✓" if mime_type == expected_mime else "✗"
        print(f"{status} {filename}: {mime_type}")


def test_text_processing():
    """Test plain text document processing."""
    print("\n=== Testing Text File Processing ===")

    # Create sample text file
    text_content = """This is a test document.
It contains multiple lines of text.
This is used to test the document processor.

The processor should extract all this text correctly."""

    file_content = io.BytesIO(text_content.encode('utf-8'))

    try:
        result = document_processor.process_document(
            file_content,
            "test.txt"
        )

        print(f"✓ Text processing successful")
        print(f"  - Extracted {len(result.text)} characters")
        print(f"  - Word count: {result.word_count}")
        print(f"  - Metadata: {result.metadata}")

        # Verify text extraction
        if result.text.strip() == text_content.strip():
            print(f"✓ Text content matches original")
        else:
            print(f"✗ Text content mismatch")

    except Exception as e:
        print(f"✗ Text processing failed: {str(e)}")


def test_markdown_processing():
    """Test markdown document processing."""
    print("\n=== Testing Markdown File Processing ===")

    # Create sample markdown file
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

    try:
        result = document_processor.process_document(
            file_content,
            "test.md"
        )

        print(f"✓ Markdown processing successful")
        print(f"  - Extracted {len(result.text)} characters")
        print(f"  - Word count: {result.word_count}")
        print(f"  - Metadata type: {result.metadata.get('type')}")

    except Exception as e:
        print(f"✗ Markdown processing failed: {str(e)}")


def test_csv_processing():
    """Test CSV document processing."""
    print("\n=== Testing CSV File Processing ===")

    # Create sample CSV file
    csv_content = """Name,Age,City,Country
John Doe,30,New York,USA
Jane Smith,25,London,UK
Bob Johnson,35,Toronto,Canada
Alice Williams,28,Sydney,Australia"""

    file_content = io.BytesIO(csv_content.encode('utf-8'))

    try:
        result = document_processor.process_document(
            file_content,
            "test.csv"
        )

        print(f"✓ CSV processing successful")
        print(f"  - Extracted {len(result.text)} characters")
        print(f"  - Word count: {result.word_count}")
        print(f"  - Metadata:")
        print(f"    - Rows: {result.metadata.get('row_count')}")
        print(f"    - Columns: {result.metadata.get('column_count')}")
        print(f"    - Column names: {result.metadata.get('columns')}")

        # Verify column detection
        expected_columns = ['Name', 'Age', 'City', 'Country']
        if result.metadata.get('columns') == expected_columns:
            print(f"✓ Columns detected correctly")
        else:
            print(f"✗ Column detection failed")

    except Exception as e:
        print(f"✗ CSV processing failed: {str(e)}")


def test_file_size_validation():
    """Test file size validation."""
    print("\n=== Testing File Size Validation ===")

    test_cases = [
        (1024, 2048, True),           # 1KB < 2KB
        (2048, 2048, True),           # 2KB = 2KB
        (3072, 2048, False),          # 3KB > 2KB
        (10485760, 10485760, True),   # 10MB = 10MB (exact limit)
        (10485761, 10485760, False),  # 10MB + 1 byte > 10MB
    ]

    for file_size, max_size, should_pass in test_cases:
        result = document_processor.validate_file_size(file_size, max_size)
        status = "✓" if result == should_pass else "✗"

        file_size_mb = file_size / (1024 * 1024)
        max_size_mb = max_size / (1024 * 1024)

        print(f"{status} {file_size_mb:.2f}MB vs {max_size_mb:.2f}MB: {'Valid' if result else 'Invalid'}")


def test_text_preview():
    """Test text preview extraction."""
    print("\n=== Testing Text Preview Extraction ===")

    # Short text
    short_text = "This is a short text."
    preview = document_processor.extract_text_preview(short_text, 100)

    if preview == short_text:
        print(f"✓ Short text preview: '{preview}'")
    else:
        print(f"✗ Short text preview failed")

    # Long text
    long_text = "This is a very long text. " * 50
    preview = document_processor.extract_text_preview(long_text, 100)

    if len(preview) <= 103 and preview.endswith("..."):  # 100 + "..."
        print(f"✓ Long text preview: '{preview[:50]}...' (length: {len(preview)})")
    else:
        print(f"✗ Long text preview failed")


def test_error_handling():
    """Test error handling for invalid files."""
    print("\n=== Testing Error Handling ===")

    # Test unsupported file type
    try:
        DocumentProcessor.get_document_type("document.xyz")
        print(f"✗ Should have raised UnsupportedDocumentTypeError")
    except UnsupportedDocumentTypeError:
        print(f"✓ Correctly rejected unsupported file type")

    # Test empty file
    try:
        empty_content = io.BytesIO(b"")
        result = document_processor.process_document(empty_content, "empty.txt")
        print(f"✗ Should have raised DocumentProcessingError for empty file")
    except DocumentProcessingError as e:
        print(f"✓ Correctly handled empty file: {str(e)}")

    # Test corrupted file
    try:
        corrupted_content = io.BytesIO(b"Not a valid PDF file")
        result = document_processor.process_document(
            corrupted_content,
            "corrupted.pdf",
            DocumentType.PDF
        )
        print(f"✗ Should have raised DocumentProcessingError for corrupted file")
    except DocumentProcessingError as e:
        print(f"✓ Correctly handled corrupted file: {str(e)}")


def run_all_tests():
    """Run all document processor tests."""
    print("=" * 60)
    print("DOCUMENT PROCESSOR TEST SUITE")
    print("=" * 60)

    try:
        test_supported_extensions()
        test_mime_type_detection()
        test_text_processing()
        test_markdown_processing()
        test_csv_processing()
        test_file_size_validation()
        test_text_preview()
        test_error_handling()

        print("\n" + "=" * 60)
        print("TEST SUITE COMPLETED")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Test suite failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
