"""
Chat service for managing conversations and messages.

This service handles:
- Chat session creation and management
- Message persistence and retrieval
- Conversation history management
- Integration with RAG pipeline for responses
- Chat title generation
"""

import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from sqlalchemy.orm import selectinload

from models.chat import Chat
from models.message import Message, MessageRole
from models.project import Project
from core.rag_pipeline import RAGPipeline, RAGResponse
from core.database import get_db

logger = logging.getLogger(__name__)


class ChatServiceError(Exception):
    """Raised when chat service operations fail."""
    pass


class ChatService:
    """
    Service for managing chat conversations and messages.

    Provides CRUD operations for chats, message management,
    and integration with RAG pipeline for generating responses.
    """

    def __init__(self, rag_pipeline: Optional[RAGPipeline] = None):
        """
        Initialize chat service.

        Args:
            rag_pipeline: RAG pipeline instance (optional, creates default if not provided)
        """
        self.rag_pipeline = rag_pipeline or RAGPipeline()
        logger.info("ChatService initialized")

    async def create_chat(
        self,
        db: AsyncSession,
        project_id: int,
        title: Optional[str] = None
    ) -> Chat:
        """
        Create a new chat session.

        Args:
            db: Database session
            project_id: ID of the project this chat belongs to
            title: Optional chat title (defaults to "New Chat")

        Returns:
            Created chat object

        Raises:
            ChatServiceError: If chat creation fails
        """
        try:
            # Verify project exists
            result = await db.execute(
                select(Project).where(Project.id == project_id)
            )
            project = result.scalar_one_or_none()

            if not project:
                raise ChatServiceError(f"Project {project_id} not found")

            # Create chat
            chat = Chat(
                project_id=project_id,
                title=title or "New Chat",
                message_count=0
            )

            db.add(chat)
            await db.commit()
            await db.refresh(chat)

            logger.info(f"Created chat {chat.id} in project {project_id}")
            return chat

        except ChatServiceError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create chat: {str(e)}")
            raise ChatServiceError(f"Failed to create chat: {str(e)}") from e

    async def get_chat(
        self,
        db: AsyncSession,
        chat_id: int,
        include_messages: bool = True
    ) -> Optional[Chat]:
        """
        Get a chat by ID.

        Args:
            db: Database session
            chat_id: Chat ID
            include_messages: Whether to load messages (default: True)

        Returns:
            Chat object or None if not found
        """
        try:
            query = select(Chat).where(Chat.id == chat_id)

            if include_messages:
                query = query.options(selectinload(Chat.messages))

            result = await db.execute(query)
            chat = result.scalar_one_or_none()

            if chat:
                logger.debug(f"Retrieved chat {chat_id} with {len(chat.messages)} messages")

            return chat

        except Exception as e:
            logger.error(f"Failed to get chat {chat_id}: {str(e)}")
            return None

    async def list_chats(
        self,
        db: AsyncSession,
        project_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Chat]:
        """
        List chats for a project.

        Args:
            db: Database session
            project_id: Project ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of chat objects
        """
        try:
            query = (
                select(Chat)
                .where(Chat.project_id == project_id)
                .order_by(Chat.updated_at.desc())
                .offset(skip)
                .limit(limit)
            )

            result = await db.execute(query)
            chats = result.scalars().all()

            logger.info(f"Retrieved {len(chats)} chats for project {project_id}")
            return list(chats)

        except Exception as e:
            logger.error(f"Failed to list chats: {str(e)}")
            return []

    async def update_chat(
        self,
        db: AsyncSession,
        chat_id: int,
        title: Optional[str] = None
    ) -> Optional[Chat]:
        """
        Update a chat.

        Args:
            db: Database session
            chat_id: Chat ID
            title: New title (optional)

        Returns:
            Updated chat or None if not found

        Raises:
            ChatServiceError: If update fails
        """
        try:
            chat = await self.get_chat(db, chat_id, include_messages=False)

            if not chat:
                return None

            if title is not None:
                chat.title = title

            await db.commit()
            await db.refresh(chat)

            logger.info(f"Updated chat {chat_id}")
            return chat

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to update chat {chat_id}: {str(e)}")
            raise ChatServiceError(f"Failed to update chat: {str(e)}") from e

    async def delete_chat(
        self,
        db: AsyncSession,
        chat_id: int
    ) -> bool:
        """
        Delete a chat (soft delete).

        Args:
            db: Database session
            chat_id: Chat ID

        Returns:
            True if deleted, False if not found
        """
        try:
            chat = await self.get_chat(db, chat_id, include_messages=False)

            if not chat:
                return False

            # Soft delete
            chat.deleted_at = datetime.utcnow()
            await db.commit()

            logger.info(f"Deleted chat {chat_id}")
            return True

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to delete chat {chat_id}: {str(e)}")
            return False

    async def add_message(
        self,
        db: AsyncSession,
        chat_id: int,
        role: MessageRole,
        content: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        model_name: Optional[str] = None
    ) -> Message:
        """
        Add a message to a chat.

        Args:
            db: Database session
            chat_id: Chat ID
            role: Message role (user, assistant, system)
            content: Message content
            sources: Optional source references
            model_name: Optional model name (for assistant messages)

        Returns:
            Created message

        Raises:
            ChatServiceError: If message creation fails
        """
        try:
            # Verify chat exists
            chat = await self.get_chat(db, chat_id, include_messages=False)

            if not chat:
                raise ChatServiceError(f"Chat {chat_id} not found")

            # Create message
            message = Message(
                chat_id=chat_id,
                role=role,
                content=content,
                model_name=model_name
            )

            # Set sources if provided
            if sources:
                message.set_sources(sources)

            db.add(message)

            # Update chat message count and title
            chat.increment_message_count()

            # Auto-generate title from first user message
            if chat.message_count == 1 and role == MessageRole.USER:
                chat.title = chat.generate_title(content)

            await db.commit()
            await db.refresh(message)

            logger.info(f"Added {role.value} message to chat {chat_id}")
            return message

        except ChatServiceError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to add message to chat {chat_id}: {str(e)}")
            raise ChatServiceError(f"Failed to add message: {str(e)}") from e

    async def get_chat_history(
        self,
        db: AsyncSession,
        chat_id: int,
        max_messages: Optional[int] = None
    ) -> List[Dict[str, str]]:
        """
        Get chat history formatted for LLM consumption.

        Args:
            db: Database session
            chat_id: Chat ID
            max_messages: Maximum number of messages to retrieve (most recent)

        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        try:
            chat = await self.get_chat(db, chat_id, include_messages=True)

            if not chat:
                return []

            messages = chat.messages

            # Filter out system messages (usually not needed in history)
            messages = [m for m in messages if m.role != MessageRole.SYSTEM]

            # Limit to max_messages if specified
            if max_messages and len(messages) > max_messages:
                messages = messages[-max_messages:]

            # Format for LLM
            history = [
                {
                    'role': msg.role.value,
                    'content': msg.content
                }
                for msg in messages
            ]

            logger.debug(f"Retrieved {len(history)} messages for chat {chat_id}")
            return history

        except Exception as e:
            logger.error(f"Failed to get chat history for {chat_id}: {str(e)}")
            return []

    async def send_message(
        self,
        db: AsyncSession,
        chat_id: int,
        user_message: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        include_history: bool = True,
        max_history: int = 5
    ) -> RAGResponse:
        """
        Send a user message and generate a response using RAG pipeline.

        Args:
            db: Database session
            chat_id: Chat ID
            user_message: User's message content
            model: LLM model to use (optional)
            temperature: Sampling temperature
            include_history: Whether to include conversation history
            max_history: Maximum history messages to include

        Returns:
            RAG response with answer and sources

        Raises:
            ChatServiceError: If message sending fails
        """
        try:
            # Get chat to verify it exists and get project_id
            chat = await self.get_chat(db, chat_id, include_messages=False)

            if not chat:
                raise ChatServiceError(f"Chat {chat_id} not found")

            # Add user message to database
            user_msg = await self.add_message(
                db=db,
                chat_id=chat_id,
                role=MessageRole.USER,
                content=user_message
            )

            # Get chat history if requested
            history = []
            if include_history:
                history = await self.get_chat_history(
                    db=db,
                    chat_id=chat_id,
                    max_messages=max_history
                )
                # Remove the just-added user message from history
                # (it will be in the current query)
                if history and history[-1]['role'] == 'user':
                    history = history[:-1]

            # Generate response using RAG pipeline
            rag_response = await self.rag_pipeline.generate_answer(
                query=user_message,
                project_id=chat.project_id,
                chat_history=history,
                model=model,
                temperature=temperature
            )

            # Add assistant message to database
            assistant_msg = await self.add_message(
                db=db,
                chat_id=chat_id,
                role=MessageRole.ASSISTANT,
                content=rag_response.answer,
                sources=[
                    {
                        'id': src.id,
                        'content': src.content,
                        'metadata': src.metadata,
                        'score': src.score
                    }
                    for src in rag_response.sources
                ],
                model_name=rag_response.model
            )

            logger.info(
                f"Generated response for chat {chat_id} "
                f"with {len(rag_response.sources)} sources"
            )

            return rag_response

        except ChatServiceError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to send message in chat {chat_id}: {str(e)}")
            raise ChatServiceError(f"Failed to send message: {str(e)}") from e

    async def send_message_stream(
        self,
        db: AsyncSession,
        chat_id: int,
        user_message: str,
        model: Optional[str] = None,
        temperature: float = 0.7,
        include_history: bool = True,
        max_history: int = 5
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Send a user message and stream the response.

        This method:
        1. Saves the user message
        2. Streams the RAG response
        3. Saves the assistant message after streaming completes

        Args:
            db: Database session
            chat_id: Chat ID
            user_message: User's message content
            model: LLM model to use (optional)
            temperature: Sampling temperature
            include_history: Whether to include conversation history
            max_history: Maximum history messages to include

        Yields:
            Stream events from RAG pipeline

        Raises:
            ChatServiceError: If message sending fails
        """
        try:
            # Get chat to verify it exists and get project_id
            chat = await self.get_chat(db, chat_id, include_messages=False)

            if not chat:
                raise ChatServiceError(f"Chat {chat_id} not found")

            # Add user message to database
            user_msg = await self.add_message(
                db=db,
                chat_id=chat_id,
                role=MessageRole.USER,
                content=user_message
            )

            # Get chat history if requested
            history = []
            if include_history:
                history = await self.get_chat_history(
                    db=db,
                    chat_id=chat_id,
                    max_messages=max_history
                )
                # Remove the just-added user message from history
                if history and history[-1]['role'] == 'user':
                    history = history[:-1]

            # Stream response using RAG pipeline
            accumulated_answer = ""
            sources = []
            model_name = model or self.rag_pipeline.llm_client.default_model

            async for event in self.rag_pipeline.generate_answer_stream(
                query=user_message,
                project_id=chat.project_id,
                chat_history=history,
                model=model,
                temperature=temperature
            ):
                # Forward event to caller
                yield event

                # Accumulate data for database storage
                if event['type'] == 'sources':
                    sources = event['data']
                elif event['type'] == 'token':
                    accumulated_answer += event['data']
                elif event['type'] == 'done':
                    model_name = event['data']['model']

            # Save complete assistant message to database
            if accumulated_answer:
                assistant_msg = await self.add_message(
                    db=db,
                    chat_id=chat_id,
                    role=MessageRole.ASSISTANT,
                    content=accumulated_answer,
                    sources=sources,
                    model_name=model_name
                )

                logger.info(
                    f"Saved streamed response for chat {chat_id} "
                    f"with {len(sources)} sources"
                )

        except ChatServiceError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to stream message in chat {chat_id}: {str(e)}")
            # Yield error event
            yield {
                'type': 'error',
                'data': str(e)
            }
            raise ChatServiceError(f"Failed to stream message: {str(e)}") from e

    async def get_message_count(
        self,
        db: AsyncSession,
        chat_id: int
    ) -> int:
        """
        Get the number of messages in a chat.

        Args:
            db: Database session
            chat_id: Chat ID

        Returns:
            Number of messages
        """
        try:
            result = await db.execute(
                select(func.count(Message.id)).where(Message.chat_id == chat_id)
            )
            count = result.scalar_one()
            return count

        except Exception as e:
            logger.error(f"Failed to get message count for chat {chat_id}: {str(e)}")
            return 0

    async def search_chats(
        self,
        db: AsyncSession,
        project_id: int,
        query: str,
        limit: int = 20
    ) -> List[Chat]:
        """
        Search for chats by title or message content.

        Args:
            db: Database session
            project_id: Project ID
            query: Search query
            limit: Maximum results to return

        Returns:
            List of matching chats
        """
        try:
            # Search by title or message content
            search_pattern = f"%{query}%"

            stmt = (
                select(Chat)
                .where(
                    and_(
                        Chat.project_id == project_id,
                        Chat.title.ilike(search_pattern)
                    )
                )
                .order_by(Chat.updated_at.desc())
                .limit(limit)
            )

            result = await db.execute(stmt)
            chats = result.scalars().all()

            logger.info(f"Found {len(chats)} chats matching '{query}'")
            return list(chats)

        except Exception as e:
            logger.error(f"Failed to search chats: {str(e)}")
            return []


# Global chat service instance
chat_service = ChatService()
