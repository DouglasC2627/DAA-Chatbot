"""
CRUD operations for Document model.
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Document, DocumentStatus
from crud.base import CRUDBase


class CRUDDocument(CRUDBase[Document]):
    """CRUD operations for Document model."""

    async def get_by_project(
        self,
        db: AsyncSession,
        project_id: int,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Document]:
        """
        Get documents for a specific project.

        Args:
            db: Database session
            project_id: Project ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of documents
        """
        result = await db.execute(
            select(Document)
            .where(Document.project_id == project_id)
            .where(Document.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_status(
        self,
        db: AsyncSession,
        status: DocumentStatus,
        *,
        project_id: Optional[int] = None
    ) -> List[Document]:
        """
        Get documents by status.

        Args:
            db: Database session
            status: Document status
            project_id: Optional project ID filter

        Returns:
            List of documents
        """
        query = select(Document).where(Document.status == status)

        if project_id is not None:
            query = query.where(Document.project_id == project_id)

        result = await db.execute(query)
        return list(result.scalars().all())

    async def mark_processing(self, db: AsyncSession, id: int) -> bool:
        """
        Mark document as processing.

        Args:
            db: Database session
            id: Document ID

        Returns:
            True if successful
        """
        document = await self.get(db, id)
        if not document:
            return False

        document.mark_processing()
        await db.flush()
        return True

    async def mark_completed(
        self,
        db: AsyncSession,
        id: int,
        chunk_count: int,
        word_count: Optional[int] = None
    ) -> bool:
        """
        Mark document as completed.

        Args:
            db: Database session
            id: Document ID
            chunk_count: Number of chunks created
            word_count: Word count if available

        Returns:
            True if successful
        """
        document = await self.get(db, id)
        if not document:
            return False

        document.mark_completed(chunk_count, word_count)
        await db.flush()
        return True

    async def mark_failed(
        self,
        db: AsyncSession,
        id: int,
        error_message: str
    ) -> bool:
        """
        Mark document as failed.

        Args:
            db: Database session
            id: Document ID
            error_message: Error description

        Returns:
            True if successful
        """
        document = await self.get(db, id)
        if not document:
            return False

        document.mark_failed(error_message)
        await db.flush()
        return True

    async def soft_delete(self, db: AsyncSession, id: int) -> bool:
        """
        Soft delete a document.

        Args:
            db: Database session
            id: Document ID

        Returns:
            True if deleted, False if not found
        """
        document = await self.get(db, id)
        if not document:
            return False

        document.soft_delete()
        await db.flush()
        return True


# Create instance
document = CRUDDocument(Document)
