"""
CRUD operations for Chat model.
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Chat
from crud.base import CRUDBase


class CRUDChat(CRUDBase[Chat]):
    """CRUD operations for Chat model."""

    async def get_by_project(
        self,
        db: AsyncSession,
        project_id: int,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Chat]:
        """
        Get chats for a specific project.

        Args:
            db: Database session
            project_id: Project ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of chats
        """
        result = await db.execute(
            select(Chat)
            .where(Chat.project_id == project_id)
            .where(Chat.deleted_at.is_(None))
            .order_by(Chat.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_messages(
        self,
        db: AsyncSession,
        id: int
    ) -> Optional[Chat]:
        """
        Get chat with all messages loaded.

        Args:
            db: Database session
            id: Chat ID

        Returns:
            Chat instance with messages
        """
        result = await db.execute(
            select(Chat).where(Chat.id == id)
        )
        return result.scalar_one_or_none()

    async def update_title(
        self,
        db: AsyncSession,
        id: int,
        title: str
    ) -> bool:
        """
        Update chat title.

        Args:
            db: Database session
            id: Chat ID
            title: New title

        Returns:
            True if successful
        """
        chat = await self.get(db, id)
        if not chat:
            return False

        chat.title = title
        await db.flush()
        return True

    async def increment_message_count(
        self,
        db: AsyncSession,
        id: int
    ) -> bool:
        """
        Increment message count.

        Args:
            db: Database session
            id: Chat ID

        Returns:
            True if successful
        """
        chat = await self.get(db, id)
        if not chat:
            return False

        chat.increment_message_count()
        await db.flush()
        return True

    async def soft_delete(self, db: AsyncSession, id: int) -> bool:
        """
        Soft delete a chat.

        Args:
            db: Database session
            id: Chat ID

        Returns:
            True if deleted, False if not found
        """
        chat = await self.get(db, id)
        if not chat:
            return False

        chat.soft_delete()
        await db.flush()
        return True


# Create instance
chat = CRUDChat(Chat)
