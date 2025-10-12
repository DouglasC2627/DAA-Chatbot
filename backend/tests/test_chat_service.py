"""
Tests for Chat Service.

This test suite tests:
- Chat CRUD operations (create, read, update, delete, list)
- Message management (add, retrieve, history)
- Context window management
- Conversation memory
- RAG pipeline integration
- Response streaming
- Search functionality
"""

import pytest
import sys
import os
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.chat_service import ChatService, ChatServiceError
from models.chat import Chat
from models.message import Message, MessageRole
from models.project import Project
from core.rag_pipeline import RAGPipeline, RAGResponse, RetrievedDocument
from core.database import SessionLocal


@pytest.fixture
async def db_session():
    """Create a test database session."""
    async with SessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def test_project(db_session):
    """Create a test project."""
    project = Project(
        name="Test Project",
        description="Test project for chat service tests"
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    yield project

    # Cleanup
    await db_session.delete(project)
    await db_session.commit()


@pytest.fixture
def mock_rag_pipeline():
    """Create a mock RAG pipeline."""
    mock_pipeline = Mock(spec=RAGPipeline)

    # Mock generate_answer to return a RAG response
    mock_response = RAGResponse(
        answer="This is a test answer from the RAG pipeline.",
        sources=[
            RetrievedDocument(
                id="test_chunk_1",
                content="Test source content",
                metadata={'document_id': 1, 'chunk_index': 0},
                distance=0.2
            )
        ],
        model="llama3.2"
    )
    mock_pipeline.generate_answer = AsyncMock(return_value=mock_response)

    # Mock streaming response
    async def mock_stream():
        yield {'type': 'sources', 'data': [{'id': 'test', 'content': 'test', 'metadata': {}, 'score': 0.9}]}
        yield {'type': 'token', 'data': 'Test '}
        yield {'type': 'token', 'data': 'streaming '}
        yield {'type': 'token', 'data': 'response'}
        yield {'type': 'done', 'data': {'model': 'llama3.2', 'sources_count': 1}}

    mock_pipeline.generate_answer_stream = Mock(return_value=mock_stream())
    mock_pipeline.llm_client = Mock()
    mock_pipeline.llm_client.default_model = "llama3.2"

    return mock_pipeline


@pytest.fixture
def chat_service(mock_rag_pipeline):
    """Create a chat service with mocked RAG pipeline."""
    return ChatService(rag_pipeline=mock_rag_pipeline)


class TestChatCRUD:
    """Test chat CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_chat(self, chat_service, db_session, test_project):
        """Test creating a new chat."""
        chat = await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id,
            title="Test Chat"
        )

        assert chat is not None
        assert chat.id is not None
        assert chat.project_id == test_project.id
        assert chat.title == "Test Chat"
        assert chat.message_count == 0

    @pytest.mark.asyncio
    async def test_create_chat_default_title(self, chat_service, db_session, test_project):
        """Test creating a chat with default title."""
        chat = await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id
        )

        assert chat.title == "New Chat"

    @pytest.mark.asyncio
    async def test_create_chat_nonexistent_project(self, chat_service, db_session):
        """Test creating a chat for non-existent project."""
        with pytest.raises(ChatServiceError) as exc_info:
            await chat_service.create_chat(
                db=db_session,
                project_id=99999
            )

        assert "not found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_get_chat(self, chat_service, db_session, test_project):
        """Test retrieving a chat by ID."""
        # Create chat
        created_chat = await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id,
            title="Test Chat"
        )

        # Retrieve chat
        retrieved_chat = await chat_service.get_chat(
            db=db_session,
            chat_id=created_chat.id
        )

        assert retrieved_chat is not None
        assert retrieved_chat.id == created_chat.id
        assert retrieved_chat.title == created_chat.title

    @pytest.mark.asyncio
    async def test_get_chat_not_found(self, chat_service, db_session):
        """Test retrieving non-existent chat."""
        chat = await chat_service.get_chat(
            db=db_session,
            chat_id=99999
        )

        assert chat is None

    @pytest.mark.asyncio
    async def test_get_chat_without_messages(self, chat_service, db_session, test_project):
        """Test retrieving chat without loading messages."""
        created_chat = await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id
        )

        retrieved_chat = await chat_service.get_chat(
            db=db_session,
            chat_id=created_chat.id,
            include_messages=False
        )

        assert retrieved_chat is not None
        # Messages should not be loaded
        assert not hasattr(retrieved_chat, 'messages') or retrieved_chat.messages == []

    @pytest.mark.asyncio
    async def test_update_chat(self, chat_service, db_session, test_project):
        """Test updating a chat title."""
        chat = await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id,
            title="Original Title"
        )

        updated_chat = await chat_service.update_chat(
            db=db_session,
            chat_id=chat.id,
            title="Updated Title"
        )

        assert updated_chat is not None
        assert updated_chat.title == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_chat_not_found(self, chat_service, db_session):
        """Test updating non-existent chat."""
        result = await chat_service.update_chat(
            db=db_session,
            chat_id=99999,
            title="New Title"
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_delete_chat(self, chat_service, db_session, test_project):
        """Test deleting a chat (soft delete)."""
        chat = await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id
        )

        success = await chat_service.delete_chat(
            db=db_session,
            chat_id=chat.id
        )

        assert success is True

        # Verify chat is soft deleted
        deleted_chat = await chat_service.get_chat(db_session, chat.id)
        assert deleted_chat.deleted_at is not None

    @pytest.mark.asyncio
    async def test_delete_chat_not_found(self, chat_service, db_session):
        """Test deleting non-existent chat."""
        success = await chat_service.delete_chat(
            db=db_session,
            chat_id=99999
        )

        assert success is False

    @pytest.mark.asyncio
    async def test_list_chats(self, chat_service, db_session, test_project):
        """Test listing chats for a project."""
        # Create multiple chats
        for i in range(3):
            await chat_service.create_chat(
                db=db_session,
                project_id=test_project.id,
                title=f"Chat {i+1}"
            )

        chats = await chat_service.list_chats(
            db=db_session,
            project_id=test_project.id
        )

        assert len(chats) == 3

    @pytest.mark.asyncio
    async def test_list_chats_with_pagination(self, chat_service, db_session, test_project):
        """Test listing chats with pagination."""
        # Create 5 chats
        for i in range(5):
            await chat_service.create_chat(
                db=db_session,
                project_id=test_project.id,
                title=f"Chat {i+1}"
            )

        # Get first 2
        first_page = await chat_service.list_chats(
            db=db_session,
            project_id=test_project.id,
            skip=0,
            limit=2
        )

        assert len(first_page) == 2

        # Get next 2
        second_page = await chat_service.list_chats(
            db=db_session,
            project_id=test_project.id,
            skip=2,
            limit=2
        )

        assert len(second_page) == 2


class TestMessageManagement:
    """Test message management operations."""

    @pytest.mark.asyncio
    async def test_add_user_message(self, chat_service, db_session, test_project):
        """Test adding a user message."""
        chat = await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id
        )

        message = await chat_service.add_message(
            db=db_session,
            chat_id=chat.id,
            role=MessageRole.USER,
            content="Hello, this is a test message"
        )

        assert message is not None
        assert message.chat_id == chat.id
        assert message.role == MessageRole.USER
        assert message.content == "Hello, this is a test message"

    @pytest.mark.asyncio
    async def test_add_assistant_message_with_sources(self, chat_service, db_session, test_project):
        """Test adding an assistant message with sources."""
        chat = await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id
        )

        sources = [
            {
                'id': 'chunk1',
                'content': 'Source content',
                'metadata': {'document_id': 1},
                'score': 0.95
            }
        ]

        message = await chat_service.add_message(
            db=db_session,
            chat_id=chat.id,
            role=MessageRole.ASSISTANT,
            content="This is the answer",
            sources=sources,
            model_name="llama3.2"
        )

        assert message.model_name == "llama3.2"
        assert message.has_sources is True

    @pytest.mark.asyncio
    async def test_add_message_to_nonexistent_chat(self, chat_service, db_session):
        """Test adding message to non-existent chat."""
        with pytest.raises(ChatServiceError):
            await chat_service.add_message(
                db=db_session,
                chat_id=99999,
                role=MessageRole.USER,
                content="Test"
            )

    @pytest.mark.asyncio
    async def test_message_count_increments(self, chat_service, db_session, test_project):
        """Test that message count increments correctly."""
        chat = await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id
        )

        assert chat.message_count == 0

        # Add first message
        await chat_service.add_message(
            db=db_session,
            chat_id=chat.id,
            role=MessageRole.USER,
            content="Message 1"
        )

        # Refresh and check
        updated_chat = await chat_service.get_chat(db_session, chat.id)
        assert updated_chat.message_count == 1

        # Add second message
        await chat_service.add_message(
            db=db_session,
            chat_id=chat.id,
            role=MessageRole.ASSISTANT,
            content="Response 1"
        )

        updated_chat = await chat_service.get_chat(db_session, chat.id)
        assert updated_chat.message_count == 2

    @pytest.mark.asyncio
    async def test_auto_title_generation(self, chat_service, db_session, test_project):
        """Test automatic title generation from first message."""
        chat = await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id
        )

        assert chat.title == "New Chat"

        # Add first message
        await chat_service.add_message(
            db=db_session,
            chat_id=chat.id,
            role=MessageRole.USER,
            content="What is machine learning and how does it work?"
        )

        # Check title was auto-generated
        updated_chat = await chat_service.get_chat(db_session, chat.id)
        assert updated_chat.title != "New Chat"
        assert len(updated_chat.title) > 0


class TestChatHistory:
    """Test chat history management."""

    @pytest.mark.asyncio
    async def test_get_chat_history(self, chat_service, db_session, test_project):
        """Test retrieving chat history."""
        chat = await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id
        )

        # Add messages
        await chat_service.add_message(
            db=db_session,
            chat_id=chat.id,
            role=MessageRole.USER,
            content="Question 1"
        )
        await chat_service.add_message(
            db=db_session,
            chat_id=chat.id,
            role=MessageRole.ASSISTANT,
            content="Answer 1"
        )

        history = await chat_service.get_chat_history(
            db=db_session,
            chat_id=chat.id
        )

        assert len(history) == 2
        assert history[0]['role'] == 'user'
        assert history[0]['content'] == "Question 1"
        assert history[1]['role'] == 'assistant'
        assert history[1]['content'] == "Answer 1"

    @pytest.mark.asyncio
    async def test_get_chat_history_with_limit(self, chat_service, db_session, test_project):
        """Test retrieving limited chat history."""
        chat = await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id
        )

        # Add 5 messages
        for i in range(5):
            await chat_service.add_message(
                db=db_session,
                chat_id=chat.id,
                role=MessageRole.USER,
                content=f"Message {i+1}"
            )

        # Get only last 3
        history = await chat_service.get_chat_history(
            db=db_session,
            chat_id=chat.id,
            max_messages=3
        )

        assert len(history) == 3
        # Should be most recent messages
        assert history[-1]['content'] == "Message 5"

    @pytest.mark.asyncio
    async def test_get_chat_history_filters_system_messages(self, chat_service, db_session, test_project):
        """Test that system messages are filtered from history."""
        chat = await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id
        )

        # Add messages including system message
        await chat_service.add_message(
            db=db_session,
            chat_id=chat.id,
            role=MessageRole.USER,
            content="User message"
        )
        await chat_service.add_message(
            db=db_session,
            chat_id=chat.id,
            role=MessageRole.SYSTEM,
            content="System message"
        )
        await chat_service.add_message(
            db=db_session,
            chat_id=chat.id,
            role=MessageRole.ASSISTANT,
            content="Assistant message"
        )

        history = await chat_service.get_chat_history(
            db=db_session,
            chat_id=chat.id
        )

        # System message should be filtered out
        assert len(history) == 2
        assert all(msg['role'] != 'system' for msg in history)

    @pytest.mark.asyncio
    async def test_get_message_count(self, chat_service, db_session, test_project):
        """Test getting message count for a chat."""
        chat = await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id
        )

        # Add messages
        for i in range(3):
            await chat_service.add_message(
                db=db_session,
                chat_id=chat.id,
                role=MessageRole.USER,
                content=f"Message {i+1}"
            )

        count = await chat_service.get_message_count(
            db=db_session,
            chat_id=chat.id
        )

        assert count == 3


class TestRAGIntegration:
    """Test RAG pipeline integration."""

    @pytest.mark.asyncio
    async def test_send_message(self, chat_service, db_session, test_project):
        """Test sending a message and getting RAG response."""
        chat = await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id
        )

        response = await chat_service.send_message(
            db=db_session,
            chat_id=chat.id,
            user_message="What is machine learning?"
        )

        assert response is not None
        assert isinstance(response, RAGResponse)
        assert len(response.answer) > 0
        assert len(response.sources) > 0
        assert response.model == "llama3.2"

        # Verify messages were saved
        updated_chat = await chat_service.get_chat(db_session, chat.id, include_messages=True)
        assert updated_chat.message_count == 2  # User + Assistant

    @pytest.mark.asyncio
    async def test_send_message_with_history(self, chat_service, db_session, test_project):
        """Test sending message with conversation history."""
        chat = await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id
        )

        # Send first message
        await chat_service.send_message(
            db=db_session,
            chat_id=chat.id,
            user_message="What is Python?"
        )

        # Send second message (should include history)
        response = await chat_service.send_message(
            db=db_session,
            chat_id=chat.id,
            user_message="Tell me more about it",
            include_history=True,
            max_history=5
        )

        assert response is not None
        # RAG pipeline should have been called with history
        chat_service.rag_pipeline.generate_answer.assert_called()

    @pytest.mark.asyncio
    async def test_send_message_stream(self, chat_service, db_session, test_project):
        """Test streaming message response."""
        chat = await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id
        )

        events = []
        async for event in chat_service.send_message_stream(
            db=db_session,
            chat_id=chat.id,
            user_message="What is AI?"
        ):
            events.append(event)

        # Verify we got streaming events
        assert len(events) > 0

        # Check event types
        event_types = [e['type'] for e in events]
        assert 'sources' in event_types
        assert 'token' in event_types
        assert 'done' in event_types

        # Verify messages were saved
        updated_chat = await chat_service.get_chat(db_session, chat.id)
        assert updated_chat.message_count == 2


class TestSearchFunctionality:
    """Test chat search functionality."""

    @pytest.mark.asyncio
    async def test_search_chats_by_title(self, chat_service, db_session, test_project):
        """Test searching chats by title."""
        # Create chats with different titles
        await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id,
            title="Python Tutorial"
        )
        await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id,
            title="JavaScript Guide"
        )
        await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id,
            title="Python Best Practices"
        )

        # Search for Python
        results = await chat_service.search_chats(
            db=db_session,
            project_id=test_project.id,
            query="Python"
        )

        assert len(results) == 2
        assert all('Python' in chat.title for chat in results)

    @pytest.mark.asyncio
    async def test_search_chats_case_insensitive(self, chat_service, db_session, test_project):
        """Test that search is case-insensitive."""
        await chat_service.create_chat(
            db=db_session,
            project_id=test_project.id,
            title="Machine Learning Basics"
        )

        results = await chat_service.search_chats(
            db=db_session,
            project_id=test_project.id,
            query="machine"  # lowercase
        )

        assert len(results) == 1

    @pytest.mark.asyncio
    async def test_search_chats_with_limit(self, chat_service, db_session, test_project):
        """Test search with result limit."""
        # Create multiple matching chats
        for i in range(5):
            await chat_service.create_chat(
                db=db_session,
                project_id=test_project.id,
                title=f"Test Chat {i+1}"
            )

        results = await chat_service.search_chats(
            db=db_session,
            project_id=test_project.id,
            query="Test",
            limit=3
        )

        assert len(results) == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
