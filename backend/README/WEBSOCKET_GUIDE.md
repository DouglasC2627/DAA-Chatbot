# WebSocket Implementation Guide

## Overview

The DAA Chatbot supports real-time WebSocket communication using Socket.IO for streaming chat responses, document processing updates, and project notifications.

## Server Configuration

### Starting the Server

The WebSocket server is integrated with the FastAPI application:

```bash
# Development mode with auto-reload
uvicorn api.main:socket_app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn api.main:socket_app --host 0.0.0.0 --port 8000 --workers 4
```

### Connection URL

WebSocket connections are available at:
```
ws://localhost:8000/socket.io/
```

## Client-Side Events

### Connection Events

#### Connect to Server
```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:8000', {
  path: '/socket.io',
  transports: ['websocket', 'polling']
});

socket.on('connect', () => {
  console.log('Connected:', socket.id);
});

socket.on('connection_status', (data) => {
  console.log('Status:', data.status); // 'connected'
});
```

#### Disconnect
```javascript
socket.on('disconnect', () => {
  console.log('Disconnected from server');
});
```

### Project Room Management

#### Join a Project Room
```javascript
socket.emit('join_project', {
  project_id: 1
});

socket.on('project_joined', (data) => {
  console.log('Joined project:', data.project_id);
});
```

#### Leave a Project Room
```javascript
socket.emit('leave_project', {
  project_id: 1
});

socket.on('project_left', (data) => {
  console.log('Left project:', data.project_id);
});
```

### Chat Message Streaming

#### Send a Message
```javascript
socket.emit('send_message', {
  chat_id: 1,
  message: 'What is this document about?',
  model: 'llama3.2',          // optional
  temperature: 0.7,            // optional
  include_history: true        // optional
});
```

#### Receive Message Events

```javascript
// Message received acknowledgment
socket.on('message_received', (data) => {
  console.log('Processing message for chat:', data.chat_id);
});

// Retrieved source documents
socket.on('message_sources', (data) => {
  console.log('Sources:', data.sources);
  // data.sources is an array of retrieved documents:
  // [
  //   {
  //     id: "chunk_123",
  //     content: "Retrieved text...",
  //     metadata: { document_id: 5, page: 2, ... },
  //     score: 0.85
  //   },
  //   ...
  // ]
});

// Streaming response tokens
socket.on('message_token', (data) => {
  // Append token to UI
  appendToMessage(data.chat_id, data.token);
});

// Message complete
socket.on('message_complete', (data) => {
  console.log('Complete:', data.metadata);
  // data.metadata contains:
  // { model: 'llama3.2', sources_count: 5 }
});
```

### Real-time Notifications

#### Document Processing Status
```javascript
socket.on('document_status', (data) => {
  console.log(`Document ${data.document_id}: ${data.status}`);
  if (data.progress) {
    updateProgressBar(data.document_id, data.progress);
  }
});
```

#### Project Updates
```javascript
socket.on('project_update', (data) => {
  console.log(`Update type: ${data.type}`);
  console.log('Data:', data.data);
  // Examples:
  // { type: 'document_added', data: { document_id: 10, filename: 'doc.pdf' } }
  // { type: 'document_deleted', data: { document_id: 5 } }
});
```

### Health Check (Ping/Pong)

```javascript
socket.emit('ping', {});

socket.on('pong', (data) => {
  console.log('Latency:', Date.now() - data.timestamp);
});
```

### Error Handling

```javascript
socket.on('error', (data) => {
  console.error('WebSocket error:', data.message);
  if (data.chat_id) {
    console.error('Related to chat:', data.chat_id);
  }
});
```

## Complete Example: Streaming Chat

