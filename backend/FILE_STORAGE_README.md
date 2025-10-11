# File Storage System Documentation

## Overview

The file storage system provides a secure, organized way to handle document uploads in the DAA Chatbot. It includes comprehensive validation, project-based storage organization, and utilities for file lifecycle management.

## Components

### 1. File Validation (`utils/file_validation.py`)

Provides security-focused validation for uploaded files:

- **File Size Validation**: Enforces maximum file size limits (default 10MB)
- **File Type Validation**: Supports PDF, DOCX, TXT, MD, CSV, XLSX formats
- **MIME Type Validation**: Validates files match their declared type
- **Filename Sanitization**: Prevents directory traversal and dangerous characters
- **Magic Number Detection**: Content-based file type verification

#### Supported File Types

| Extension | Document Type | MIME Types |
|-----------|---------------|------------|
| .pdf | PDF | application/pdf |
| .docx, .doc | DOCX | application/vnd.openxmlformats-officedocument.wordprocessingml.document |
| .txt | TXT | text/plain |
| .md, .markdown | MD | text/markdown, text/plain |
| .csv | CSV | text/csv, application/csv |
| .xlsx, .xls | XLSX | application/vnd.openxmlformats-officedocument.spreadsheetml.sheet |

#### Usage Example

```python
from utils.file_validation import validate_file_upload, FileValidationError

try:
    safe_filename, doc_type, mime_type = validate_file_upload(
        filename="document.pdf",
        file_size=1024 * 1024,  # 1MB
        mime_type="application/pdf",
        content=file_bytes  # Optional for enhanced validation
    )
    print(f"Valid file: {safe_filename} ({doc_type.value})")
except FileValidationError as e:
    print(f"Validation failed: {e}")
```

### 2. File Storage Service (`services/file_storage.py`)

Manages physical file storage with project-based organization:

#### Features

- **Project-Based Directories**: Files organized as `project_{id}/filename`
- **Unique Filenames**: Prevents collisions with timestamp + UUID format
- **CRUD Operations**: Save, read, delete, move files
- **Cleanup Utilities**: Remove orphaned files and project directories
- **Storage Statistics**: Track file counts and sizes

#### Directory Structure

```
storage/
└── documents/
    ├── project_1/
    │   ├── 20251011_091703_abc12345_document.pdf
    │   └── 20251011_092014_def67890_report.docx
    ├── project_2/
    │   └── 20251011_093520_ghi34567_data.csv
    └── project_3/
        └── ...
```

#### Usage Examples

##### Save a File

```python
from services.file_storage import file_storage_service, FileStorageError

try:
    # file_stream is a BinaryIO object (e.g., from request.files)
    relative_path, unique_filename = file_storage_service.save_file(
        file_content=file_stream,
        original_filename="document.pdf",
        project_id=1
    )
    print(f"Saved to: {relative_path}")
except FileStorageError as e:
    print(f"Storage failed: {e}")
```

##### Read a File

```python
try:
    content = file_storage_service.read_file("project_1/20251011_091703_abc12345_document.pdf")
    print(f"Read {len(content)} bytes")
except FileStorageError as e:
    print(f"Read failed: {e}")
```

##### Delete a File

```python
deleted = file_storage_service.delete_file("project_1/20251011_091703_abc12345_document.pdf")
if deleted:
    print("File deleted")
```

##### Cleanup Project Files

```python
# Delete all files for a project
deleted_count = file_storage_service.cleanup_project_files(project_id=1)
print(f"Deleted {deleted_count} files")
```

##### Remove Orphaned Files

```python
# Remove files not tracked in database
valid_paths = ["project_1/file1.pdf", "project_1/file2.pdf"]
orphaned_count = file_storage_service.cleanup_orphaned_files(
    project_id=1,
    valid_file_paths=valid_paths
)
print(f"Removed {orphaned_count} orphaned files")
```

##### Get Storage Statistics

```python
# Stats for specific project
stats = file_storage_service.get_storage_stats(project_id=1)
print(f"Project has {stats['total_files']} files ({stats['total_size_mb']} MB)")

# Stats for all storage
stats = file_storage_service.get_storage_stats()
print(f"Total: {stats['total_files']} files ({stats['total_size_mb']} MB)")
```

## Security Features

### Input Validation

1. **File Size Limits**: Prevents resource exhaustion
2. **Extension Whitelist**: Only allows supported file types
3. **MIME Type Verification**: Ensures file content matches extension
4. **Filename Sanitization**: Removes path traversal attempts and dangerous characters

### Filename Security

