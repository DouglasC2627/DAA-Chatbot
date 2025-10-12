"""
Tests for file storage system.

This test suite tests:
- File validation
- File upload and storage
- File retrieval
- File deletion
- Cleanup utilities
"""

import pytest
import io
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from utils.file_validation import (
    validate_file_upload,
    validate_file_size,
    get_document_type,
    sanitize_filename,
    is_supported_file_type,
    get_supported_extensions,
    FileValidationError
)
from services.file_storage import FileStorageService, FileStorageError
from models.document import DocumentType


class TestFileValidation:
    """Test file validation utilities."""

    def test_valid_pdf_file(self):
        """Test validating a valid PDF file."""
        filename, doc_type, mime_type = validate_file_upload(
            "test_document.pdf",
            1024 * 1024,  # 1MB
            "application/pdf"
        )

        assert filename == "test_document.pdf"
        assert doc_type == DocumentType.PDF
        assert mime_type == "application/pdf"

    def test_file_too_large(self):
        """Test rejecting oversized file."""
        with pytest.raises(FileValidationError):
            validate_file_size(15 * 1024 * 1024)  # 15MB (over limit)

    def test_unsupported_file_type(self):
        """Test rejecting unsupported file type."""
        with pytest.raises(FileValidationError):
            get_document_type("test.exe")

    def test_dangerous_filename(self):
        """Test rejecting dangerous filename."""
        with pytest.raises(FileValidationError):
            sanitize_filename("../../../etc/passwd")

    def test_supported_extensions(self):
        """Test listing supported file types."""
        extensions = get_supported_extensions()

        assert isinstance(extensions, list)
        assert len(extensions) > 0
        assert '.pdf' in extensions
        assert '.txt' in extensions

    @pytest.mark.parametrize("filename,expected_type", [
        ("document.pdf", DocumentType.PDF),
        ("spreadsheet.xlsx", DocumentType.XLSX),
        ("notes.txt", DocumentType.TXT),
        ("readme.md", DocumentType.MD),
        ("data.csv", DocumentType.CSV),
        ("report.docx", DocumentType.DOCX)
    ])
    def test_document_type_detection(self, filename, expected_type):
        """Test document type detection for various file types."""
        doc_type = get_document_type(filename)
        assert doc_type == expected_type


