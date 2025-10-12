"""
Chat API routes.

Endpoints:
- POST /api/chats - Create a new chat
- GET /api/chats/{chat_id} - Get chat details
- PUT /api/chats/{chat_id} - Update chat
- DELETE /api/chats/{chat_id} - Delete chat
- GET /api/projects/{project_id}/chats - List chats for a project
- POST /api/chats/{chat_id}/messages - Send a message and get response
- GET /api/chats/{chat_id}/messages - Get message history
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import json

from core.database import get_db
from services.chat_service import chat_service, ChatServiceError
from models.message import MessageRole

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


# Request/Response Models
class CreateChatRequest(BaseModel):
    """Request model for creating a chat."""
    project_id: int = Field(..., description="ID of the project")
    title: Optional[str] = Field(None, description="Chat title (optional)")


class UpdateChatRequest(BaseModel):
    """Request model for updating a chat."""
    title: str = Field(..., description="New chat title")


class SendMessageRequest(BaseModel):
    """Request model for sending a message."""
    message: str = Field(..., description="User message content")
    model: Optional[str] = Field(None, description="LLM model to use (optional)")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="Sampling temperature")
    include_history: bool = Field(True, description="Include conversation history")
    max_history: int = Field(5, ge=1, le=20, description="Maximum history messages")
    stream: bool = Field(False, description="Stream the response")


class MessageResponse(BaseModel):
    """Response model for a single message."""
    id: int
    chat_id: int
    role: str
    content: str
    sources: Optional[List[dict]] = None
    model_name: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


class SourceDocument(BaseModel):
    """Source document reference."""
    id: str
    content: str
    metadata: dict
    score: float


class ChatResponse(BaseModel):
    """Response model for chat details."""
    id: int
    project_id: int
    title: str
    message_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class ChatResponseWithMessages(ChatResponse):
    """Chat response including messages."""
    messages: List[MessageResponse]


class RAGAnswerResponse(BaseModel):
    """Response model for RAG answer."""
    answer: str
    sources: List[SourceDocument]
    model: str
    message_id: Optional[int] = None


# Endpoints

@router.post("/chats", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def create_chat(
    request: CreateChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new chat session.

    Args:
        request: Chat creation request
        db: Database session

    Returns:
        Created chat details

    Raises:
        HTTPException: If chat creation fails
    """
    try:
        chat = await chat_service.create_chat(
            db=db,
            project_id=request.project_id,
            title=request.title
        )

        return ChatResponse(
            id=chat.id,
            project_id=chat.project_id,
            title=chat.title,
            message_count=chat.message_count,
            created_at=chat.created_at.isoformat(),
            updated_at=chat.updated_at.isoformat()
        )

    except ChatServiceError as e:
        logger.error(f"Chat creation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/chats/{chat_id}", response_model=ChatResponseWithMessages)
