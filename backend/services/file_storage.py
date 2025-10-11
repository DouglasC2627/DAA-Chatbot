"""
File storage service for managing document uploads and storage.

This service handles:
- Storing uploaded files in project-based directories
- Generating unique filenames to prevent collisions
- Retrieving files from storage
- Deleting files and cleaning up orphaned files
- Managing storage directory structure
"""
import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO, Optional

from core.config import settings
from models.document import Document, DocumentType


class FileStorageError(Exception):
    """Raised when file storage operations fail."""
    pass


class FileStorageService:
    """Service for managing file storage operations."""

    def __init__(self, base_dir: str = None):
        """
        Initialize file storage service.

        Args:
            base_dir: Base directory for file storage (defaults to settings.UPLOAD_DIR)
        """
        self.base_dir = Path(base_dir or settings.UPLOAD_DIR)
        self._ensure_base_directory()

    def _ensure_base_directory(self) -> None:
        """Ensure base storage directory exists."""
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_project_directory(self, project_id: int) -> Path:
        """
        Get storage directory path for a specific project.

        Args:
            project_id: ID of the project

        Returns:
            Path to project's storage directory
        """
        return self.base_dir / f"project_{project_id}"

    def _ensure_project_directory(self, project_id: int) -> Path:
        """
        Ensure project storage directory exists.

        Args:
            project_id: ID of the project

        Returns:
            Path to project's storage directory
        """
        project_dir = self._get_project_directory(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    def _generate_unique_filename(
        self,
        original_filename: str,
        project_id: int
    ) -> str:
        """
        Generate a unique filename to prevent collisions.

        Format: {timestamp}_{uuid}_{original_filename}

        Args:
            original_filename: Original name of the file
            project_id: ID of the project

        Returns:
            Unique filename
        """
        # Get file extension
        extension = Path(original_filename).suffix
        name_without_ext = Path(original_filename).stem

        # Generate unique identifier
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]

        # Create unique filename
        unique_filename = f"{timestamp}_{unique_id}_{name_without_ext}{extension}"

        return unique_filename

    def _get_relative_path(self, project_id: int, filename: str) -> str:
        """
        Get relative path for storage in database.

        Args:
            project_id: ID of the project
            filename: Name of the file

        Returns:
            Relative path string
        """
        return f"project_{project_id}/{filename}"

    def save_file(
        self,
        file_content: BinaryIO,
        original_filename: str,
        project_id: int
    ) -> tuple[str, str]:
        """
        Save uploaded file to storage.

        Args:
            file_content: File content as binary stream
            original_filename: Original name of the file
            project_id: ID of the project

        Returns:
            Tuple of (file_path, unique_filename)

        Raises:
            FileStorageError: If file cannot be saved
        """
        try:
            # Ensure project directory exists
            project_dir = self._ensure_project_directory(project_id)

            # Generate unique filename
            unique_filename = self._generate_unique_filename(
                original_filename,
                project_id
            )

            # Full path to save file
            file_path = project_dir / unique_filename

            # Save file
            with open(file_path, "wb") as f:
                # Copy file content
                shutil.copyfileobj(file_content, f)

            # Return relative path for database storage
            relative_path = self._get_relative_path(project_id, unique_filename)

            return relative_path, unique_filename

        except Exception as e:
            raise FileStorageError(f"Failed to save file: {str(e)}") from e

    def get_file_path(self, relative_path: str) -> Path:
        """
        Get absolute path to a file from relative path.

        Args:
            relative_path: Relative path stored in database

        Returns:
            Absolute Path to the file

        Raises:
            FileStorageError: If file doesn't exist
        """
        file_path = self.base_dir / relative_path

        if not file_path.exists():
            raise FileStorageError(f"File not found: {relative_path}")

        return file_path

    def read_file(self, relative_path: str) -> bytes:
        """
        Read file content from storage.

        Args:
            relative_path: Relative path stored in database

        Returns:
            File content as bytes

        Raises:
            FileStorageError: If file cannot be read
        """
        try:
            file_path = self.get_file_path(relative_path)

            with open(file_path, "rb") as f:
                return f.read()

        except Exception as e:
            raise FileStorageError(f"Failed to read file: {str(e)}") from e

    def delete_file(self, relative_path: str) -> bool:
        """
        Delete file from storage.

        Args:
            relative_path: Relative path stored in database

        Returns:
            True if file was deleted, False if it didn't exist

        Raises:
            FileStorageError: If file cannot be deleted
        """
        try:
            file_path = self.base_dir / relative_path

            if file_path.exists():
                file_path.unlink()
                return True

            return False

        except Exception as e:
            raise FileStorageError(f"Failed to delete file: {str(e)}") from e

    def file_exists(self, relative_path: str) -> bool:
        """
        Check if file exists in storage.

        Args:
            relative_path: Relative path stored in database

        Returns:
            True if file exists, False otherwise
        """
        file_path = self.base_dir / relative_path
        return file_path.exists()

    def get_file_size(self, relative_path: str) -> int:
        """
        Get size of stored file.

        Args:
            relative_path: Relative path stored in database

        Returns:
            File size in bytes

        Raises:
            FileStorageError: If file doesn't exist
        """
        file_path = self.get_file_path(relative_path)
        return file_path.stat().st_size

    def move_file(
        self,
        old_relative_path: str,
        new_project_id: int
    ) -> str:
        """
        Move file to a different project directory.

        Args:
            old_relative_path: Current relative path
            new_project_id: ID of the new project

        Returns:
            New relative path

        Raises:
            FileStorageError: If file cannot be moved
        """
        try:
            # Get source file
            old_path = self.get_file_path(old_relative_path)
            filename = old_path.name

            # Ensure new project directory exists
            new_project_dir = self._ensure_project_directory(new_project_id)

            # New path
            new_path = new_project_dir / filename
            new_relative_path = self._get_relative_path(new_project_id, filename)

            # Move file
            shutil.move(str(old_path), str(new_path))

            return new_relative_path

        except Exception as e:
            raise FileStorageError(f"Failed to move file: {str(e)}") from e

    def cleanup_project_files(self, project_id: int) -> int:
        """
        Delete all files for a project.

        Args:
            project_id: ID of the project

        Returns:
            Number of files deleted

        Raises:
            FileStorageError: If cleanup fails
        """
        try:
            project_dir = self._get_project_directory(project_id)

            if not project_dir.exists():
                return 0

            # Count files before deletion
            files = list(project_dir.glob("*"))
            file_count = len([f for f in files if f.is_file()])

            # Delete directory and all contents
            shutil.rmtree(project_dir)

            return file_count

        except Exception as e:
            raise FileStorageError(
                f"Failed to cleanup project files: {str(e)}"
            ) from e

    def cleanup_orphaned_files(
        self,
        project_id: int,
        valid_file_paths: list[str]
    ) -> int:
        """
        Remove files that are not tracked in database.

        Args:
            project_id: ID of the project
            valid_file_paths: List of relative paths that should exist

        Returns:
            Number of orphaned files deleted
        """
        project_dir = self._get_project_directory(project_id)

        if not project_dir.exists():
            return 0

        # Get all files in project directory
        all_files = [f for f in project_dir.glob("*") if f.is_file()]

        # Convert valid paths to absolute paths
        valid_absolute_paths = {
            (self.base_dir / path).resolve()
            for path in valid_file_paths
        }

        # Find and delete orphaned files
        deleted_count = 0
        for file_path in all_files:
            if file_path.resolve() not in valid_absolute_paths:
                try:
                    file_path.unlink()
                    deleted_count += 1
                except Exception:
                    # Continue even if one file fails
                    pass

        return deleted_count

    def get_storage_stats(self, project_id: Optional[int] = None) -> dict:
        """
        Get storage statistics.

        Args:
            project_id: Optional project ID to get stats for specific project

        Returns:
            Dictionary with storage statistics
        """
        if project_id is not None:
            project_dir = self._get_project_directory(project_id)
            if not project_dir.exists():
                return {
                    "total_files": 0,
                    "total_size_bytes": 0,
                    "total_size_mb": 0.0
                }

            files = [f for f in project_dir.glob("*") if f.is_file()]
        else:
            files = [f for f in self.base_dir.rglob("*") if f.is_file()]

        total_size = sum(f.stat().st_size for f in files)

        return {
            "total_files": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }

    def list_project_files(self, project_id: int) -> list[dict]:
        """
        List all files for a project.

        Args:
            project_id: ID of the project

        Returns:
            List of file information dictionaries
        """
        project_dir = self._get_project_directory(project_id)

        if not project_dir.exists():
            return []

        files = []
        for file_path in project_dir.glob("*"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "relative_path": self._get_relative_path(
                        project_id,
                        file_path.name
                    ),
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024 * 1024), 2),
                    "modified_at": datetime.fromtimestamp(stat.st_mtime)
                })

        return files


# Create global file storage service instance
file_storage_service = FileStorageService()
