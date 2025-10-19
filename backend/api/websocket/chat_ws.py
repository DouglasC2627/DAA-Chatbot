"""
WebSocket handler for real-time chat functionality.

This module provides WebSocket support for:
- Real-time message streaming
- Live response generation
- Connection management per project
- Error handling and reconnection support
"""

import logging
import asyncio
from typing import Dict, Any, Optional
import socketio

from services.chat_service import ChatService, ChatServiceError
from core.database import get_db
from core.rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)

# Create Socket.IO async server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',  # TODO: Configure based on environment
    logger=True,
    engineio_logger=True
)

# Store active connections and their metadata
active_connections: Dict[str, Dict[str, Any]] = {}

# Initialize services
chat_service = ChatService(rag_pipeline=RAGPipeline())


@sio.event
async def connect(sid: str, environ: Dict[str, Any], auth: Optional[Dict[str, Any]] = None):
    """
    Handle client connection.

    Args:
        sid: Socket session ID
        environ: ASGI environment dict
        auth: Optional authentication data

    Returns:
        True to accept connection, False to reject
    """
    try:
        logger.info(f"Client connecting: {sid}")

        # TODO: Implement authentication
        # For now, accept all connections
        # In production, validate auth token here:
        # if not auth or 'token' not in auth:
        #     logger.warning(f"Rejected connection from {sid}: No auth token")
        #     return False

        # Store connection metadata
        active_connections[sid] = {
            'connected_at': asyncio.get_event_loop().time(),
            'project_id': None,
            'chat_id': None
        }

        logger.info(f"Client connected: {sid}")
        await sio.emit('connection_status', {'status': 'connected'}, room=sid)
        return True

    except Exception as e:
        logger.error(f"Error during connection: {e}", exc_info=True)
        return False


@sio.event
async def disconnect(sid: str):
    """
    Handle client disconnection.

    Args:
        sid: Socket session ID
    """
    try:
        logger.info(f"Client disconnecting: {sid}")

        # Clean up connection metadata
        if sid in active_connections:
            connection_data = active_connections[sid]
            project_id = connection_data.get('project_id')

            # Leave project room if joined
            if project_id:
                await sio.leave_room(sid, f"project_{project_id}")
                logger.info(f"Client {sid} left project room {project_id}")

            del active_connections[sid]

        logger.info(f"Client disconnected: {sid}")

    except Exception as e:
        logger.error(f"Error during disconnection: {e}", exc_info=True)


@sio.event
async def join_project(sid: str, data: Dict[str, Any]):
    """
    Join a project room for receiving project-specific updates.

    Args:
        sid: Socket session ID
        data: Dict containing 'project_id'
    """
    try:
        project_id = data.get('project_id')

        if not project_id:
            await sio.emit('error', {
                'message': 'project_id is required'
            }, room=sid)
            return

        # Leave previous project room if any
        if sid in active_connections:
            old_project_id = active_connections[sid].get('project_id')
            if old_project_id and old_project_id != project_id:
                await sio.leave_room(sid, f"project_{old_project_id}")

        # Join new project room
        await sio.enter_room(sid, f"project_{project_id}")

        # Update connection metadata
        if sid in active_connections:
            active_connections[sid]['project_id'] = project_id

        logger.info(f"Client {sid} joined project {project_id}")
        await sio.emit('project_joined', {
            'project_id': project_id,
            'status': 'success'
        }, room=sid)

    except Exception as e:
        logger.error(f"Error joining project: {e}", exc_info=True)
        await sio.emit('error', {
            'message': f'Failed to join project: {str(e)}'
        }, room=sid)


@sio.event
async def leave_project(sid: str, data: Dict[str, Any]):
    """
    Leave a project room.

    Args:
        sid: Socket session ID
        data: Dict containing 'project_id'
    """
    try:
        project_id = data.get('project_id')

        if not project_id:
            await sio.emit('error', {
                'message': 'project_id is required'
            }, room=sid)
            return

        # Leave project room
        await sio.leave_room(sid, f"project_{project_id}")

        # Update connection metadata
        if sid in active_connections:
            active_connections[sid]['project_id'] = None

        logger.info(f"Client {sid} left project {project_id}")
        await sio.emit('project_left', {
            'project_id': project_id,
            'status': 'success'
        }, room=sid)

    except Exception as e:
        logger.error(f"Error leaving project: {e}", exc_info=True)
        await sio.emit('error', {
            'message': f'Failed to leave project: {str(e)}'
        }, room=sid)