```javascript
import io from 'socket.io-client';
import { useState } from 'react';

function ChatComponent({ chatId, projectId }) {
  const [socket, setSocket] = useState(null);
  const [message, setMessage] = useState('');
  const [response, setResponse] = useState('');
  const [sources, setSources] = useState([]);

  useEffect(() => {
    // Connect to server
    const newSocket = io('http://localhost:8000', {
      path: '/socket.io',
      transports: ['websocket']
    });

    newSocket.on('connect', () => {
      // Join project room
      newSocket.emit('join_project', { project_id: projectId });
    });

    // Handle streaming responses
    newSocket.on('message_sources', (data) => {
      setSources(data.sources);
    });

    newSocket.on('message_token', (data) => {
      setResponse(prev => prev + data.token);
    });

    newSocket.on('message_complete', (data) => {
      console.log('Response complete');
    });

    newSocket.on('error', (data) => {
      console.error('Error:', data.message);
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, [projectId]);

  const sendMessage = () => {
    if (!socket || !message.trim()) return;

    setResponse(''); // Clear previous response
    setSources([]);

    socket.emit('send_message', {
      chat_id: chatId,
      message: message,
      temperature: 0.7,
      include_history: true
    });

    setMessage('');
  };

  return (
    <div>
      <input
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
      />
      <button onClick={sendMessage}>Send</button>

      {sources.length > 0 && (
        <div className="sources">
          <h4>Sources:</h4>
          {sources.map((source, i) => (
            <div key={i}>
              Document {source.metadata.document_id}, Page {source.metadata.page}
            </div>
          ))}
        </div>
      )}

      <div className="response">{response}</div>
    </div>
  );
}
```

## Server-Side Utilities

### Broadcasting to Project Rooms

```python
from api.websocket.chat_ws import broadcast_to_project

# Broadcast custom event to all clients in a project
await broadcast_to_project(
    project_id=1,
    event='custom_event',
    data={'key': 'value'}
)
```

### Document Processing Notifications

```python
from api.websocket.chat_ws import notify_document_processing

# Notify about document processing
await notify_document_processing(
    project_id=1,
    document_id=5,
    status='processing',  # 'processing', 'completed', 'failed'
    progress=75           # 0-100
)
```

### Project Update Notifications

```python
from api.websocket.chat_ws import notify_project_update

# Notify about project changes
await notify_project_update(
    project_id=1,
    update_type='document_added',
    data={
        'document_id': 10,
        'filename': 'new_doc.pdf'
    }
)
```

## Event Flow: Sending a Chat Message

1. **Client** sends message via `send_message` event
2. **Server** validates request and saves user message to database
3. **Server** emits `message_received` acknowledgment
4. **Server** retrieves relevant documents from vector store
5. **Server** emits `message_sources` with retrieved documents
6. **Server** streams LLM response token by token via `message_token`
7. **Server** emits `message_complete` when done
8. **Server** saves assistant message to database

## Room Structure

- Each project has a room: `project_{project_id}`
- Clients join rooms to receive project-specific updates
- Clients can be in only one project room at a time
- Room switching automatically leaves the previous room

## Connection Metadata

Each connection tracks:
- `connected_at`: Connection timestamp
- `project_id`: Currently joined project (or `None`)
- `chat_id`: Last active chat (or `None`)

## Error Handling

All event handlers include comprehensive error handling:

- Invalid data → `error` event with descriptive message
- Missing required fields → `error` event
- Service failures → `error` event with context
- Disconnections → Automatic cleanup of connection metadata

## Authentication (Placeholder)

Currently, all connections are accepted. To implement authentication:

```python
@sio.event
async def connect(sid: str, environ: Dict[str, Any], auth: Optional[Dict[str, Any]] = None):
    if not auth or 'token' not in auth:
        return False  # Reject connection

    # Validate JWT token
    try:
        user = validate_jwt_token(auth['token'])
        active_connections[sid]['user_id'] = user.id
        return True
    except:
        return False
```

Client-side:
```javascript
const socket = io('http://localhost:8000', {
  auth: {
    token: 'your-jwt-token'
  }
});
```

## Testing

Run WebSocket tests:
```bash
pytest tests/test_websocket.py -v
```

## Troubleshooting

### Connection Issues

1. **CORS errors**: Update `cors_allowed_origins` in `chat_ws.py`
2. **Connection timeout**: Check firewall settings
3. **Polling fallback**: WebSocket may fall back to polling if WS fails

### Performance

- Use `transports: ['websocket']` to force WebSocket (faster than polling)
- Implement reconnection logic for network interruptions
- Monitor `active_connections` dict for connection leaks

### Debugging

Enable Socket.IO logging:
```python
sio = socketio.AsyncServer(
    async_mode='asgi',
    logger=True,
    engineio_logger=True  # Detailed logs
)
```

## Next Steps

For Task 8.2 (Frontend WebSocket Integration):
1. Create `frontend/lib/websocket.ts` connection manager
2. Implement auto-reconnection logic
3. Create React hooks for WebSocket events
4. Add connection status indicator to UI
5. Implement typing indicators (optional)
