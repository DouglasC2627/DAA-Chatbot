"""
CRUD operations for Message model.
"""
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Message, MessageRole
from crud.base import CRUDBase


class CRUDMessage(CRUDBase[Message]):
    """CRUD operations for Message model."""

    async def get_by_chat(
        self,
        db: AsyncSession,
        chat_id: int,
        *,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """
        Get messages for a specific chat.

        Args:
            db: Database session
            chat_id: Chat ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of messages ordered by creation time
        """
        result = await db.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.asc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent(
        self,
        db: AsyncSession,
        chat_id: int,
        limit: int = 10
    ) -> List[Message]:
        """
        Get recent messages from a chat.

        Args:
            db: Database session
            chat_id: Chat ID
            limit: Maximum number of messages to return

        Returns:
            List of recent messages
        """
        result = await db.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        # Reverse to get chronological order
        return list(reversed(result.scalars().all()))

    async def create_user_message(
        self,
        db: AsyncSession,
        chat_id: int,
        content: str
    ) -> Message:
        """
        Create a user message.

        Args:
            db: Database session
            chat_id: Chat ID
            content: Message content

        Returns:
            Created message
        """
        return await self.create(db, obj_in={
            "chat_id": chat_id,
            "role": MessageRole.USER,
            "content": content
        })

    async def create_assistant_message(
        self,
        db: AsyncSession,
        chat_id: int,
        content: str,
        model_name: str,
        sources: Optional[List[dict]] = None,
        token_count: Optional[int] = None
    ) -> Message:
        """
        Create an assistant message.

        Args:
            db: Database session
            chat_id: Chat ID
            content: Message content
            model_name: LLM model name
            sources: Optional source references
            token_count: Optional token count

        Returns:
            Created message
        """
        message = await self.create(db, obj_in={
            "chat_id": chat_id,
            "role": MessageRole.ASSISTANT,
            "content": content,
            "model_name": model_name,
            "token_count": token_count
        })

        if sources:
            message.set_sources(sources)
            await db.flush()

        return message

    async def get_by_role(
        self,
        db: AsyncSession,
        chat_id: int,
        role: MessageRole
    ) -> List[Message]:
        """
        Get messages by role for a chat.

        Args:
            db: Database session
            chat_id: Chat ID
            role: Message role

        Returns:
            List of messages
        """
        result = await db.execute(
            select(Message)
            .where(Message.chat_id == chat_id)
            .where(Message.role == role)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())


# Create instance
message = CRUDMessage(Message)