@sio.event
async def send_message(sid: str, data: Dict[str, Any]):
    """
    Handle incoming chat message and stream response.

    Args:
        sid: Socket session ID
        data: Message data containing:
            - chat_id: Chat session ID
            - message: User message text
            - model: Optional LLM model name
            - temperature: Optional temperature setting
            - include_history: Whether to include chat history
    """
    try:
        # Extract message data
        chat_id = data.get('chat_id')
        user_message = data.get('message')
        model = data.get('model')
        temperature = data.get('temperature', 0.7)
        include_history = data.get('include_history', True)

        # Validate required fields
        if not chat_id:
            await sio.emit('error', {
                'message': 'chat_id is required'
            }, room=sid)
            return

        if not user_message:
            await sio.emit('error', {
                'message': 'message is required'
            }, room=sid)
            return

        logger.info(f"Processing message for chat {chat_id} from client {sid}")

        # Update connection metadata
        if sid in active_connections:
            active_connections[sid]['chat_id'] = chat_id

        # Emit message received acknowledgment
        await sio.emit('message_received', {
            'chat_id': chat_id,
            'status': 'processing'
        }, room=sid)

        # Get database session
        async for db in get_db():
            try:
                # Stream response using chat service
                async for event in chat_service.send_message_stream(
                    db=db,
                    chat_id=chat_id,
                    user_message=user_message,
                    model=model,
                    temperature=temperature,
                    include_history=include_history
                ):
                    # Forward stream events to client
                    event_type = event.get('type')

                    if event_type == 'sources':
                        # Send retrieved sources
                        await sio.emit('message_sources', {
                            'chat_id': chat_id,
                            'sources': event['data']
                        }, room=sid)

                    elif event_type == 'token':
                        # Stream text token
                        await sio.emit('message_token', {
                            'chat_id': chat_id,
                            'token': event['data']
                        }, room=sid)

                    elif event_type == 'done':
                        # Send completion signal
                        await sio.emit('message_complete', {
                            'chat_id': chat_id,
                            'metadata': event['data']
                        }, room=sid)

                logger.info(f"Successfully streamed response for chat {chat_id}")

            except ChatServiceError as e:
                logger.error(f"Chat service error: {e}", exc_info=True)
                await sio.emit('error', {
                    'message': f'Chat error: {str(e)}',
                    'chat_id': chat_id
                }, room=sid)

            finally:
                # Close database session
                await db.close()
                break

    except Exception as e:
        logger.error(f"Error processing message: {e}", exc_info=True)
        await sio.emit('error', {
            'message': f'Failed to process message: {str(e)}',
            'chat_id': data.get('chat_id')
        }, room=sid)


@sio.event
async def ping(sid: str, data: Optional[Dict[str, Any]] = None):
    """
    Handle ping request for connection health check.

    Args:
        sid: Socket session ID
        data: Optional ping data
    """
    await sio.emit('pong', {
        'timestamp': asyncio.get_event_loop().time()
    }, room=sid)


# Utility functions for broadcasting updates

async def broadcast_to_project(project_id: int, event: str, data: Dict[str, Any]):
    """
    Broadcast an event to all clients in a project room.

    Args:
        project_id: Project ID
        event: Event name
        data: Event data
    """
    try:
        room = f"project_{project_id}"
        await sio.emit(event, data, room=room)
        logger.debug(f"Broadcast {event} to project {project_id}")
    except Exception as e:
        logger.error(f"Error broadcasting to project {project_id}: {e}")


async def notify_document_processing(project_id: int, document_id: int, status: str, progress: Optional[int] = None):
    """
    Notify clients about document processing status.

    Args:
        project_id: Project ID
        document_id: Document ID
        status: Processing status (processing, completed, failed)
        progress: Optional progress percentage (0-100)
    """
    await broadcast_to_project(project_id, 'document_status', {
        'document_id': document_id,
        'status': status,
        'progress': progress
    })


async def notify_project_update(project_id: int, update_type: str, data: Dict[str, Any]):
    """
    Notify clients about project updates.

    Args:
        project_id: Project ID
        update_type: Type of update (document_added, document_deleted, etc.)
        data: Update data
    """
    await broadcast_to_project(project_id, 'project_update', {
        'type': update_type,
        'data': data
    })


# Export the Socket.IO app for integration with FastAPI
__all__ = ['sio', 'broadcast_to_project', 'notify_document_processing', 'notify_project_update']
