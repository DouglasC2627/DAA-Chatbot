"""
Project API routes.

This module provides REST API endpoints for project management:
- Create, read, update, delete projects
- Open project folders
- Get project statistics
- Export/import projects
- Switch project contexts
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from services.project_service import project_service, ProjectServiceError
from models.base import format_datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/projects", tags=["projects"])


# Pydantic models for request/response

class ProjectCreate(BaseModel):
    """Request model for creating a project."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    folder_path: Optional[str] = Field(None, description="Path to project folder")
    settings: Optional[dict] = Field(None, description="Project settings")


class ProjectUpdate(BaseModel):
    """Request model for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    folder_path: Optional[str] = None
    settings: Optional[dict] = None


class ProjectResponse(BaseModel):
    """Response model for project data."""
    id: int
    name: str
    description: Optional[str]
    chroma_collection_name: str
    document_count: int
    total_chunks: int
    settings: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]

    class Config:
        from_attributes = True


class ProjectStatistics(BaseModel):
    """Response model for project statistics."""
    project_id: int
    project_name: str
    document_count: int
    total_chunks: int
    total_size_bytes: int
    chat_count: int
    message_count: int
    created_at: Optional[str]
    updated_at: Optional[str]
    folder_path: Optional[str]


class FolderOpenResponse(BaseModel):
    """Response model for opening a project folder."""
    folder_path: str
    file_count: int
    files: List[dict]
    supported_extensions: List[str]


class ProjectExportResponse(BaseModel):
    """Response model for project export."""
    export_path: str
    project_name: str
    document_count: int
    chat_count: int
    export_date: str


class ProjectSwitchResponse(BaseModel):
    """Response model for switching project context."""
    previous_project: dict
    current_project: dict


# API Endpoints

@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new project.

    Args:
        project_data: Project creation data
        db: Database session

    Returns:
        Created project

    Raises:
        HTTPException: If project creation fails
    """
    try:
        project = await project_service.create_project(
            db=db,
            name=project_data.name,
            description=project_data.description,
            folder_path=project_data.folder_path,
            settings_dict=project_data.settings
        )

        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            chroma_collection_name=project.chroma_collection_name,
            document_count=project.document_count,
            total_chunks=project.total_chunks,
            settings=project.settings,
            created_at=format_datetime(project.created_at),
            updated_at=format_datetime(project.updated_at)
        )

    except ProjectServiceError as e:
        logger.error(f"Failed to create project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    include_deleted: bool = Query(False, description="Include soft-deleted projects"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all projects.

    Args:
        skip: Number of records to skip
        limit: Maximum records to return
        include_deleted: Include soft-deleted projects
        db: Database session

    Returns:
        List of projects
    """
    try:
        projects = await project_service.list_projects(
            db=db,
            skip=skip,
            limit=limit,
            include_deleted=include_deleted
        )

        return [
            ProjectResponse(
                id=project.id,
                name=project.name,
                description=project.description,
                chroma_collection_name=project.chroma_collection_name,
                document_count=project.document_count,
                total_chunks=project.total_chunks,
                settings=project.settings,
                created_at=project.created_at.isoformat() if project.created_at else None,
                updated_at=project.updated_at.isoformat() if project.updated_at else None
            )
            for project in projects
        ]

    except Exception as e:
        logger.error(f"Failed to list projects: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list projects"
        )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a project by ID.

    Args:
        project_id: Project ID
        db: Database session

    Returns:
        Project details

    Raises:
        HTTPException: If project not found
    """
    try:
        project = await project_service.get_project(db, project_id)

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            chroma_collection_name=project.chroma_collection_name,
            document_count=project.document_count,
            total_chunks=project.total_chunks,
            settings=project.settings,
            created_at=format_datetime(project.created_at),
            updated_at=format_datetime(project.updated_at)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get project"
        )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a project.

    Args:
        project_id: Project ID
        project_data: Project update data
        db: Database session

    Returns:
        Updated project

    Raises:
        HTTPException: If project not found or update fails
    """
    try:
        project = await project_service.update_project(
            db=db,
            project_id=project_id,
            name=project_data.name,
            description=project_data.description,
            folder_path=project_data.folder_path,
            settings_dict=project_data.settings
        )

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            chroma_collection_name=project.chroma_collection_name,
            document_count=project.document_count,
            total_chunks=project.total_chunks,
            settings=project.settings,
            created_at=format_datetime(project.created_at),
            updated_at=format_datetime(project.updated_at)
        )

    except HTTPException:
        raise
    except ProjectServiceError as e:
        logger.error(f"Failed to update project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error updating project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update project"
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    hard_delete: bool = Query(False, description="Permanently delete project"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a project.

    Args:
        project_id: Project ID
        hard_delete: If True, permanently delete; otherwise soft delete
        db: Database session

    Raises:
        HTTPException: If project not found or deletion fails
    """
    try:
        success = await project_service.delete_project(
            db=db,
            project_id=project_id,
            hard_delete=hard_delete
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

    except HTTPException:
        raise
    except ProjectServiceError as e:
        logger.error(f"Failed to delete project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete project"
        )


@router.post("/{project_id}/open-folder", response_model=FolderOpenResponse)
async def open_project_folder(
    project_id: int,
    folder_path: str = Query(..., description="Path to folder to open"),
    db: AsyncSession = Depends(get_db)
):
    """
    Open a folder for a project and scan for documents.

    This endpoint allows users to point a project to a specific folder
    and discover what files are available for import.

    Args:
        project_id: Project ID
        folder_path: Path to the folder to open
        db: Database session

    Returns:
        Folder information and discovered files

    Raises:
        HTTPException: If operation fails
    """
    try:
        result = await project_service.open_project_folder(
            db=db,
            project_id=project_id,
            folder_path=folder_path
        )

        return FolderOpenResponse(**result)

    except ProjectServiceError as e:
        logger.error(f"Failed to open project folder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error opening project folder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to open project folder"
        )


@router.get("/{project_id}/folder")
async def get_project_folder(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get the folder path associated with a project.

    Args:
        project_id: Project ID
        db: Database session

    Returns:
        Folder path or null if not set
    """
    try:
        folder_path = await project_service.get_project_folder(db, project_id)

        return {
            "project_id": project_id,
            "folder_path": folder_path
        }

    except Exception as e:
        logger.error(f"Failed to get project folder: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get project folder"
        )


@router.get("/{project_id}/statistics", response_model=ProjectStatistics)
async def get_project_statistics(
    project_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed statistics for a project.

    Args:
        project_id: Project ID
        db: Database session

    Returns:
        Project statistics

    Raises:
        HTTPException: If project not found
    """
    try:
        stats = await project_service.get_project_statistics(db, project_id)

        return ProjectStatistics(**stats)

    except ProjectServiceError as e:
        logger.error(f"Failed to get project statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error getting project statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get project statistics"
        )


@router.post("/{project_id}/export", response_model=ProjectExportResponse)
async def export_project(
    project_id: int,
    export_path: str = Query(..., description="Path where to save the export"),
    include_documents: bool = Query(True, description="Include documents in export"),
    include_chats: bool = Query(True, description="Include chats in export"),
    db: AsyncSession = Depends(get_db)
):
    """
    Export a project to a file.

    Args:
        project_id: Project ID
        export_path: Path where to save the export
        include_documents: Include documents in export
        include_chats: Include chat histories in export
        db: Database session

    Returns:
        Export metadata

    Raises:
        HTTPException: If export fails
    """
    try:
        result = await project_service.export_project(
            db=db,
            project_id=project_id,
            export_path=export_path,
            include_documents=include_documents,
            include_chats=include_chats
        )

        return ProjectExportResponse(**result)

    except ProjectServiceError as e:
        logger.error(f"Failed to export project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error exporting project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export project"
        )


@router.post("/import", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def import_project(
    import_path: str = Query(..., description="Path to the export file"),
    new_name: Optional[str] = Query(None, description="Optional new name for imported project"),
    db: AsyncSession = Depends(get_db)
):
    """
    Import a project from an export file.

    Args:
        import_path: Path to the export file
        new_name: Optional new name for the imported project
        db: Database session

    Returns:
        Imported project

    Raises:
        HTTPException: If import fails
    """
    try:
        project = await project_service.import_project(
            db=db,
            import_path=import_path,
            new_name=new_name
        )

        return ProjectResponse(
            id=project.id,
            name=project.name,
            description=project.description,
            chroma_collection_name=project.chroma_collection_name,
            document_count=project.document_count,
            total_chunks=project.total_chunks,
            settings=project.settings,
            created_at=format_datetime(project.created_at),
            updated_at=format_datetime(project.updated_at)
        )

    except ProjectServiceError as e:
        logger.error(f"Failed to import project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error importing project: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to import project"
        )


@router.post("/switch", response_model=ProjectSwitchResponse)
async def switch_project_context(
    from_project_id: int = Query(..., description="Current project ID"),
    to_project_id: int = Query(..., description="Target project ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Switch from one project context to another.

    This endpoint is useful for UI operations when switching between projects.

    Args:
        from_project_id: Current project ID
        to_project_id: Target project ID
        db: Database session

    Returns:
        Information about the project switch

    Raises:
        HTTPException: If switching fails
    """
    try:
        result = await project_service.switch_project_context(
            db=db,
            from_project_id=from_project_id,
            to_project_id=to_project_id
        )

        return ProjectSwitchResponse(**result)

    except ProjectServiceError as e:
        logger.error(f"Failed to switch project context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error switching project context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to switch project context"
        )
