# Services Layer Documentation

This document provides detailed documentation for the services layer, which contains the business logic for the DAA Chatbot application.

## Table of Contents

- [Overview](#overview)
- [Service Architecture](#service-architecture)
- [Services](#services)
  - [Document Processor](#document-processor)
  - [Chat Service](#chat-service)
  - [Project Service](#project-service)
  - [Analytics Service](#analytics-service)
  - [File Storage](#file-storage)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)

## Overview

The `services/` directory contains business logic that orchestrates operations across multiple layers (database, file system, vector store, LLM). Services act as the interface between API routes and core functionality.

```
backend/services/
├── document_processor.py  # Extract text from various file formats
├── chat_service.py        # Conversation management and history
├── project_service.py     # Project CRUD and isolation logic
├── analytics_service.py   # Analytics computations and visualizations
└── file_storage.py        # File system operations and management
```

**Key Responsibilities:**
- Coordinate multi-step operations
- Implement business rules and validation
- Handle errors and edge cases
- Manage transactions across systems
- Provide clean interfaces for API routes

## Service Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    API Routes                           │
│         (Handle HTTP requests/responses)                 │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  Services Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Document   │  │     Chat     │  │   Project    │  │
│  │  Processor   │  │   Service    │  │   Service    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│  ┌──────────────┐  ┌──────────────┐                    │
│  │  Analytics   │  │    File      │                    │
│  │   Service    │  │   Storage    │                    │
│  └──────────────┘  └──────────────┘                    │
└──────┬────────────────────┬────────────────────┬────────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────┐  ┌──────────────┐    ┌──────────────┐
│ CRUD Layer   │  │ Core Modules │    │ File System  │
│  (Database)  │  │ (RAG, LLM)   │    │    (Disk)    │
└──────────────┘  └──────────────┘    └──────────────┘
```

## Services

### Document Processor

**File:** `services/document_processor.py`

Extracts text content from various document formats and prepares them for embedding.

#### Key Functions

##### `process_document(file_path: str, file_type: str) -> Dict`

Extract text and metadata from a document.

**Parameters:**
- `file_path` (str): Path to the uploaded file
- `file_type` (str): File extension (pdf, docx, txt, csv, xlsx, md)

**Returns:**
```python
{
    "text": "Extracted text content...",
    "metadata": {
        "page_count": 10,
        "word_count": 5000,
        "char_count": 30000,
        "language": "en",
        "has_images": True
    }
}
```

**Usage Example:**
```python
from backend.services.document_processor import process_document

result = process_document(
    file_path="/path/to/document.pdf",
    file_type="pdf"
)

text = result["text"]
metadata = result["metadata"]
print(f"Extracted {metadata['word_count']} words from {metadata['page_count']} pages")
```

**Supported Formats:**

1. **PDF (.pdf)**
   - Uses `pypdf` library
   - Extracts text page by page
   - Preserves page numbers in metadata
   - Handles multi-column layouts

   ```python
   # PDF-specific metadata
   {
       "page_count": 10,
       "has_images": True,
       "is_encrypted": False
   }
   ```

2. **Word Documents (.docx)**
   - Uses `python-docx` library
   - Extracts paragraphs and tables
   - Preserves document structure

   ```python
   # DOCX-specific metadata
   {
       "paragraph_count": 45,
       "table_count": 3,
       "section_count": 5
   }
   ```

3. **Text Files (.txt, .md)**
   - Direct file reading with encoding detection
   - Markdown formatting preserved
   - Fast processing

   ```python
   # TXT/MD-specific metadata
   {
       "encoding": "utf-8",
       "line_count": 250
   }
   ```

4. **CSV Files (.csv)**
   - Uses `pandas` for robust parsing
   - Converts to structured text
   - Handles various delimiters

   ```python
   # CSV-specific metadata
   {
       "row_count": 1000,
       "column_count": 10,
       "columns": ["Name", "Age", "City", ...]
   }
   ```

5. **Excel Files (.xlsx)**
   - Uses `openpyxl` library
   - Processes all sheets
   - Handles formulas and formatting

   ```python
   # XLSX-specific metadata
   {
       "sheet_count": 3,
       "total_rows": 5000,
       "sheets": ["Sales", "Inventory", "Reports"]
   }
   ```

##### `validate_file(file_path: str, max_size: int) -> bool`

Validate file before processing.

**Checks:**
- File exists and is readable
- File size within limits
- MIME type matches extension
- File is not corrupted

```python
from backend.services.document_processor import validate_file

is_valid = validate_file(
    file_path="/path/to/doc.pdf",
    max_size=10485760  # 10MB
)

if not is_valid:
    raise ValueError("Invalid file")
```

##### `chunk_and_embed(text: str, document_id: int, metadata: Dict) -> List[Dict]`

Split text into chunks and generate embeddings.

```python
from backend.services.document_processor import chunk_and_embed

chunks = await chunk_and_embed(
    text=extracted_text,
    document_id=1,
    metadata={"document_name": "doc.pdf", "page_count": 10}
)

# Returns chunks ready for vector store
# [
#   {
#     "id": "doc_1_chunk_0",
#     "text": "First chunk...",
#     "embedding": [0.1, 0.2, ...],
#     "metadata": {...}
#   }, ...
# ]
```

**Error Handling:**

```python
from backend.services.document_processor import process_document, DocumentProcessingError

try:
    result = process_document(file_path, file_type)
except DocumentProcessingError as e:
    # Handle specific processing errors
    logger.error(f"Failed to process document: {e}")
except Exception as e:
    # Handle unexpected errors
    logger.error(f"Unexpected error: {e}")
```

---

### Chat Service

**File:** `services/chat_service.py`

Manages chat conversations, message history, and RAG-based response generation.

#### Key Functions

##### `create_chat(project_id: int, title: str, db: Session) -> Chat`

Create a new chat conversation.

```python
from backend.services.chat_service import create_chat

chat = create_chat(
    project_id=1,
    title="Discussion about ML",
    db=db_session
)

print(f"Created chat {chat.id}: {chat.title}")
```

##### `send_message(chat_id: int, message: str, db: Session) -> Message`

Send a user message and get an AI response.

**Process:**
1. Save user message to database
2. Load chat history
3. Call RAG pipeline to generate response
4. Save assistant message to database
5. Return complete conversation

```python
from backend.services.chat_service import send_message

response = await send_message(
    chat_id=1,
    message="What is machine learning?",
    db=db_session
)

print(f"User: {response['user_message'].content}")
print(f"AI: {response['assistant_message'].content}")
print(f"Sources: {response['sources']}")
```

**Response Format:**
```python
{
    "user_message": Message(
        id=1,
        chat_id=1,
        role="user",
        content="What is machine learning?",
        created_at=datetime(...)
    ),
    "assistant_message": Message(
        id=2,
        chat_id=1,
        role="assistant",
        content="Machine learning is...",
        created_at=datetime(...),
        metadata={
            "sources": [
                {
                    "document_id": 1,
                    "document_name": "ml_intro.pdf",
                    "chunk_text": "ML is a subset...",
                    "similarity": 0.92,
                    "page": 3
                }
            ]
        }
    ),
    "sources": [...]
}
```

##### `stream_message(chat_id: int, message: str, db: Session) -> AsyncGenerator`

Stream AI response in real-time.

```python
from backend.services.chat_service import stream_message

async for chunk in stream_message(
    chat_id=1,
    message="Explain neural networks",
    db=db_session
):
    if chunk["type"] == "token":
        print(chunk["content"], end="", flush=True)
    elif chunk["type"] == "sources":
        print("\nSources:", chunk["data"])
```

**Stream Events:**
- `token`: Individual response token
- `sources`: Retrieved source documents
- `complete`: Final message metadata
- `error`: Error information

##### `get_chat_history(chat_id: int, limit: int, db: Session) -> List[Message]`

Retrieve chat message history.

```python
from backend.services.chat_service import get_chat_history

messages = get_chat_history(
    chat_id=1,
    limit=50,
    db=db_session
)

for msg in messages:
    print(f"{msg.role}: {msg.content}")
```

##### `delete_chat(chat_id: int, db: Session) -> None`

Delete a chat and all its messages.

```python
from backend.services.chat_service import delete_chat

delete_chat(chat_id=1, db=db_session)
```

**Best Practices:**

1. **Context Management**: Limit history to last N turns to avoid context overflow
2. **Source Attribution**: Always include retrieved sources in responses
3. **Error Recovery**: Save user messages even if AI response fails
4. **Streaming**: Use streaming for better user experience

---

### Project Service

**File:** `services/project_service.py`

Manages project lifecycle and ensures data isolation.

#### Key Functions

##### `create_project(name: str, description: str, db: Session) -> Project`

Create a new project with isolated resources.

**Process:**
1. Create project record in database
2. Initialize ChromaDB collection for project
3. Create storage directory for documents
4. Set up default configuration

```python
from backend.services.project_service import create_project

project = create_project(
    name="Research Project",
    description="AI and ML research papers",
    db=db_session
)

print(f"Project {project.id} created with collection 'project_{project.id}'")
```

##### `get_project_stats(project_id: int, db: Session) -> Dict`

Get comprehensive project statistics.

```python
from backend.services.project_service import get_project_stats

stats = get_project_stats(project_id=1, db=db_session)

print(f"""
Project Statistics:
- Documents: {stats['document_count']}
- Total chunks: {stats['chunk_count']}
- Chats: {stats['chat_count']}
- Total messages: {stats['message_count']}
- Storage used: {stats['storage_bytes']} bytes
- Last activity: {stats['last_activity']}
""")
```

**Stats Format:**
```python
{
    "project_id": 1,
    "document_count": 15,
    "chunk_count": 450,
    "chat_count": 5,
    "message_count": 78,
    "storage_bytes": 5242880,
    "last_activity": "2025-01-07T12:00:00Z",
    "created_at": "2025-01-01T10:00:00Z"
}
```

##### `delete_project(project_id: int, db: Session) -> None`

Delete project and all associated data.

**Cleanup Operations:**
1. Delete all documents from file system
2. Delete ChromaDB collection and embeddings
3. Delete all chat conversations and messages
4. Delete project record from database
5. Remove storage directory

```python
from backend.services.project_service import delete_project

delete_project(project_id=1, db=db_session)
# All data permanently removed
```

##### `duplicate_project(project_id: int, new_name: str, db: Session) -> Project`

Create a copy of a project (useful for experiments).

```python
from backend.services.project_service import duplicate_project

new_project = duplicate_project(
    project_id=1,
    new_name="Project Copy for Testing",
    db=db_session
)

# New project has copies of all documents and embeddings
# Chats are NOT copied (fresh start)
```

**Project Isolation:**

Each project maintains complete isolation:
- **Database**: Separate records with foreign key constraints
- **Vector Store**: Dedicated ChromaDB collection
- **File System**: Isolated directory structure
- **Queries**: Filtered by project_id at all levels

---

### Analytics Service

**File:** `services/analytics_service.py`

Provides analytics, visualizations, and insights into embeddings and RAG performance.

#### Key Functions

##### `get_embeddings_with_reduction(project_id: int, method: str, dimensions: int) -> Dict`

Get embeddings reduced to 2D or 3D for visualization.

**Parameters:**
- `project_id` (int): Project to analyze
- `method` (str): Reduction method (`pca`, `tsne`, `umap`)
- `dimensions` (int): Target dimensions (2 or 3)

```python
from backend.services.analytics_service import get_embeddings_with_reduction

data = await get_embeddings_with_reduction(
    project_id=1,
    method="tsne",
    dimensions=2
)

# Returns reduced embeddings ready for plotting
for point in data["embeddings"]:
    print(f"Doc: {point['document_name']}, Coords: {point['coordinates']}")
```

**Reduction Methods:**

1. **PCA (Principal Component Analysis)**
   - Fast and deterministic
   - Preserves global structure
   - Best for initial exploration

2. **t-SNE (t-Distributed Stochastic Neighbor Embedding)**
   - Preserves local structure
   - Good for cluster visualization
   - Slower than PCA

3. **UMAP (Uniform Manifold Approximation and Projection)**
   - Balance of speed and quality
   - Preserves both local and global structure
   - Best overall visualization

##### `compute_similarity_matrix(project_id: int, level: str, limit: int) -> Dict`

Compute pairwise similarity between documents or chunks.

**Parameters:**
- `level` (str): `document` (avg similarity) or `chunk` (individual chunks)
- `limit` (int): Maximum items to include (for performance)

```python
from backend.services.analytics_service import compute_similarity_matrix

matrix = await compute_similarity_matrix(
    project_id=1,
    level="document",
    limit=20
)

# Similarity matrix for heatmap visualization
print(matrix["similarity_matrix"])  # [[1.0, 0.85, ...], [0.85, 1.0, ...]]
print(matrix["labels"])  # ["doc1.pdf", "doc2.pdf", ...]
```

**Use Cases:**
- Identify duplicate or similar documents
- Find content clusters
- Detect outliers
- Validate embedding quality

##### `get_embedding_statistics(project_id: int) -> Dict`

Calculate comprehensive embedding statistics.

```python
from backend.services.analytics_service import get_embedding_statistics

stats = await get_embedding_statistics(project_id=1)

print(f"""
Embedding Statistics:
- Total chunks: {stats['total_chunks']}
- Embedding dimension: {stats['dimension']}
- Average norm: {stats['avg_norm']:.3f}
- Std dev norm: {stats['std_norm']:.3f}
- Min similarity: {stats['min_similarity']:.3f}
- Max similarity: {stats['max_similarity']:.3f}
- Avg similarity: {stats['avg_similarity']:.3f}
""")
```

**Statistics Included:**
- Chunk and document counts
- Embedding dimensions
- Vector norms (length)
- Similarity distribution
- Per-document breakdowns
- Outlier detection

##### `test_retrieval(project_id: int, query: str, k: int) -> Dict`

Test RAG retrieval quality.

```python
from backend.services.analytics_service import test_retrieval

results = await test_retrieval(
    project_id=1,
    query="What is deep learning?",
    k=5
)

print(f"Retrieval time: {results['retrieval_time_ms']}ms")
for i, result in enumerate(results['results']):
    print(f"{i+1}. {result['document_name']} (sim: {result['similarity']:.3f})")
    print(f"   {result['chunk_text'][:100]}...")
```

**Evaluation Metrics:**
- Retrieval latency
- Similarity scores
- Chunk diversity (from different docs)
- Relevance assessment

---

### File Storage

**File:** `services/file_storage.py`

Manages file system operations for uploaded documents.

#### Key Functions

##### `save_uploaded_file(file: UploadFile, project_id: int) -> str`

Save an uploaded file to the project directory.

**Process:**
1. Generate unique filename (prevents collisions)
2. Create project directory if needed
3. Save file to disk
4. Set appropriate permissions
5. Return file path

```python
from backend.services.file_storage import save_uploaded_file
from fastapi import UploadFile

file_path = await save_uploaded_file(
    file=uploaded_file,
    project_id=1
)

print(f"File saved to: {file_path}")
# /storage/documents/project_1/document_abc123.pdf
```

**Directory Structure:**
```
storage/documents/
├── project_1/
│   ├── document_abc123.pdf
│   ├── report_def456.docx
│   └── data_ghi789.xlsx
├── project_2/
│   └── notes_jkl012.txt
```

##### `delete_file(file_path: str) -> None`

Delete a file from storage.

```python
from backend.services.file_storage import delete_file

delete_file("/storage/documents/project_1/document_abc123.pdf")
```

##### `get_file_info(file_path: str) -> Dict`

Get detailed file information.

```python
from backend.services.file_storage import get_file_info

info = get_file_info("/storage/documents/project_1/doc.pdf")

print(f"""
File Information:
- Size: {info['size_bytes']} bytes ({info['size_human']})
- Created: {info['created_at']}
- Modified: {info['modified_at']}
- MIME type: {info['mime_type']}
- Checksum: {info['md5_hash']}
""")
```

##### `get_project_storage_size(project_id: int) -> int`

Calculate total storage used by a project.

```python
from backend.services.file_storage import get_project_storage_size

size_bytes = get_project_storage_size(project_id=1)
size_mb = size_bytes / (1024 * 1024)

print(f"Project uses {size_mb:.2f} MB of storage")
```

##### `cleanup_orphaned_files(db: Session) -> List[str]`

Remove files not referenced in database.

```python
from backend.services.file_storage import cleanup_orphaned_files

removed = cleanup_orphaned_files(db=db_session)

print(f"Cleaned up {len(removed)} orphaned files")
for file_path in removed:
    print(f"  - {file_path}")
```

**Best Practices:**

1. **Unique Filenames**: Always generate unique names to prevent collisions
2. **Validation**: Validate files before saving (size, type, content)
3. **Atomic Operations**: Use temp files and rename for atomic saves
4. **Cleanup**: Delete files when documents are removed from database
5. **Permissions**: Set appropriate file permissions for security
6. **Monitoring**: Track storage usage per project

---

## Usage Examples

### Complete Document Upload Flow

```python
from backend.services.document_processor import process_document, chunk_and_embed
from backend.services.file_storage import save_uploaded_file
from backend.services.project_service import get_project_stats
from backend.core.vectorstore import VectorStore
from backend.crud.document import create_document

async def upload_and_process_document(
    file: UploadFile,
    project_id: int,
    db: Session
):
    try:
        # 1. Save file to storage
        file_path = await save_uploaded_file(file, project_id)

        # 2. Create database record
        document = create_document(
            db=db,
            project_id=project_id,
            filename=file.filename,
            file_path=file_path,
            file_type=file.content_type,
            status="processing"
        )

        # 3. Extract text
        result = process_document(file_path, document.file_type)

        # 4. Chunk and embed
        chunks = await chunk_and_embed(
            text=result["text"],
            document_id=document.id,
            metadata=result["metadata"]
        )

        # 5. Store in vector database
        vectorstore = VectorStore()
        await vectorstore.add_documents(project_id, chunks)

        # 6. Update document status
        document.status = "completed"
        document.metadata = result["metadata"]
        db.commit()

        # 7. Log stats
        stats = get_project_stats(project_id, db)
        logger.info(f"Document processed. Project now has {stats['chunk_count']} chunks")

        return document

    except Exception as e:
        document.status = "failed"
        document.error_message = str(e)
        db.commit()
        raise
```

### Chat with Streaming

```python
from backend.services.chat_service import stream_message
import asyncio

async def chat_with_streaming(chat_id: int, message: str, db: Session):
    full_response = ""
    sources = []

    async for chunk in stream_message(chat_id, message, db):
        if chunk["type"] == "token":
            # Send to WebSocket
            full_response += chunk["content"]
            await websocket.send_json({
                "type": "token",
                "content": chunk["content"]
            })

        elif chunk["type"] == "sources":
            sources = chunk["data"]

        elif chunk["type"] == "complete":
            # Send final message
            await websocket.send_json({
                "type": "complete",
                "message_id": chunk["message_id"],
                "sources": sources
            })

    return full_response, sources
```

### Analytics Dashboard Data

```python
from backend.services.analytics_service import (
    get_embeddings_with_reduction,
    compute_similarity_matrix,
    get_embedding_statistics
)

async def get_analytics_dashboard_data(project_id: int):
    # Parallel data fetching
    embeddings_task = get_embeddings_with_reduction(
        project_id, method="tsne", dimensions=2
    )
    similarity_task = compute_similarity_matrix(
        project_id, level="document", limit=20
    )
    stats_task = get_embedding_statistics(project_id)

    # Wait for all
    embeddings, similarity, stats = await asyncio.gather(
        embeddings_task,
        similarity_task,
        stats_task
    )

    return {
        "embeddings": embeddings,
        "similarity": similarity,
        "statistics": stats
    }
```

---

## Best Practices

### 1. Error Handling

Always wrap service calls in try-except blocks and provide meaningful errors:

```python
from backend.services.document_processor import DocumentProcessingError

try:
    result = process_document(file_path, file_type)
except DocumentProcessingError as e:
    logger.error(f"Failed to process {file_path}: {e}")
    return {"error": str(e), "status": "failed"}
except Exception as e:
    logger.exception("Unexpected error in document processing")
    return {"error": "Internal server error", "status": "failed"}
```

### 2. Transaction Management

Use database transactions for multi-step operations:

```python
from sqlalchemy.orm import Session

def create_project_with_documents(name: str, files: List, db: Session):
    try:
        # Start transaction
        project = create_project(name, "", db)

        for file in files:
            document = create_document(db, project.id, file)

        db.commit()  # Commit all or nothing
        return project

    except Exception:
        db.rollback()  # Rollback on error
        raise
```

### 3. Async Operations

Use async for I/O-bound operations:

```python
import asyncio

async def process_multiple_documents(documents: List):
    # Process in parallel
    tasks = [process_document(doc.path, doc.type) for doc in documents]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Handle results
    for doc, result in zip(documents, results):
        if isinstance(result, Exception):
            logger.error(f"Failed to process {doc.path}: {result}")
        else:
            logger.info(f"Processed {doc.path} successfully")
```

### 4. Resource Cleanup

Always clean up resources:

```python
from contextlib import contextmanager

@contextmanager
def temporary_file(file_path: str):
    try:
        yield file_path
    finally:
        # Cleanup even if error occurs
        if os.path.exists(file_path):
            os.remove(file_path)

with temporary_file("temp.pdf") as path:
    process_document(path, "pdf")
    # File automatically deleted after block
```

### 5. Validation

Validate inputs early:

```python
def validate_project_id(project_id: int, db: Session):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project {project_id} not found")
    return project

def send_message(chat_id: int, message: str, db: Session):
    # Validate early
    if not message or not message.strip():
        raise ValueError("Message cannot be empty")

    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise ValueError(f"Chat {chat_id} not found")

    # Validate project exists
    validate_project_id(chat.project_id, db)

    # Proceed with processing
    ...
```

### 6. Logging

Add comprehensive logging:

```python
import logging

logger = logging.getLogger(__name__)

def process_document(file_path: str, file_type: str):
    logger.info(f"Processing document: {file_path} ({file_type})")

    try:
        result = extract_text(file_path, file_type)
        logger.info(f"Extracted {result['metadata']['word_count']} words")
        return result

    except Exception as e:
        logger.error(f"Failed to process {file_path}: {e}", exc_info=True)
        raise
```

### 7. Performance Monitoring

Track performance metrics:

```python
import time

def track_performance(func):
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start

        logger.info(f"{func.__name__} took {duration:.2f}s")
        return result

    return wrapper

@track_performance
async def process_document(file_path: str, file_type: str):
    # Processing logic
    ...
```

---

## Testing Services

### Unit Testing

```python
import pytest
from backend.services.document_processor import process_document

def test_process_pdf():
    result = process_document("test_files/sample.pdf", "pdf")

    assert result["text"] is not None
    assert len(result["text"]) > 0
    assert result["metadata"]["page_count"] > 0

@pytest.mark.asyncio
async def test_chunk_and_embed():
    chunks = await chunk_and_embed(
        text="Sample text for testing",
        document_id=1,
        metadata={}
    )

    assert len(chunks) > 0
    assert "embedding" in chunks[0]
    assert len(chunks[0]["embedding"]) == 768  # nomic-embed-text dimension
```

### Integration Testing

```python
from backend.services.chat_service import send_message
from backend.core.database import SessionLocal

@pytest.mark.integration
async def test_complete_chat_flow():
    db = SessionLocal()

    try:
        # Create project
        project = create_project("Test Project", "", db)

        # Upload document
        # ... (upload logic)

        # Create chat
        chat = create_chat(project.id, "Test Chat", db)

        # Send message
        response = await send_message(
            chat_id=chat.id,
            message="Test question",
            db=db
        )

        assert response["assistant_message"] is not None
        assert len(response["sources"]) > 0

    finally:
        db.close()
```

---

## Troubleshooting

### Common Issues

1. **File Processing Fails**
   - Check file permissions
   - Verify file is not corrupted
   - Ensure sufficient disk space
   - Check supported format

2. **Embedding Generation Slow**
   - Use batch processing
   - Check Ollama is running locally
   - Consider smaller embedding model
   - Monitor system resources

3. **Storage Issues**
   - Check disk space
   - Verify directory permissions
   - Clean up orphaned files
   - Monitor project storage limits

4. **Database Errors**
   - Check migrations are up to date
   - Verify database file permissions
   - Monitor database size
   - Use proper transaction handling

---

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Ollama Documentation](https://github.com/ollama/ollama)
- [ChromaDB Documentation](https://docs.trychroma.com/)
