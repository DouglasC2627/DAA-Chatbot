"""
Test script for file storage system.

This script tests:
- File validation
- File upload and storage
- File retrieval
- File deletion
- Cleanup utilities
"""
import io
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

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


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}\n")


def test_file_validation():
    """Test file validation utilities."""
    print_section("Testing File Validation")

    # Test 1: Valid file
    print("Test 1: Validating a valid PDF file...")
    try:
        filename, doc_type, mime_type = validate_file_upload(
            "test_document.pdf",
            1024 * 1024,  # 1MB
            "application/pdf"
        )
        print(f"✓ Valid file accepted")
        print(f"  - Sanitized filename: {filename}")
        print(f"  - Document type: {doc_type.value}")
        print(f"  - MIME type: {mime_type}")
    except FileValidationError as e:
        print(f"✗ Validation failed: {e}")

    # Test 2: File too large
    print("\nTest 2: Validating oversized file...")
    try:
        validate_file_size(15 * 1024 * 1024)  # 15MB (over limit)
        print("✗ Should have rejected oversized file")
    except FileValidationError as e:
        print(f"✓ Correctly rejected: {e}")

    # Test 3: Unsupported file type
    print("\nTest 3: Validating unsupported file type...")
    try:
        get_document_type("test.exe")
        print("✗ Should have rejected unsupported type")
    except FileValidationError as e:
        print(f"✓ Correctly rejected: {e}")

    # Test 4: Dangerous filename
    print("\nTest 4: Validating dangerous filename...")
    try:
        sanitize_filename("../../../etc/passwd")
        print("✗ Should have rejected dangerous filename")
    except FileValidationError as e:
        print(f"✓ Correctly rejected: {e}")

    # Test 5: Check supported types
    print("\nTest 5: Listing supported file types...")
    extensions = get_supported_extensions()
    print(f"✓ Supported extensions: {', '.join(extensions)}")

    # Test 6: Various file types
    print("\nTest 6: Testing different file types...")
    test_files = [
        ("document.pdf", DocumentType.PDF),
        ("spreadsheet.xlsx", DocumentType.XLSX),
        ("notes.txt", DocumentType.TXT),
        ("readme.md", DocumentType.MD),
        ("data.csv", DocumentType.CSV),
        ("report.docx", DocumentType.DOCX)
    ]

    for filename, expected_type in test_files:
        try:
            doc_type = get_document_type(filename)
            if doc_type == expected_type:
                print(f"✓ {filename} → {doc_type.value}")
            else:
                print(f"✗ {filename} → expected {expected_type.value}, got {doc_type.value}")
        except FileValidationError as e:
            print(f"✗ {filename} → error: {e}")


