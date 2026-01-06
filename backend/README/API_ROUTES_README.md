# API Routes Documentation

This document provides comprehensive documentation for all API endpoints in the DAA Chatbot backend.

## Table of Contents

- [Overview](#overview)
- [Base URL](#base-url)
- [Authentication](#authentication)
- [Routes](#routes)
  - [Health Check](#health-check)
  - [Projects](#projects)
  - [Documents](#documents)
  - [Chat](#chat)
  - [LLM](#llm)
  - [Analytics](#analytics)
- [WebSocket Events](#websocket-events)
- [Error Handling](#error-handling)

## Overview

The DAA Chatbot API is built with FastAPI and provides a RESTful interface for managing projects, documents, chat conversations, and RAG-based question answering. Real-time chat streaming is handled via WebSocket using Socket.IO.

All API endpoints are documented with OpenAPI/Swagger and can be explored interactively at `/docs` when the server is running.

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API is designed for local single-user deployment and does not require authentication. For production deployments, consider implementing JWT-based authentication.

## Routes

### Health Check

#### `GET /api/health`

Check the health status of the backend service and Ollama connection.

**Response:**
```json
{
  "status": "healthy",
  "ollama": {
    "connected": true,
    "host": "http://localhost:11434",
    "models": ["llama3.2", "nomic-embed-text"]
  },
  "database": {
    "connected": true
  }
}
```

**Status Codes:**
- `200 OK`: Service is healthy
- `503 Service Unavailable`: Service is unhealthy (Ollama not reachable, database error)

---

### Projects

Projects are isolated workspaces that contain their own sets of documents and chat conversations.

#### `POST /api/projects`

Create a new project.

**Request Body:**
```json
{
  "name": "My Project",
  "description": "Optional project description"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "My Project",
  "description": "Optional project description",
  "created_at": "2025-01-07T12:00:00Z",
  "updated_at": "2025-01-07T12:00:00Z",
  "document_count": 0,
  "chat_count": 0
}
```

**Status Codes:**
- `201 Created`: Project created successfully
- `400 Bad Request`: Invalid request body
- `500 Internal Server Error`: Database error

#### `GET /api/projects`

List all projects.

**Query Parameters:**
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Maximum number of records to return (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "name": "My Project",
    "description": "Optional project description",
    "created_at": "2025-01-07T12:00:00Z",
    "updated_at": "2025-01-07T12:00:00Z",
    "document_count": 5,
    "chat_count": 3
  }
]
```

**Status Codes:**
- `200 OK`: Projects retrieved successfully

#### `GET /api/projects/{project_id}`

Get a specific project by ID.

**Path Parameters:**
- `project_id` (int): Project ID

**Response:**
```json
{
  "id": 1,
  "name": "My Project",
  "description": "Optional project description",
  "created_at": "2025-01-07T12:00:00Z",
  "updated_at": "2025-01-07T12:00:00Z",
  "document_count": 5,
  "chat_count": 3
}
```

**Status Codes:**
- `200 OK`: Project retrieved successfully
- `404 Not Found`: Project not found

#### `PUT /api/projects/{project_id}`

Update a project.

**Path Parameters:**
- `project_id` (int): Project ID

**Request Body:**
```json
{
  "name": "Updated Project Name",
  "description": "Updated description"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Updated Project Name",
  "description": "Updated description",
  "created_at": "2025-01-07T12:00:00Z",
  "updated_at": "2025-01-07T13:00:00Z",
  "document_count": 5,
  "chat_count": 3
}
```

**Status Codes:**
- `200 OK`: Project updated successfully
- `404 Not Found`: Project not found
- `400 Bad Request`: Invalid request body

#### `DELETE /api/projects/{project_id}`

Delete a project and all associated documents, embeddings, and chat history.

**Path Parameters:**
- `project_id` (int): Project ID

**Response:**
```json
{
  "message": "Project deleted successfully"
}
```

**Status Codes:**
- `200 OK`: Project deleted successfully
- `404 Not Found`: Project not found

---

### Documents

Documents are files uploaded to projects that are processed, chunked, and embedded for RAG retrieval.

#### `POST /api/projects/{project_id}/documents`

Upload a document to a project.

**Path Parameters:**
- `project_id` (int): Project ID

**Request:**
- Content-Type: `multipart/form-data`
- File field: `file`

**Supported Formats:**
- PDF (`.pdf`)
- Microsoft Word (`.docx`)
- Text files (`.txt`, `.md`)
- CSV (`.csv`)
- Excel (`.xlsx`)

**Response:**
```json
{
  "id": 1,
  "project_id": 1,
  "filename": "document.pdf",
  "file_type": "pdf",
  "file_size": 102400,
  "status": "processing",
  "created_at": "2025-01-07T12:00:00Z",
  "processed_at": null,
  "metadata": {
    "page_count": 10,
    "word_count": 5000
  }
}
```

**Status Codes:**
- `201 Created`: Document upload initiated
- `400 Bad Request`: Invalid file type or size
- `404 Not Found`: Project not found
- `413 Payload Too Large`: File exceeds maximum size (default 10MB)

#### `GET /api/projects/{project_id}/documents`

List all documents in a project.

**Path Parameters:**
- `project_id` (int): Project ID

**Query Parameters:**
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Maximum number of records to return (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "project_id": 1,
    "filename": "document.pdf",
    "file_type": "pdf",
    "file_size": 102400,
    "status": "completed",
    "created_at": "2025-01-07T12:00:00Z",
    "processed_at": "2025-01-07T12:05:00Z",
    "metadata": {
      "page_count": 10,
      "word_count": 5000,
      "chunk_count": 25
    }
  }
]
```

**Status Codes:**
- `200 OK`: Documents retrieved successfully
- `404 Not Found`: Project not found

#### `GET /api/documents/{document_id}`

Get a specific document by ID.

**Path Parameters:**
- `document_id` (int): Document ID

**Response:**
```json
{
  "id": 1,
  "project_id": 1,
  "filename": "document.pdf",
  "file_type": "pdf",
  "file_size": 102400,
  "status": "completed",
  "created_at": "2025-01-07T12:00:00Z",
  "processed_at": "2025-01-07T12:05:00Z",
  "metadata": {
    "page_count": 10,
    "word_count": 5000,
    "chunk_count": 25
  }
}
```

**Status Codes:**
- `200 OK`: Document retrieved successfully
- `404 Not Found`: Document not found

#### `DELETE /api/documents/{document_id}`

Delete a document and its embeddings.

**Path Parameters:**
- `document_id` (int): Document ID

**Response:**
```json
{
  "message": "Document deleted successfully"
}
```

**Status Codes:**
- `200 OK`: Document deleted successfully
- `404 Not Found`: Document not found

---

### Chat

Chat endpoints manage conversations and message history.

#### `POST /api/projects/{project_id}/chats`

Create a new chat conversation in a project.

**Path Parameters:**
- `project_id` (int): Project ID

**Request Body:**
```json
{
  "title": "My Conversation"
}
```

**Response:**
```json
{
  "id": 1,
  "project_id": 1,
  "title": "My Conversation",
  "created_at": "2025-01-07T12:00:00Z",
  "updated_at": "2025-01-07T12:00:00Z",
  "message_count": 0
}
```

**Status Codes:**
- `201 Created`: Chat created successfully
- `404 Not Found`: Project not found

#### `GET /api/projects/{project_id}/chats`

List all chats in a project.

**Path Parameters:**
- `project_id` (int): Project ID

**Response:**
```json
[
  {
    "id": 1,
    "project_id": 1,
    "title": "My Conversation",
    "created_at": "2025-01-07T12:00:00Z",
    "updated_at": "2025-01-07T12:00:00Z",
    "message_count": 10
  }
]
```

**Status Codes:**
- `200 OK`: Chats retrieved successfully
- `404 Not Found`: Project not found

#### `GET /api/chats/{chat_id}`

Get a specific chat by ID.

**Path Parameters:**
- `chat_id` (int): Chat ID

**Response:**
```json
{
  "id": 1,
  "project_id": 1,
  "title": "My Conversation",
  "created_at": "2025-01-07T12:00:00Z",
  "updated_at": "2025-01-07T12:00:00Z",
  "message_count": 10
}
```

**Status Codes:**
- `200 OK`: Chat retrieved successfully
- `404 Not Found`: Chat not found

#### `GET /api/chats/{chat_id}/messages`

Get all messages in a chat.

**Path Parameters:**
- `chat_id` (int): Chat ID

**Query Parameters:**
- `skip` (int, optional): Number of records to skip (default: 0)
- `limit` (int, optional): Maximum number of records to return (default: 100)

**Response:**
```json
[
  {
    "id": 1,
    "chat_id": 1,
    "role": "user",
    "content": "What is RAG?",
    "created_at": "2025-01-07T12:00:00Z"
  },
  {
    "id": 2,
    "chat_id": 1,
    "role": "assistant",
    "content": "RAG stands for Retrieval-Augmented Generation...",
    "created_at": "2025-01-07T12:00:05Z",
    "sources": [
      {
        "document_id": 1,
        "document_name": "rag_paper.pdf",
        "chunk_text": "Retrieval-Augmented Generation combines...",
        "page": 1,
        "similarity": 0.92
      }
    ]
  }
]
```

**Status Codes:**
- `200 OK`: Messages retrieved successfully
- `404 Not Found`: Chat not found

#### `DELETE /api/chats/{chat_id}`

Delete a chat and all its messages.

**Path Parameters:**
- `chat_id` (int): Chat ID

**Response:**
```json
{
  "message": "Chat deleted successfully"
}
```

**Status Codes:**
- `200 OK`: Chat deleted successfully
- `404 Not Found`: Chat not found

---

### LLM

LLM endpoints provide configuration and testing capabilities for Ollama models.

#### `GET /api/llm/models`

List all available models in Ollama.

**Response:**
```json
{
  "models": [
    {
      "name": "llama3.2",
      "size": "4.7GB",
      "modified_at": "2025-01-07T10:00:00Z"
    },
    {
      "name": "nomic-embed-text",
      "size": "274MB",
      "modified_at": "2025-01-07T10:00:00Z"
    }
  ]
}
```

**Status Codes:**
- `200 OK`: Models retrieved successfully
- `503 Service Unavailable`: Cannot connect to Ollama

#### `POST /api/llm/test`

Test LLM generation with a simple prompt.

**Request Body:**
```json
{
  "prompt": "What is the capital of France?",
  "model": "llama3.2"
}
```

**Response:**
```json
{
  "response": "The capital of France is Paris.",
  "model": "llama3.2",
  "generated_at": "2025-01-07T12:00:00Z"
}
```

**Status Codes:**
- `200 OK`: Test successful
- `400 Bad Request`: Invalid request
- `503 Service Unavailable`: Cannot connect to Ollama

#### `GET /api/llm/config`

Get current LLM configuration.

**Response:**
```json
{
  "llm_model": "llama3.2",
  "embedding_model": "nomic-embed-text",
  "ollama_host": "http://localhost:11434",
  "chunk_size": 1000,
  "chunk_overlap": 200,
  "retrieval_k": 5
}
```

**Status Codes:**
- `200 OK`: Configuration retrieved successfully

---

### Analytics

Analytics endpoints provide embedding visualization and similarity analysis.

#### `GET /api/projects/{project_id}/analytics/embeddings`

Get embeddings data for visualization.

**Path Parameters:**
- `project_id` (int): Project ID

**Query Parameters:**
- `reduction_method` (string, optional): Dimensionality reduction method (`pca`, `tsne`, `umap`) (default: `pca`)
- `dimensions` (int, optional): Target dimensions (2 or 3) (default: 2)

**Response:**
```json
{
  "embeddings": [
    {
      "chunk_id": "doc1_chunk0",
      "document_id": 1,
      "document_name": "document.pdf",
      "chunk_index": 0,
      "text": "First chunk of text...",
      "coordinates": [0.5, -0.3],
      "norm": 1.0
    }
  ],
  "method": "pca",
  "dimensions": 2,
  "stats": {
    "total_chunks": 100,
    "total_documents": 5,
    "avg_norm": 0.98,
    "std_norm": 0.05
  }
}
```

**Status Codes:**
- `200 OK`: Embeddings retrieved successfully
- `404 Not Found`: Project not found
- `400 Bad Request`: Invalid parameters

#### `GET /api/projects/{project_id}/analytics/similarity`

Get similarity matrix for documents or chunks.

**Path Parameters:**
- `project_id` (int): Project ID

**Query Parameters:**
- `level` (string, optional): Analysis level (`document` or `chunk`) (default: `document`)
- `limit` (int, optional): Maximum number of items to analyze (default: 50)

**Response:**
```json
{
  "similarity_matrix": [[1.0, 0.85], [0.85, 1.0]],
  "labels": ["document1.pdf", "document2.pdf"],
  "level": "document",
  "method": "cosine"
}
```

**Status Codes:**
- `200 OK`: Similarity matrix retrieved successfully
- `404 Not Found`: Project not found

#### `POST /api/projects/{project_id}/analytics/test-retrieval`

Test retrieval quality with a query.

**Path Parameters:**
- `project_id` (int): Project ID

**Request Body:**
```json
{
  "query": "What is machine learning?",
  "k": 5
}
```

**Response:**
```json
{
  "query": "What is machine learning?",
  "results": [
    {
      "chunk_text": "Machine learning is a subset of artificial intelligence...",
      "document_name": "ml_intro.pdf",
      "document_id": 1,
      "similarity": 0.92,
      "chunk_index": 5,
      "page": 3
    }
  ],
  "retrieval_time_ms": 45
}
```

**Status Codes:**
- `200 OK`: Retrieval test successful
- `404 Not Found`: Project not found
- `400 Bad Request`: Invalid query

---

## WebSocket Events

Real-time chat streaming uses Socket.IO on the same port as the HTTP API.

### Connection

```javascript
import io from 'socket.io-client';

const socket = io('http://localhost:8000');
```

### Events

#### Client → Server: `send_message`

Send a message to start a chat conversation.

**Payload:**
```json
{
  "chat_id": 1,
  "message": "What is RAG?",
  "project_id": 1
}
```

#### Server → Client: `message_chunk`

Receive streaming response chunks.

**Payload:**
```json
{
  "chat_id": 1,
  "chunk": "RAG stands for",
  "type": "token"
}
```

#### Server → Client: `message_complete`

Receive complete message with metadata.

**Payload:**
```json
{
  "chat_id": 1,
  "message_id": 2,
  "content": "RAG stands for Retrieval-Augmented Generation...",
  "sources": [
    {
      "document_id": 1,
      "document_name": "rag_paper.pdf",
      "chunk_text": "Retrieval-Augmented Generation combines...",
      "page": 1,
      "similarity": 0.92
    }
  ]
}
```

#### Server → Client: `error`

Error occurred during processing.

**Payload:**
```json
{
  "error": "Error message",
  "chat_id": 1
}
```

---

## Error Handling

### Standard Error Response

All errors return a consistent format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters or body
- `404 Not Found`: Resource not found
- `413 Payload Too Large`: File upload exceeds size limit
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: External service (Ollama) unavailable

### Common Error Scenarios

1. **Ollama Not Running**: Returns 503 with message about Ollama connectivity
2. **Invalid File Type**: Returns 400 with list of supported formats
3. **Project Not Found**: Returns 404 when accessing non-existent project
4. **Database Error**: Returns 500 with generic error message (details in server logs)

---

## Interactive Documentation

For interactive API exploration with request/response examples:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Both provide detailed schema information, request examples, and the ability to test endpoints directly from the browser.