The sanitization process:
- Strips all directory components (e.g., `../../../etc/passwd` → `passwd`)
- Rejects files with dangerous characters: `.. / \ \0 : * ? " < > |`
- Enforces maximum filename length (255 characters)
- Uses UUID-based unique names to prevent collisions

### Storage Isolation

- Each project has its own directory
- Files are stored with relative paths in the database
- Physical access requires valid project context
- Cleanup operations are project-scoped

## Configuration

Settings in `core/config.py`:

```python
# Storage directory
UPLOAD_DIR: str = "./storage/documents"

# Maximum file size (10MB)
MAX_FILE_SIZE: int = 10485760
```

## Testing

Run the comprehensive test suite:

```bash
cd backend
source venv/bin/activate
python test_file_storage.py
```

The test suite covers:
- File validation (valid files, oversized files, unsupported types, dangerous filenames)
- File storage operations (save, read, delete, list, move)
- Cleanup utilities (orphaned files, project cleanup)
- Integration testing (validation + storage workflow)

## Error Handling

### FileValidationError

Raised when file validation fails:
- File size exceeds limit
- Unsupported file type
- Invalid MIME type
- Dangerous filename

### FileStorageError

Raised when storage operations fail:
- Cannot save file (disk full, permission issues)
- File not found
- Cannot delete file
- Cleanup operations fail

## Best Practices

1. **Always Validate Before Storing**
   ```python
   # Validate first
   safe_filename, doc_type, mime_type = validate_file_upload(...)
   # Then store
   relative_path, unique_filename = file_storage_service.save_file(...)
   ```

2. **Store Relative Paths in Database**
   - Database should store the relative path returned by `save_file()`
   - Never store absolute paths

3. **Cleanup on Deletion**
   - When deleting a document from database, also delete from storage
   - Use `delete_file()` with the stored relative path

4. **Regular Orphan Cleanup**
   - Periodically run `cleanup_orphaned_files()` to remove untracked files
   - Compare database records with filesystem

5. **Project Deletion**
   - When deleting a project, use `cleanup_project_files()` to remove all files

## Integration with Document Model

The Document model (`models/document.py`) tracks file metadata:

```python
class Document(Base):
    filename: str           # Original filename
    file_path: str          # Relative path from storage service
    file_size: int          # Size in bytes
    file_type: DocumentType # Type enum
    mime_type: str          # MIME type
    status: DocumentStatus  # Processing status
    # ... other fields
```

### Complete Upload Workflow

```python
from utils.file_validation import validate_file_upload, FileValidationError
from services.file_storage import file_storage_service, FileStorageError
from models.document import Document
from crud.document import create_document

async def upload_document(file, project_id: int, db: Session):
    try:
        # 1. Read file content
        content = await file.read()

        # 2. Validate
        safe_filename, doc_type, mime_type = validate_file_upload(
            filename=file.filename,
            file_size=len(content),
            mime_type=file.content_type,
            content=content
        )

        # 3. Store file
        file.file.seek(0)  # Reset stream position
        relative_path, unique_filename = file_storage_service.save_file(
            file_content=file.file,
            original_filename=safe_filename,
            project_id=project_id
        )

        # 4. Create database record
        document = create_document(
            db=db,
            project_id=project_id,
            filename=safe_filename,
            file_path=relative_path,
            file_size=len(content),
            file_type=doc_type,
            mime_type=mime_type
        )

        return document

    except FileValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FileStorageError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## Future Enhancements

Potential improvements:

1. **Compression**: Compress stored files to save space
2. **Encryption**: Encrypt files at rest
3. **Cloud Storage**: Support S3/GCS as storage backend
4. **Virus Scanning**: Integrate antivirus scanning
5. **Thumbnails**: Generate preview images for documents
6. **Versioning**: Track multiple versions of the same document
7. **Streaming**: Support streaming large files without loading into memory

## Troubleshooting

### File not found errors

- Ensure `UPLOAD_DIR` in config matches actual storage location
- Check file permissions on storage directory
- Verify relative path is correctly stored in database

### Permission denied errors

- Ensure web server has write permissions to storage directory
- Check parent directory permissions

### Disk space issues

- Monitor storage usage with `get_storage_stats()`
- Implement cleanup policies for old files
- Consider implementing storage quotas per project

## Summary

Task 2.3 File Storage System is now complete with:

- ✅ Project-based storage directory structure
- ✅ Comprehensive file upload validation (size, type, MIME, security)
- ✅ File storage service with CRUD operations
- ✅ File cleanup utilities for orphaned files and project deletion
- ✅ Test script with 100% passing tests
- ✅ Full documentation and usage examples

The system is production-ready and provides a secure foundation for document management in the DAA Chatbot.
