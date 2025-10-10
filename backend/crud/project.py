"""
CRUD operations for Project model.
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Project
from crud.base import CRUDBase


class CRUDProject(CRUDBase[Project]):
    """CRUD operations for Project model."""

    async def get_by_name(self, db: AsyncSession, name: str) -> Optional[Project]:
        """
        Get project by name.

        Args:
            db: Database session
            name: Project name

        Returns:
            Project instance or None
        """
        result = await db.execute(
            select(Project).where(Project.name == name)
        )
        return result.scalar_one_or_none()

    async def get_active(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Project]:
        """
        Get active (non-deleted) projects.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of active projects
        """
        result = await db.execute(
            select(Project)
            .where(Project.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_stats(self, db: AsyncSession, id: int) -> Optional[Project]:
        """
        Get project with all related documents and chats.

        Args:
            db: Database session
            id: Project ID

        Returns:
            Project instance with relationships loaded
        """
        result = await db.execute(
            select(Project).where(Project.id == id)
        )
        return result.scalar_one_or_none()

    async def update_document_count(
        self,
        db: AsyncSession,
        project_id: int
    ) -> bool:
        """
        Update cached document count for a project.

        Args:
            db: Database session
            project_id: Project ID

        Returns:
            True if successful
        """
        project = await self.get(db, project_id)
        if not project:
            return False

        project.document_count = len(project.documents)
        await db.flush()
        return True

    async def soft_delete(self, db: AsyncSession, id: int) -> bool:
        """
        Soft delete a project.

        Args:
            db: Database session
            id: Project ID

        Returns:
            True if deleted, False if not found
        """
        project = await self.get(db, id)
        if not project:
            return False

        project.soft_delete()
        await db.flush()
        return True


# Create instance
project = CRUDProject(Project)
