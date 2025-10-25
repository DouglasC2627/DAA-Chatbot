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
from core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import Depends
from models.project import Project
from models.document import Document

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


class ProjectCountUpdate(BaseModel):
    """Individual project count update result."""
    project_id: int
    project_name: str
    old_count: int
    new_count: int
    updated: bool


class RecalculateCountsResponse(BaseModel):
    """Response model for recalculate counts operation."""
    status: str
    total_projects: int
    updated_projects: int
    projects: list[ProjectCountUpdate]
    message: str


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


@router.post("/recalculate-counts", response_model=RecalculateCountsResponse)
async def recalculate_project_counts(db: AsyncSession = Depends(get_db)):
    """
    Recalculate document counts for all projects.

    This endpoint recalculates the cached document_count field for all projects
    by counting the actual number of documents in the database. Useful for:
    - Fixing incorrect counts after manual database operations
    - Recovering from errors during document upload/delete
    - Verifying data integrity

    Returns:
        Details of which projects were updated and their new counts
    """
    try:
        # Get all projects
        result = await db.execute(select(Project))
        projects = result.scalars().all()

        project_updates = []
        updated_count = 0

        for project in projects:
            # Count actual documents for this project
            doc_result = await db.execute(
                select(Document).where(Document.project_id == project.id)
            )
            documents = doc_result.scalars().all()
            actual_count = len(documents)

            # Check if update needed
            old_count = project.document_count
            needs_update = old_count != actual_count

            if needs_update:
                project.document_count = actual_count
                updated_count += 1
                logger.info(
                    f"Updated project {project.id} ({project.name}): "
                    f"{old_count} -> {actual_count}"
                )

            # Add to results
            project_updates.append(
                ProjectCountUpdate(
                    project_id=project.id,
                    project_name=project.name,
                    old_count=old_count,
                    new_count=actual_count,
                    updated=needs_update
                )
            )

        # Commit all changes
        await db.commit()

        message = (
            f"Successfully recalculated counts for {len(projects)} projects. "
            f"Updated {updated_count} project(s)."
        )

        logger.info(message)

        return RecalculateCountsResponse(
            status="success",
            total_projects=len(projects),
            updated_projects=updated_count,
            projects=project_updates,
            message=message
        )

    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to recalculate project counts: {str(e)}")
        return RecalculateCountsResponse(
            status="error",
            total_projects=0,
            updated_projects=0,
            projects=[],
            message=f"Failed to recalculate counts: {str(e)}"
        )
