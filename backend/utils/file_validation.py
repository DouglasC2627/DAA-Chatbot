"""
File validation utilities for document uploads.

This module provides validation functions for file uploads including:
- File size validation
- File type/MIME type validation
- File extension validation
- Security checks
"""
import mimetypes
import os
from pathlib import Path
from typing import Tuple

from core.config import settings
from models.document import DocumentType


# Mapping of DocumentType to allowed MIME types
ALLOWED_MIME_TYPES = {
    DocumentType.PDF: ["application/pdf"],
    DocumentType.DOCX: [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword"
    ],
    DocumentType.TXT: ["text/plain"],
    DocumentType.MD: ["text/markdown", "text/plain"],
    DocumentType.CSV: ["text/csv", "application/csv"],
    DocumentType.XLSX: [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel"
    ]
}

# Mapping of file extensions to DocumentType
EXTENSION_TO_TYPE = {
    ".pdf": DocumentType.PDF,
    ".docx": DocumentType.DOCX,
    ".doc": DocumentType.DOCX,
    ".txt": DocumentType.TXT,
    ".md": DocumentType.MD,
    ".markdown": DocumentType.MD,
    ".csv": DocumentType.CSV,
    ".xlsx": DocumentType.XLSX,
    ".xls": DocumentType.XLSX
}


class FileValidationError(Exception):
    """Raised when file validation fails."""
    pass


def validate_file_size(file_size: int) -> None:
    """
    Validate that file size is within allowed limits.

    Args:
        file_size: Size of the file in bytes

    Raises:
        FileValidationError: If file size exceeds the maximum allowed size
    """
    if file_size <= 0:
        raise FileValidationError("File size must be greater than 0")

    if file_size > settings.MAX_FILE_SIZE:
        max_size_mb = settings.MAX_FILE_SIZE / (1024 * 1024)
        actual_size_mb = file_size / (1024 * 1024)
        raise FileValidationError(
            f"File size ({actual_size_mb:.2f} MB) exceeds maximum allowed size "
            f"({max_size_mb:.2f} MB)"
        )


def get_file_extension(filename: str) -> str:
    """
    Extract and normalize file extension.

    Args:
        filename: Name of the file

    Returns:
        Lowercase file extension including the dot (e.g., '.pdf')
    """
    return Path(filename).suffix.lower()


def get_document_type(filename: str) -> DocumentType:
    """
    Determine DocumentType from filename extension.

    Args:
        filename: Name of the file

    Returns:
        DocumentType enum value

    Raises:
        FileValidationError: If file extension is not supported
    """
    extension = get_file_extension(filename)

    if extension not in EXTENSION_TO_TYPE:
        raise FileValidationError(
            f"Unsupported file type: {extension}. "
            f"Supported types: {', '.join(EXTENSION_TO_TYPE.keys())}"
        )

    return EXTENSION_TO_TYPE[extension]


def validate_mime_type(mime_type: str, document_type: DocumentType) -> None:
    """
    Validate that MIME type matches the document type.

    Args:
        mime_type: MIME type of the file
        document_type: Expected document type

    Raises:
        FileValidationError: If MIME type doesn't match expected type
    """
    allowed_types = ALLOWED_MIME_TYPES.get(document_type, [])

    if mime_type not in allowed_types:
        raise FileValidationError(
            f"MIME type '{mime_type}' does not match expected type for {document_type.value}. "
            f"Allowed types: {', '.join(allowed_types)}"
        )


def detect_mime_type(filename: str, content: bytes = None) -> str:
    """
    Detect MIME type from filename and optionally file content.

    Args:
        filename: Name of the file
        content: Optional file content for content-based detection

    Returns:
        Detected MIME type
    """
    # First try to guess from filename
    mime_type, _ = mimetypes.guess_type(filename)

    if mime_type:
        return mime_type

    # If content is provided, try magic number detection
    if content:
        # Check for common file signatures (magic numbers)
        if content.startswith(b'%PDF'):
            return "application/pdf"
        elif content.startswith(b'PK\x03\x04'):
            # ZIP-based formats (DOCX, XLSX)
            if filename.lower().endswith('.docx'):
                return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            elif filename.lower().endswith('.xlsx'):
                return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    # Default to binary
    return "application/octet-stream"


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal and other security issues.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename

    Raises:
        FileValidationError: If filename is invalid
    """
    if not filename:
        raise FileValidationError("Filename cannot be empty")

    # Remove path components
    filename = os.path.basename(filename)

    # Remove or replace dangerous characters
    dangerous_chars = ['..', '/', '\\', '\0', ':', '*', '?', '"', '<', '>', '|']
    for char in dangerous_chars:
        if char in filename:
            raise FileValidationError(
                f"Filename contains invalid character: '{char}'"
            )

    # Ensure filename is not too long (most systems limit to 255 chars)
    if len(filename) > 255:
        raise FileValidationError("Filename is too long (max 255 characters)")

    return filename


def validate_file_upload(
    filename: str,
    file_size: int,
    mime_type: str = None,
    content: bytes = None
) -> Tuple[str, DocumentType, str]:
    """
    Comprehensive validation for file uploads.

    Args:
        filename: Original filename
        file_size: Size of the file in bytes
        mime_type: Optional MIME type (will be detected if not provided)
        content: Optional file content for enhanced validation

    Returns:
        Tuple of (sanitized_filename, document_type, mime_type)

    Raises:
        FileValidationError: If any validation check fails
    """
    # Sanitize filename
    safe_filename = sanitize_filename(filename)

    # Validate file size
    validate_file_size(file_size)

    # Determine document type
    document_type = get_document_type(safe_filename)

    # Detect or validate MIME type
    if mime_type is None:
        mime_type = detect_mime_type(safe_filename, content)

    validate_mime_type(mime_type, document_type)

    return safe_filename, document_type, mime_type


def is_supported_file_type(filename: str) -> bool:
    """
    Check if file type is supported.

    Args:
        filename: Name of the file

    Returns:
        True if file type is supported, False otherwise
    """
    extension = get_file_extension(filename)
    return extension in EXTENSION_TO_TYPE


def get_supported_extensions() -> list[str]:
    """
    Get list of supported file extensions.

    Returns:
        List of supported extensions
    """
    return list(EXTENSION_TO_TYPE.keys())


def get_supported_mime_types() -> list[str]:
    """
    Get list of all supported MIME types.

    Returns:
        List of supported MIME types
    """
    mime_types = []
    for types in ALLOWED_MIME_TYPES.values():
        mime_types.extend(types)
    return list(set(mime_types))  # Remove duplicates
