"""
Maintenance API routes.

This module provides endpoints for system maintenance and administrative tasks:
- ChromaDB cleanup and optimization
- Storage statistics
- Database maintenance
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, status
from pydantic import BaseModel

from core.vectorstore import vector_store
from services.file_storage import file_storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/maintenance", tags=["maintenance"])


# Response Models

class CleanupResponse(BaseModel):
    """Response model for cleanup operations."""
    status: str
    cleaned_items: int
    cleaned_size_bytes: int
    active_collections: list
    message: str


class StorageStatsResponse(BaseModel):
    """Response model for storage statistics."""
    total_files: int
    total_size_bytes: int
    total_size_mb: float


class MaintenanceStatusResponse(BaseModel):
    """Response model for overall maintenance status."""
    vectorstore_stats: Dict[str, Any]
    file_storage_stats: Dict[str, Any]


# Endpoints

@router.post("/cleanup/vectorstore", response_model=CleanupResponse)
async def cleanup_vectorstore():
    """
    Clean up orphaned ChromaDB files.

    This endpoint triggers a comprehensive cleanup of the ChromaDB persist directory,
    removing files that don't belong to any active collection. This is useful after
    deleting multiple projects or when you notice the chroma folder is not being
    cleaned up properly.

    Returns:
        Cleanup statistics including items removed and disk space freed
    """
    try:
        result = vector_store.force_cleanup_all_orphaned_files()

        if result.get("status") == "error":
            return CleanupResponse(
                status="error",
                cleaned_items=0,
                cleaned_size_bytes=0,
                active_collections=[],
                message=result.get("message", "Unknown error")
            )

        cleaned_items = result.get("cleaned_items", 0)
        cleaned_size_mb = result.get("cleaned_size_bytes", 0) / (1024 * 1024)

        message = (
            f"Successfully cleaned up {cleaned_items} orphaned items, "
            f"freed {cleaned_size_mb:.2f} MB of disk space"
        )

        logger.info(message)

        return CleanupResponse(
            status=result.get("status", "success"),
            cleaned_items=cleaned_items,
            cleaned_size_bytes=result.get("cleaned_size_bytes", 0),
            active_collections=result.get("active_collections", []),
            message=message
        )

    except Exception as e:
        logger.error(f"Vectorstore cleanup failed: {str(e)}")
        return CleanupResponse(
            status="error",
            cleaned_items=0,
            cleaned_size_bytes=0,
            active_collections=[],
            message=f"Cleanup failed: {str(e)}"
        )


@router.get("/stats/storage", response_model=StorageStatsResponse)
async def get_storage_stats():
    """
    Get overall file storage statistics.

    Returns:
        Storage statistics including total files and disk usage
    """
    try:
        stats = file_storage_service.get_storage_stats()

        return StorageStatsResponse(
            total_files=stats.get("total_files", 0),
            total_size_bytes=stats.get("total_size_bytes", 0),
            total_size_mb=stats.get("total_size_mb", 0.0)
        )

    except Exception as e:
        logger.error(f"Failed to get storage stats: {str(e)}")
        return StorageStatsResponse(
            total_files=0,
            total_size_bytes=0,
            total_size_mb=0.0
        )


@router.get("/status", response_model=MaintenanceStatusResponse)
async def get_maintenance_status():
    """
    Get overall maintenance status and statistics.

    This endpoint provides a comprehensive view of system health,
    including vectorstore and file storage statistics.

    Returns:
        Comprehensive maintenance status
    """
    try:
        # Get vectorstore stats
        collections = vector_store.list_collections()
        vectorstore_stats = {
            "total_collections": len(collections),
            "collections": collections
        }

        # Get file storage stats
        file_storage_stats = file_storage_service.get_storage_stats()

        return MaintenanceStatusResponse(
            vectorstore_stats=vectorstore_stats,
            file_storage_stats=file_storage_stats
        )

    except Exception as e:
        logger.error(f"Failed to get maintenance status: {str(e)}")
        return MaintenanceStatusResponse(
            vectorstore_stats={"error": str(e)},
            file_storage_stats={"error": str(e)}
        )