async def get_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get chat details including messages.

    Args:
        chat_id: Chat ID
        db: Database session

    Returns:
        Chat details with messages

    Raises:
        HTTPException: If chat not found
    """
    chat = await chat_service.get_chat(db, chat_id, include_messages=True)

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat {chat_id} not found"
        )

    messages = [
        MessageResponse(
            id=msg.id,
            chat_id=msg.chat_id,
            role=msg.role.value,
            content=msg.content,
            sources=msg.get_sources() if msg.has_sources else None,
            model_name=msg.model_name,
            created_at=msg.created_at.isoformat()
        )
        for msg in chat.messages
    ]

    return ChatResponseWithMessages(
        id=chat.id,
        project_id=chat.project_id,
        title=chat.title,
        message_count=chat.message_count,
        created_at=chat.created_at.isoformat(),
        updated_at=chat.updated_at.isoformat(),
        messages=messages
    )


@router.put("/chats/{chat_id}", response_model=ChatResponse)
async def update_chat(
    chat_id: int,
    request: UpdateChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Update chat details.

    Args:
        chat_id: Chat ID
        request: Update request
        db: Database session

    Returns:
        Updated chat details

    Raises:
        HTTPException: If chat not found or update fails
    """
    try:
        chat = await chat_service.update_chat(
            db=db,
            chat_id=chat_id,
            title=request.title
        )

        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chat {chat_id} not found"
            )

        return ChatResponse(
            id=chat.id,
            project_id=chat.project_id,
            title=chat.title,
            message_count=chat.message_count,
            created_at=chat.created_at.isoformat(),
            updated_at=chat.updated_at.isoformat()
        )

    except ChatServiceError as e:
        logger.error(f"Chat update failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat(
    chat_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a chat (soft delete).

    Args:
        chat_id: Chat ID
        db: Database session

    Raises:
        HTTPException: If chat not found
    """
    success = await chat_service.delete_chat(db, chat_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat {chat_id} not found"
        )


@router.get("/projects/{project_id}/chats", response_model=List[ChatResponse])
async def list_chats(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List chats for a project.

    Args:
        project_id: Project ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session

    Returns:
        List of chats
    """
    chats = await chat_service.list_chats(
        db=db,
        project_id=project_id,
        skip=skip,
        limit=limit
    )

    return [
        ChatResponse(
            id=chat.id,
            project_id=chat.project_id,
            title=chat.title,
            message_count=chat.message_count,
            created_at=chat.created_at.isoformat(),
            updated_at=chat.updated_at.isoformat()
        )
        for chat in chats
    ]


@router.post("/chats/{chat_id}/messages", response_model=RAGAnswerResponse)
async def send_message(
    chat_id: int,
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message and get RAG response.

    Supports both streaming and non-streaming responses based on the 'stream' parameter.

    Args:
        chat_id: Chat ID
        request: Message request
        db: Database session

    Returns:
        RAG answer with sources (non-streaming) or StreamingResponse (streaming)

    Raises:
        HTTPException: If chat not found or message sending fails
    """
    try:
        # Handle streaming response
        if request.stream:
            async def stream_generator():
                """Generate streaming response."""
                try:
                    async for event in chat_service.send_message_stream(
                        db=db,
                        chat_id=chat_id,
                        user_message=request.message,
                        model=request.model,
                        temperature=request.temperature,
                        include_history=request.include_history,
                        max_history=request.max_history
                    ):
                        # Send events as Server-Sent Events format
                        yield f"data: {json.dumps(event)}\n\n"

                    # Send final done event
                    yield "data: {\"type\": \"complete\"}\n\n"

                except Exception as e:
                    error_event = {
                        'type': 'error',
                        'data': str(e)
                    }
                    yield f"data: {json.dumps(error_event)}\n\n"

            return StreamingResponse(
                stream_generator(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )

        # Handle non-streaming response
        else:
            rag_response = await chat_service.send_message(
                db=db,
                chat_id=chat_id,
                user_message=request.message,
                model=request.model,
                temperature=request.temperature,
                include_history=request.include_history,
                max_history=request.max_history
            )

            return RAGAnswerResponse(
                answer=rag_response.answer,
                sources=[
                    SourceDocument(
                        id=src.id,
                        content=src.content,
                        metadata=src.metadata,
                        score=src.score
                    )
                    for src in rag_response.sources
                ],
                model=rag_response.model
            )

    except ChatServiceError as e:
        logger.error(f"Message sending failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/chats/{chat_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    chat_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get message history for a chat.

    Args:
        chat_id: Chat ID
        db: Database session

    Returns:
        List of messages

    Raises:
        HTTPException: If chat not found
    """
    chat = await chat_service.get_chat(db, chat_id, include_messages=True)

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat {chat_id} not found"
        )

    return [
        MessageResponse(
            id=msg.id,
            chat_id=msg.chat_id,
            role=msg.role.value,
            content=msg.content,
            sources=msg.get_sources() if msg.has_sources else None,
            model_name=msg.model_name,
            created_at=msg.created_at.isoformat()
        )
        for msg in chat.messages
    ]


@router.get("/projects/{project_id}/chats/search", response_model=List[ChatResponse])
async def search_chats(
    project_id: int,
    q: str,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Search chats by title or content.

    Args:
        project_id: Project ID
        q: Search query
        limit: Maximum results
        db: Database session

    Returns:
        List of matching chats
    """
    chats = await chat_service.search_chats(
        db=db,
        project_id=project_id,
        query=q,
        limit=limit
    )

    return [
        ChatResponse(
            id=chat.id,
            project_id=chat.project_id,
            title=chat.title,
            message_count=chat.message_count,
            created_at=chat.created_at.isoformat(),
            updated_at=chat.updated_at.isoformat()
        )
        for chat in chats
    ]
