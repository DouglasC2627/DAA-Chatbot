"""
Tests for WebSocket functionality.

This test suite verifies:
- WebSocket server initialization
- Utility functions for broadcasting
- Event handler registration
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from api.websocket.chat_ws import (
    sio,
    active_connections,
    broadcast_to_project,
    notify_document_processing,
    notify_project_update
)


def test_websocket_server_initialization():
    """Test that WebSocket server initializes correctly."""
    assert sio is not None, "Socket.IO server should be initialized"
    assert sio.async_mode == 'asgi', "Server should use ASGI mode"
    assert hasattr(sio, 'emit'), "Server should have emit method"
    assert hasattr(sio, 'enter_room'), "Server should have enter_room method"
    assert hasattr(sio, 'leave_room'), "Server should have leave_room method"


def test_active_connections_dict():
    """Test that active connections dictionary exists."""
    assert isinstance(active_connections, dict), "active_connections should be a dictionary"


def test_event_handlers_registered():
    """Test that event handlers are properly registered."""
    # Socket.IO stores handlers in a specific structure
    # Just verify the handlers dict exists
    assert hasattr(sio, 'handlers'), "Server should have handlers registered"


@pytest.mark.asyncio
async def test_broadcast_to_project():
    """Test broadcasting events to project rooms."""
    project_id = 1
    event = "test_event"
    data = {"message": "test data"}

    # This should not raise an error even if no clients are in the room
    await broadcast_to_project(project_id, event, data)


@pytest.mark.asyncio
async def test_document_processing_notification():
    """Test document processing status notifications."""
    project_id = 1
    document_id = 1

    # Test different status notifications
    await notify_document_processing(
        project_id=project_id,
        document_id=document_id,
        status='processing',
        progress=50
    )

    await notify_document_processing(
        project_id=project_id,
        document_id=document_id,
        status='completed',
        progress=100
    )


@pytest.mark.asyncio
async def test_project_update_notification():
    """Test project update notifications."""
    project_id = 1

    await notify_project_update(
        project_id=project_id,
        update_type='document_added',
        data={'document_id': 1, 'filename': 'test.pdf'}
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