def test_file_storage():
    """Test file storage service."""
    print_section("Testing File Storage Service")

    # Initialize service
    storage = FileStorageService()
    test_project_id = 999  # Use a test project ID

    # Test 1: Save a file
    print("Test 1: Saving a test file...")
    try:
        # Create test file content
        test_content = b"This is a test PDF document content."
        file_stream = io.BytesIO(test_content)

        relative_path, unique_filename = storage.save_file(
            file_stream,
            "test_document.pdf",
            test_project_id
        )

        print(f"✓ File saved successfully")
        print(f"  - Relative path: {relative_path}")
        print(f"  - Unique filename: {unique_filename}")

        # Test 2: Check file exists
        print("\nTest 2: Checking if file exists...")
        if storage.file_exists(relative_path):
            print("✓ File exists in storage")
        else:
            print("✗ File not found in storage")

        # Test 3: Get file size
        print("\nTest 3: Getting file size...")
        file_size = storage.get_file_size(relative_path)
        print(f"✓ File size: {file_size} bytes")

        # Test 4: Read file content
        print("\nTest 4: Reading file content...")
        content = storage.read_file(relative_path)
        if content == test_content:
            print("✓ File content matches original")
        else:
            print("✗ File content does not match")

        # Test 5: List project files
        print("\nTest 5: Listing project files...")
        files = storage.list_project_files(test_project_id)
        print(f"✓ Found {len(files)} file(s) in project")
        for file_info in files:
            print(f"  - {file_info['filename']} ({file_info['size_mb']} MB)")

        # Test 6: Get storage stats
        print("\nTest 6: Getting storage statistics...")
        stats = storage.get_storage_stats(test_project_id)
        print(f"✓ Storage stats for project {test_project_id}:")
        print(f"  - Total files: {stats['total_files']}")
        print(f"  - Total size: {stats['total_size_mb']} MB")

        # Test 7: Save multiple files
        print("\nTest 7: Saving multiple files...")
        file_paths = []
        for i in range(3):
            content = f"Test file {i} content".encode()
            file_stream = io.BytesIO(content)
            path, _ = storage.save_file(
                file_stream,
                f"test_file_{i}.txt",
                test_project_id
            )
            file_paths.append(path)
            print(f"✓ Saved test_file_{i}.txt")

        # Test 8: Cleanup orphaned files
        print("\nTest 8: Testing orphaned file cleanup...")
        # Keep only the first file, others should be considered orphaned
        valid_paths = [file_paths[0]]
        deleted = storage.cleanup_orphaned_files(test_project_id, valid_paths)
        print(f"✓ Cleaned up {deleted} orphaned file(s)")

        # Test 9: Delete specific file
        print("\nTest 9: Deleting specific file...")
        if storage.delete_file(file_paths[0]):
            print("✓ File deleted successfully")
        else:
            print("✗ File was not found")

        # Test 10: Cleanup all project files
        print("\nTest 10: Cleaning up all project files...")
        deleted_count = storage.cleanup_project_files(test_project_id)
        print(f"✓ Deleted {deleted_count} file(s)")

        # Verify cleanup
        remaining_files = storage.list_project_files(test_project_id)
        if len(remaining_files) == 0:
            print("✓ All files cleaned up successfully")
        else:
            print(f"✗ {len(remaining_files)} file(s) still remain")

    except FileStorageError as e:
        print(f"✗ Storage error: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


def test_integration():
    """Test integration of validation and storage."""
    print_section("Testing Integration: Validation + Storage")

    storage = FileStorageService()
    test_project_id = 998

    # Test complete workflow
    print("Test: Complete file upload workflow...")
    try:
        # Step 1: Create test file
        filename = "integration_test.pdf"
        content = b"%PDF-1.4 Test PDF content"
        file_size = len(content)

        print(f"1. Created test file: {filename} ({file_size} bytes)")

        # Step 2: Validate file
        safe_filename, doc_type, mime_type = validate_file_upload(
            filename,
            file_size,
            "application/pdf",
            content
        )
        print(f"2. Validated file:")
        print(f"   - Safe filename: {safe_filename}")
        print(f"   - Document type: {doc_type.value}")
        print(f"   - MIME type: {mime_type}")

        # Step 3: Store file
        file_stream = io.BytesIO(content)
        relative_path, unique_filename = storage.save_file(
            file_stream,
            safe_filename,
            test_project_id
        )
        print(f"3. Stored file:")
        print(f"   - Path: {relative_path}")
        print(f"   - Unique name: {unique_filename}")

        # Step 4: Verify stored file
        stored_content = storage.read_file(relative_path)
        if stored_content == content:
            print("4. ✓ Verified file content matches original")
        else:
            print("4. ✗ File content does not match")

        # Step 5: Cleanup
        storage.cleanup_project_files(test_project_id)
        print("5. ✓ Cleaned up test files")

        print("\n✓ Integration test completed successfully!")

    except (FileValidationError, FileStorageError) as e:
        print(f"\n✗ Integration test failed: {e}")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print(" File Storage System Test Suite")
    print("="*60)

    try:
        # Run test suites
        test_file_validation()
        test_file_storage()
        test_integration()

        # Summary
        print_section("Test Summary")
        print("✓ All test suites completed")
        print("\nNote: Check output above for individual test results")

    except Exception as e:
        print(f"\n✗ Fatal error during testing: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
