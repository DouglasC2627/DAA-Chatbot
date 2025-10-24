"""
Project service for managing project operations.

This service handles:
- Project CRUD operations
- Project folder management (opening different project directories)
- Project-document associations
- Project isolation for ChromaDB collections
- Project settings management
- Project export/import functionality
"""

import logging
import json
import shutil
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from models.project import Project
from models.document import Document
from models.chat import Chat
from models.base import format_datetime
from core.vectorstore import vector_store
from core.config import settings

logger = logging.getLogger(__name__)


class ProjectServiceError(Exception):
    """Raised when project service operations fail."""
    pass


class ProjectService:
    """
    Service for managing projects and their associated resources.

    Provides CRUD operations for projects, folder management,
    document associations, and project isolation.
    """

    def __init__(self):
        """Initialize project service."""
        logger.info("ProjectService initialized")

    async def create_project(
        self,
        db: AsyncSession,
        name: str,
        description: Optional[str] = None,
        folder_path: Optional[str] = None,
        settings_dict: Optional[Dict[str, Any]] = None
    ) -> Project:
        """
        Create a new project.

        Args:
            db: Database session
            name: Project name
            description: Optional project description
            folder_path: Optional path to project folder for document imports
            settings_dict: Optional project-specific settings (model, chunk size, etc.)

        Returns:
            Created project object

        Raises:
            ProjectServiceError: If project creation fails
        """
        try:
            # Check if project with same name already exists
            existing = await self._get_by_name(db, name)
            if existing:
                raise ProjectServiceError(f"Project with name '{name}' already exists")

            # Create project
            project = Project(
                name=name,
                description=description,
                chroma_collection_name="",  # Will be set after ID is assigned
                document_count=0,
                total_chunks=0,
                settings=json.dumps(settings_dict) if settings_dict else None
            )

            db.add(project)
            await db.flush()  # Flush to get the ID

            # Generate ChromaDB collection name using the ID
            project.chroma_collection_name = project.generate_collection_name()

            # Create folder path in settings if provided
            if folder_path:
                project_settings = json.loads(project.settings) if project.settings else {}
                project_settings['folder_path'] = folder_path
                project.settings = json.dumps(project_settings)

            await db.commit()
            await db.refresh(project)

            # Initialize ChromaDB collection for this project
            vector_store.get_or_create_collection(project.id)

            logger.info(f"Created project {project.id}: '{name}'")
            return project

        except ProjectServiceError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create project: {str(e)}")
            raise ProjectServiceError(f"Failed to create project: {str(e)}") from e

    async def get_project(
        self,
        db: AsyncSession,
        project_id: int,
        include_documents: bool = False,
        include_chats: bool = False
    ) -> Optional[Project]:
        """
        Get a project by ID.

        Args:
            db: Database session
            project_id: Project ID
            include_documents: Whether to load documents
            include_chats: Whether to load chats

        Returns:
            Project object or None if not found
        """
        try:
            query = select(Project).where(
                and_(
                    Project.id == project_id,
                    Project.deleted_at.is_(None)
                )
            )

            if include_documents:
                query = query.options(selectinload(Project.documents))
            if include_chats:
                query = query.options(selectinload(Project.chats))

            result = await db.execute(query)
            project = result.scalar_one_or_none()

            if project:
                logger.debug(f"Retrieved project {project_id}")

            return project

        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {str(e)}")
            return None

    async def list_projects(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        include_deleted: bool = False
    ) -> List[Project]:
        """
        List all projects.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            include_deleted: Whether to include soft-deleted projects

        Returns:
            List of project objects
        """
        try:
            query = select(Project)

            if not include_deleted:
                query = query.where(Project.deleted_at.is_(None))

            query = (
                query
                .order_by(Project.updated_at.desc())
                .offset(skip)
                .limit(limit)
            )

            result = await db.execute(query)
            projects = result.scalars().all()

            logger.info(f"Retrieved {len(projects)} projects")
            return list(projects)

        except Exception as e:
            logger.error(f"Failed to list projects: {str(e)}")
            return []

    async def update_project(
        self,
        db: AsyncSession,
        project_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        folder_path: Optional[str] = None,
        settings_dict: Optional[Dict[str, Any]] = None
    ) -> Optional[Project]:
        """
        Update a project.

        Args:
            db: Database session
            project_id: Project ID
            name: New name (optional)
            description: New description (optional)
            folder_path: New folder path (optional)
            settings_dict: New settings (optional)

        Returns:
            Updated project or None if not found

        Raises:
            ProjectServiceError: If update fails
        """
        try:
            project = await self.get_project(db, project_id)

            if not project:
                return None

            # Update fields if provided
            if name is not None:
                # Check if name is already taken by another project
                existing = await self._get_by_name(db, name)
                if existing and existing.id != project_id:
                    raise ProjectServiceError(f"Project with name '{name}' already exists")
                project.name = name

            if description is not None:
                project.description = description

            # Update folder path in settings
            if folder_path is not None:
                current_settings = json.loads(project.settings) if project.settings else {}
                current_settings['folder_path'] = folder_path
                project.settings = json.dumps(current_settings)

            # Update settings
            if settings_dict is not None:
                current_settings = json.loads(project.settings) if project.settings else {}
                current_settings.update(settings_dict)
                project.settings = json.dumps(current_settings)

            await db.commit()
            await db.refresh(project)

            logger.info(f"Updated project {project_id}")
            return project

        except ProjectServiceError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update project {project_id}: {str(e)}")
            raise ProjectServiceError(f"Failed to update project: {str(e)}") from e

    async def delete_project(
        self,
        db: AsyncSession,
        project_id: int,
        hard_delete: bool = False
    ) -> bool:
        """
        Delete a project.

        Args:
            db: Database session
            project_id: Project ID
            hard_delete: If True, permanently delete; if False, soft delete

        Returns:
            True if deleted, False if not found

        Raises:
            ProjectServiceError: If deletion fails
        """
        try:
            project = await self.get_project(db, project_id)

            if not project:
                return False

            if hard_delete:
                # Delete ChromaDB collection
                vector_store.delete_collection(project_id)

                # Delete project folder if exists
                await self._delete_project_folder(project)

                # Hard delete from database
                await db.delete(project)
                logger.info(f"Hard deleted project {project_id}")
            else:
                # Soft delete
                project.soft_delete()
                logger.info(f"Soft deleted project {project_id}")

            await db.commit()
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to delete project {project_id}: {str(e)}")
            raise ProjectServiceError(f"Failed to delete project: {str(e)}") from e

    async def open_project_folder(
        self,
        db: AsyncSession,
        project_id: int,
        folder_path: str
    ) -> Dict[str, Any]:
        """
        Open a project folder and scan for documents.

        This allows users to point a project to a specific folder
        and see what documents are available for import.

        Args:
            db: Database session
            project_id: Project ID
            folder_path: Path to the folder to open

        Returns:
            Dictionary with folder info and discovered files

        Raises:
            ProjectServiceError: If folder operations fail
        """
        try:
            project = await self.get_project(db, project_id)

            if not project:
                raise ProjectServiceError(f"Project {project_id} not found")

            # Validate folder path
            folder = Path(folder_path)
            if not folder.exists():
                raise ProjectServiceError(f"Folder does not exist: {folder_path}")

            if not folder.is_dir():
                raise ProjectServiceError(f"Path is not a directory: {folder_path}")

            # Update project with folder path
            await self.update_project(db, project_id, folder_path=str(folder.absolute()))

            # Scan for supported document files
            supported_extensions = {'.pdf', '.docx', '.txt', '.md', '.csv', '.xlsx'}
            discovered_files = []

            for ext in supported_extensions:
                for file_path in folder.rglob(f'*{ext}'):
                    if file_path.is_file():
                        discovered_files.append({
                            'name': file_path.name,
                            'path': str(file_path.absolute()),
                            'size': file_path.stat().st_size,
                            'extension': ext,
                            'relative_path': str(file_path.relative_to(folder))
                        })

            logger.info(f"Opened folder '{folder_path}' for project {project_id}, found {len(discovered_files)} files")

            return {
                'folder_path': str(folder.absolute()),
                'file_count': len(discovered_files),
                'files': discovered_files,
                'supported_extensions': list(supported_extensions)
            }

        except ProjectServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to open project folder: {str(e)}")
            raise ProjectServiceError(f"Failed to open project folder: {str(e)}") from e

    async def get_project_folder(
        self,
        db: AsyncSession,
        project_id: int
    ) -> Optional[str]:
        """
        Get the folder path associated with a project.

        Args:
            db: Database session
            project_id: Project ID

        Returns:
            Folder path or None if not set
        """
        try:
            project = await self.get_project(db, project_id)

            if not project or not project.settings:
                return None

            settings_dict = json.loads(project.settings)
            return settings_dict.get('folder_path')

        except Exception as e:
            logger.error(f"Failed to get project folder: {str(e)}")
            return None

    async def get_project_statistics(
        self,
        db: AsyncSession,
        project_id: int
    ) -> Dict[str, Any]:
        """
        Get detailed statistics for a project.

        Args:
            db: Database session
            project_id: Project ID

        Returns:
            Dictionary with project statistics
        """
        try:
            project = await self.get_project(
                db,
                project_id,
                include_documents=True,
                include_chats=True
            )

            if not project:
                raise ProjectServiceError(f"Project {project_id} not found")

            # Get vector store statistics
            vector_count = vector_store.get_collection_count(project_id)

            # Calculate document statistics
            total_size = sum(doc.file_size for doc in project.documents if doc.file_size)

            # Get chat statistics
            active_chats = [chat for chat in project.chats if not chat.deleted_at]
            total_messages = sum(chat.message_count for chat in active_chats)

            return {
                'project_id': project.id,
                'project_name': project.name,
                'document_count': len(project.documents),
                'total_chunks': vector_count,
                'total_size_bytes': total_size,
                'chat_count': len(active_chats),
                'message_count': total_messages,
                'created_at': format_datetime(project.created_at),
                'updated_at': format_datetime(project.updated_at),
                'folder_path': await self.get_project_folder(db, project_id)
            }

        except ProjectServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to get project statistics: {str(e)}")
            raise ProjectServiceError(f"Failed to get statistics: {str(e)}") from e

    async def export_project(
        self,
        db: AsyncSession,
        project_id: int,
        export_path: str,
        include_documents: bool = True,
        include_chats: bool = True
    ) -> Dict[str, Any]:
        """
        Export a project to a file.

        Args:
            db: Database session
            project_id: Project ID
            export_path: Path where to save the export
            include_documents: Whether to include documents
            include_chats: Whether to include chat histories

        Returns:
            Export metadata

        Raises:
            ProjectServiceError: If export fails
        """
        try:
            project = await self.get_project(
                db,
                project_id,
                include_documents=include_documents,
                include_chats=include_chats
            )

            if not project:
                raise ProjectServiceError(f"Project {project_id} not found")

            export_data = {
                'version': '1.0',
                'export_date': datetime.utcnow().isoformat(),
                'project': {
                    'name': project.name,
                    'description': project.description,
                    'settings': json.loads(project.settings) if project.settings else {},
                    'created_at': format_datetime(project.created_at)
                }
            }

            if include_documents:
                export_data['documents'] = [
                    {
                        'filename': doc.filename,
                        'file_type': doc.file_type,
                        'file_size': doc.file_size,
                        'file_path': doc.file_path,
                        'upload_date': doc.upload_date.isoformat() if doc.upload_date else None
                    }
                    for doc in project.documents
                ]

            if include_chats:
                export_data['chats'] = [
                    {
                        'title': chat.title,
                        'message_count': chat.message_count,
                        'created_at': format_datetime(chat.created_at)
                    }
                    for chat in project.chats
                    if not chat.deleted_at
                ]

            # Write export file
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)

            with open(export_file, 'w') as f:
                json.dump(export_data, f, indent=2)

            logger.info(f"Exported project {project_id} to {export_path}")

            return {
                'export_path': str(export_file.absolute()),
                'project_name': project.name,
                'document_count': len(export_data.get('documents', [])),
                'chat_count': len(export_data.get('chats', [])),
                'export_date': export_data['export_date']
            }

        except ProjectServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to export project: {str(e)}")
            raise ProjectServiceError(f"Failed to export project: {str(e)}") from e

    async def import_project(
        self,
        db: AsyncSession,
        import_path: str,
        new_name: Optional[str] = None
    ) -> Project:
        """
        Import a project from an export file.

        Args:
            db: Database session
            import_path: Path to the export file
            new_name: Optional new name for the imported project

        Returns:
            Imported project

        Raises:
            ProjectServiceError: If import fails
        """
        try:
            # Read export file
            import_file = Path(import_path)
            if not import_file.exists():
                raise ProjectServiceError(f"Import file not found: {import_path}")

            with open(import_file, 'r') as f:
                import_data = json.load(f)

            # Validate import data
            if 'project' not in import_data:
                raise ProjectServiceError("Invalid import file: missing project data")

            project_data = import_data['project']
            project_name = new_name or project_data['name']

            # Create new project
            project = await self.create_project(
                db=db,
                name=project_name,
                description=project_data.get('description'),
                settings_dict=project_data.get('settings', {})
            )

            logger.info(f"Imported project from {import_path} as project {project.id}")

            return project

        except ProjectServiceError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to import project: {str(e)}")
            raise ProjectServiceError(f"Failed to import project: {str(e)}") from e

    async def switch_project_context(
        self,
        db: AsyncSession,
        from_project_id: int,
        to_project_id: int
    ) -> Dict[str, Any]:
        """
        Switch from one project context to another.

        This is useful for UI operations when switching between projects.

        Args:
            db: Database session
            from_project_id: Current project ID
            to_project_id: Target project ID

        Returns:
            Information about the new project context

        Raises:
            ProjectServiceError: If switching fails
        """
        try:
            # Validate both projects exist
            from_project = await self.get_project(db, from_project_id)
            to_project = await self.get_project(db, to_project_id)

            if not from_project:
                raise ProjectServiceError(f"Source project {from_project_id} not found")

            if not to_project:
                raise ProjectServiceError(f"Target project {to_project_id} not found")

            # Get statistics for the new project
            stats = await self.get_project_statistics(db, to_project_id)

            logger.info(f"Switched project context from {from_project_id} to {to_project_id}")

            return {
                'previous_project': {
                    'id': from_project.id,
                    'name': from_project.name
                },
                'current_project': {
                    'id': to_project.id,
                    'name': to_project.name,
                    'description': to_project.description,
                    'statistics': stats
                }
            }

        except ProjectServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to switch project context: {str(e)}")
            raise ProjectServiceError(f"Failed to switch project: {str(e)}") from e

    # Private helper methods

    async def _get_by_name(
        self,
        db: AsyncSession,
        name: str
    ) -> Optional[Project]:
        """Get project by name."""
        try:
            result = await db.execute(
                select(Project).where(
                    and_(
                        Project.name == name,
                        Project.deleted_at.is_(None)
                    )
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get project by name: {str(e)}")
            return None

    async def _delete_project_folder(self, project: Project) -> None:
        """Delete project folder if it exists."""
        try:
            if not project.settings:
                return

            settings_dict = json.loads(project.settings)
            folder_path = settings_dict.get('folder_path')

            if folder_path:
                folder = Path(folder_path)
                # Only delete if it's within our upload directory
                upload_dir = Path(settings.UPLOAD_DIR).resolve()
                if folder.resolve().is_relative_to(upload_dir) and folder.exists():
                    shutil.rmtree(folder)
                    logger.info(f"Deleted project folder: {folder_path}")

        except Exception as e:
            logger.warning(f"Failed to delete project folder: {str(e)}")


# Global project service instance
project_service = ProjectService()