class TestFileStorage:
    """Test file storage service."""

    @pytest.fixture
    def storage(self):
        """Create file storage service instance."""
        return FileStorageService()

    @pytest.fixture
    def test_project_id(self):
        """Test project ID."""
        return 999

    @pytest.fixture(autouse=True)
    def cleanup(self, storage, test_project_id):
        """Cleanup test files after each test."""
        yield
        # Cleanup test files
        try:
            storage.cleanup_project_files(test_project_id)
        except:
            pass

    def test_save_file(self, storage, test_project_id):
        """Test saving a file."""
        test_content = b"This is a test PDF document content."
        file_stream = io.BytesIO(test_content)

        relative_path, unique_filename = storage.save_file(
            file_stream,
            "test_document.pdf",
            test_project_id
        )

        assert relative_path is not None
        assert unique_filename is not None
        assert storage.file_exists(relative_path)

    def test_file_exists(self, storage, test_project_id):
        """Test checking if file exists."""
        test_content = b"Test content"
        file_stream = io.BytesIO(test_content)

        relative_path, _ = storage.save_file(
            file_stream,
            "test.txt",
            test_project_id
        )

        assert storage.file_exists(relative_path) is True
        assert storage.file_exists("nonexistent/file.txt") is False

    def test_get_file_size(self, storage, test_project_id):
        """Test getting file size."""
        test_content = b"Test content with known length"
        file_stream = io.BytesIO(test_content)

        relative_path, _ = storage.save_file(
            file_stream,
            "test.txt",
            test_project_id
        )

        file_size = storage.get_file_size(relative_path)
        assert file_size == len(test_content)

    def test_read_file(self, storage, test_project_id):
        """Test reading file content."""
        test_content = b"This is test content"
        file_stream = io.BytesIO(test_content)

        relative_path, _ = storage.save_file(
            file_stream,
            "test.txt",
            test_project_id
        )

        content = storage.read_file(relative_path)
        assert content == test_content

    def test_list_project_files(self, storage, test_project_id):
        """Test listing project files."""
        # Create multiple test files
        for i in range(3):
            content = f"Test file {i} content".encode()
            file_stream = io.BytesIO(content)
            storage.save_file(
                file_stream,
                f"test_file_{i}.txt",
                test_project_id
            )

        files = storage.list_project_files(test_project_id)
        assert len(files) == 3

    def test_get_storage_stats(self, storage, test_project_id):
        """Test getting storage statistics."""
        # Create test files
        for i in range(2):
            content = f"Test content {i}".encode()
            file_stream = io.BytesIO(content)
            storage.save_file(
                file_stream,
                f"file_{i}.txt",
                test_project_id
            )

        stats = storage.get_storage_stats(test_project_id)

        assert 'total_files' in stats
        assert 'total_size_mb' in stats
        assert stats['total_files'] == 2
        assert stats['total_size_mb'] > 0

    def test_delete_file(self, storage, test_project_id):
        """Test deleting specific file."""
        test_content = b"Test content"
        file_stream = io.BytesIO(test_content)

        relative_path, _ = storage.save_file(
            file_stream,
            "test.txt",
            test_project_id
        )

        assert storage.file_exists(relative_path) is True

        success = storage.delete_file(relative_path)
        assert success is True
        assert storage.file_exists(relative_path) is False

    def test_cleanup_orphaned_files(self, storage, test_project_id):
        """Test cleaning up orphaned files."""
        file_paths = []
        for i in range(3):
            content = f"Test file {i}".encode()
            file_stream = io.BytesIO(content)
            path, _ = storage.save_file(
                file_stream,
                f"test_{i}.txt",
                test_project_id
            )
            file_paths.append(path)

        # Keep only the first file
        valid_paths = [file_paths[0]]
        deleted = storage.cleanup_orphaned_files(test_project_id, valid_paths)

        assert deleted == 2
        assert storage.file_exists(file_paths[0]) is True
        assert storage.file_exists(file_paths[1]) is False

    def test_cleanup_all_project_files(self, storage, test_project_id):
        """Test cleaning up all project files."""
        # Create test files
        for i in range(3):
            content = f"Test {i}".encode()
            file_stream = io.BytesIO(content)
            storage.save_file(
                file_stream,
                f"test_{i}.txt",
                test_project_id
            )

        deleted_count = storage.cleanup_project_files(test_project_id)
        assert deleted_count == 3

        # Verify all files are gone
        remaining_files = storage.list_project_files(test_project_id)
        assert len(remaining_files) == 0


class TestIntegration:
    """Test integration of validation and storage."""

    @pytest.fixture
    def storage(self):
        """Create file storage service instance."""
        return FileStorageService()

    @pytest.fixture
    def test_project_id(self):
        """Test project ID for integration tests."""
        return 998

    @pytest.fixture(autouse=True)
    def cleanup(self, storage, test_project_id):
        """Cleanup test files."""
        yield
        try:
            storage.cleanup_project_files(test_project_id)
        except:
            pass

    def test_complete_upload_workflow(self, storage, test_project_id):
        """Test complete file upload workflow."""
        # Step 1: Create test file
        filename = "integration_test.pdf"
        content = b"%PDF-1.4 Test PDF content"
        file_size = len(content)

        # Step 2: Validate file
        safe_filename, doc_type, mime_type = validate_file_upload(
            filename,
            file_size,
            "application/pdf",
            content
        )

        assert doc_type == DocumentType.PDF

        # Step 3: Store file
        file_stream = io.BytesIO(content)
        relative_path, unique_filename = storage.save_file(
            file_stream,
            safe_filename,
            test_project_id
        )

        assert relative_path is not None

        # Step 4: Verify stored file
        stored_content = storage.read_file(relative_path)
        assert stored_content == content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
