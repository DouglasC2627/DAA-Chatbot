# CRUD Operations Documentation

This document provides comprehensive documentation for all CRUD (Create, Read, Update, Delete) operations in the DAA Chatbot backend.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [CRUD Modules](#crud-modules)
  - [Project CRUD](#project-crud)
  - [Document CRUD](#document-crud)
  - [Chat CRUD](#chat-crud)
  - [Message CRUD](#message-crud)
  - [Settings CRUD](#settings-crud)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)

## Overview

The `crud/` directory contains database access layer functions that provide a clean, reusable interface for database operations. CRUD modules abstract SQLAlchemy queries and provide type-safe functions for interacting with the database.

```
backend/crud/
├── __init__.py
├── project.py       # Project CRUD operations
├── document.py      # Document CRUD operations
├── chat.py          # Chat and Message CRUD operations
└── settings.py      # Settings CRUD operations
```

**Key Principles:**
- **Separation of Concerns**: CRUD functions only handle database operations
- **Type Safety**: Use Pydantic models for input validation
- **Reusability**: Shared by API routes and services
- **Session Management**: Receive database session as parameter
- **No Business Logic**: Pure data access layer

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    API Routes                           │
│              (Handle HTTP requests)                      │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  Services Layer                         │
│          (Business logic and orchestration)              │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                   CRUD Layer                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   Project    │  │   Document   │  │     Chat     │  │
│  │     CRUD     │  │     CRUD     │  │     CRUD     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│               SQLAlchemy Models                         │
│                   (ORM Layer)                           │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  SQLite Database                        │
└─────────────────────────────────────────────────────────┘
```

## CRUD Modules

### Project CRUD

**File:** `crud/project.py`

CRUD operations for Project model.

#### Functions

##### `get_project(db: Session, project_id: int) -> Project | None`

Get a single project by ID.

**Parameters:**
- `db`: Database session
- `project_id`: Project ID

**Returns:** Project object or None if not found

```python
from backend.crud.project import get_project

project = get_project(db, project_id=1)
if project:
    print(f"Found: {project.name}")
else:
    print("Project not found")
```

##### `get_projects(db: Session, skip: int = 0, limit: int = 100) -> List[Project]`

Get all projects with pagination.

**Parameters:**
- `db`: Database session
- `skip`: Number of records to skip
- `limit`: Maximum records to return

**Returns:** List of Project objects

```python
from backend.crud.project import get_projects

# Get first 10 projects
projects = get_projects(db, skip=0, limit=10)

# Get next 10 projects
projects = get_projects(db, skip=10, limit=10)

for project in projects:
    print(f"{project.id}: {project.name}")
```

##### `get_project_by_name(db: Session, name: str) -> Project | None`

Get a project by exact name match.

```python
from backend.crud.project import get_project_by_name

project = get_project_by_name(db, name="AI Research")
if project:
    print(f"Found project with ID: {project.id}")
```

##### `create_project(db: Session, name: str, description: str | None = None) -> Project`

Create a new project.

**Parameters:**
- `db`: Database session
- `name`: Project name (required)
- `description`: Project description (optional)

**Returns:** Created Project object

```python
from backend.crud.project import create_project

project = create_project(
    db,
    name="Machine Learning Research",
    description="Collection of ML papers and notes"
)

print(f"Created project {project.id}")
```

**Raises:**
- `ValueError`: If name is empty or None
- `IntegrityError`: If project with same name exists (if unique constraint)

##### `update_project(db: Session, project_id: int, name: str | None = None, description: str | None = None) -> Project | None`

Update a project's fields.

**Parameters:**
- `db`: Database session
- `project_id`: Project ID to update
- `name`: New name (optional)
- `description`: New description (optional)

**Returns:** Updated Project or None if not found

```python
from backend.crud.project import update_project

project = update_project(
    db,
    project_id=1,
    name="Updated Project Name",
    description="Updated description"
)

if project:
    print(f"Updated: {project.name}")
```

##### `delete_project(db: Session, project_id: int) -> bool`

Delete a project.

**Parameters:**
- `db`: Database session
- `project_id`: Project ID to delete

**Returns:** True if deleted, False if not found

```python
from backend.crud.project import delete_project

success = delete_project(db, project_id=1)
if success:
    print("Project deleted")
else:
    print("Project not found")
```

**Note:** This only deletes the database record. Additional cleanup (files, ChromaDB collection) should be handled by the service layer.

##### `get_project_document_count(db: Session, project_id: int) -> int`

Get the number of documents in a project.

```python
from backend.crud.project import get_project_document_count

count = get_project_document_count(db, project_id=1)
print(f"Project has {count} documents")
```

##### `get_project_chat_count(db: Session, project_id: int) -> int`

Get the number of chats in a project.

```python
from backend.crud.project import get_project_chat_count

count = get_project_chat_count(db, project_id=1)
print(f"Project has {count} chats")
```

---

### Document CRUD

**File:** `crud/document.py`

CRUD operations for Document model.

#### Functions

##### `get_document(db: Session, document_id: int) -> Document | None`

Get a single document by ID.

```python
from backend.crud.document import get_document

doc = get_document(db, document_id=1)
if doc:
    print(f"Document: {doc.filename}")
```

##### `get_documents(db: Session, project_id: int, skip: int = 0, limit: int = 100) -> List[Document]`

Get all documents in a project.

```python
from backend.crud.document import get_documents

docs = get_documents(db, project_id=1, skip=0, limit=50)

for doc in docs:
    print(f"{doc.filename} - {doc.status}")
```

##### `get_documents_by_status(db: Session, project_id: int, status: str) -> List[Document]`

Get documents filtered by status.

**Status Values:** `processing`, `completed`, `failed`

```python
from backend.crud.document import get_documents_by_status

# Get all failed documents
failed = get_documents_by_status(db, project_id=1, status="failed")

for doc in failed:
    print(f"Failed: {doc.filename} - {doc.error_message}")
```

##### `create_document(db: Session, project_id: int, filename: str, file_path: str, file_type: str, file_size: int) -> Document`

Create a new document record.

```python
from backend.crud.document import create_document

doc = create_document(
    db,
    project_id=1,
    filename="research_paper.pdf",
    file_path="/storage/documents/project_1/abc123.pdf",
    file_type="pdf",
    file_size=1024000
)

print(f"Created document {doc.id} with status: {doc.status}")
```

**Default Values:**
- `status`: "processing"
- `created_at`: Current timestamp

##### `update_document_status(db: Session, document_id: int, status: str, error_message: str | None = None) -> Document | None`

Update document processing status.

```python
from backend.crud.document import update_document_status

# Mark as completed
doc = update_document_status(db, document_id=1, status="completed")

# Mark as failed with error
doc = update_document_status(
    db,
    document_id=2,
    status="failed",
    error_message="Unsupported PDF format"
)
```

##### `update_document_metadata(db: Session, document_id: int, metadata: dict) -> Document | None`

Update document metadata after processing.

```python
from backend.crud.document import update_document_metadata

metadata = {
    "page_count": 15,
    "word_count": 7500,
    "chunk_count": 38
}

doc = update_document_metadata(db, document_id=1, metadata=metadata)
```

##### `set_document_processed(db: Session, document_id: int) -> Document | None`

Mark document as processed (sets processed_at timestamp).

```python
from backend.crud.document import set_document_processed

doc = set_document_processed(db, document_id=1)
print(f"Processed at: {doc.processed_at}")
```

##### `delete_document(db: Session, document_id: int) -> bool`

Delete a document record.

```python
from backend.crud.document import delete_document

success = delete_document(db, document_id=1)
```

**Note:** This only deletes the database record. File deletion should be handled separately.

---

### Chat CRUD

**File:** `crud/chat.py`

CRUD operations for Chat and Message models.

#### Chat Functions

##### `get_chat(db: Session, chat_id: int) -> Chat | None`

Get a single chat by ID.

```python
from backend.crud.chat import get_chat

chat = get_chat(db, chat_id=1)
if chat:
    print(f"Chat: {chat.title}")
```

##### `get_chats(db: Session, project_id: int, skip: int = 0, limit: int = 100) -> List[Chat]`

Get all chats in a project.

```python
from backend.crud.chat import get_chats

chats = get_chats(db, project_id=1, limit=10)

for chat in chats:
    print(f"{chat.id}: {chat.title} - {chat.updated_at}")
```

##### `create_chat(db: Session, project_id: int, title: str) -> Chat`

Create a new chat.

```python
from backend.crud.chat import create_chat

chat = create_chat(
    db,
    project_id=1,
    title="Questions about Machine Learning"
)

print(f"Created chat {chat.id}")
```

##### `update_chat(db: Session, chat_id: int, title: str) -> Chat | None`

Update chat title.

```python
from backend.crud.chat import update_chat

chat = update_chat(
    db,
    chat_id=1,
    title="ML Discussion - Updated"
)
```

##### `delete_chat(db: Session, chat_id: int) -> bool`

Delete a chat and all its messages.

```python
from backend.crud.chat import delete_chat

success = delete_chat(db, chat_id=1)
```

**Note:** Messages are cascade deleted automatically.

#### Message Functions

##### `get_message(db: Session, message_id: int) -> Message | None`

Get a single message by ID.

```python
from backend.crud.chat import get_message

msg = get_message(db, message_id=1)
if msg:
    print(f"{msg.role}: {msg.content}")
```

##### `get_messages(db: Session, chat_id: int, skip: int = 0, limit: int = 100) -> List[Message]`

Get all messages in a chat.

```python
from backend.crud.chat import get_messages

messages = get_messages(db, chat_id=1, limit=50)

for msg in messages:
    print(f"[{msg.created_at}] {msg.role}: {msg.content}")
```

##### `get_recent_messages(db: Session, chat_id: int, limit: int = 10) -> List[Message]`

Get the N most recent messages (for context window).

```python
from backend.crud.chat import get_recent_messages

# Get last 5 messages for context
recent = get_recent_messages(db, chat_id=1, limit=5)
```

##### `create_message(db: Session, chat_id: int, role: str, content: str, metadata: dict | None = None) -> Message`

Create a new message.

**Role Values:** `user`, `assistant`, `system`

```python
from backend.crud.chat import create_message

# User message
user_msg = create_message(
    db,
    chat_id=1,
    role="user",
    content="What is deep learning?"
)

# Assistant message with sources
assistant_msg = create_message(
    db,
    chat_id=1,
    role="assistant",
    content="Deep learning is a subset of machine learning...",
    metadata={
        "sources": [
            {
                "document_id": 1,
                "document_name": "ml_intro.pdf",
                "similarity": 0.92
            }
        ]
    }
)
```

##### `delete_message(db: Session, message_id: int) -> bool`

Delete a single message.

```python
from backend.crud.chat import delete_message

success = delete_message(db, message_id=1)
```

##### `get_message_count(db: Session, chat_id: int) -> int`

Get total message count in a chat.

```python
from backend.crud.chat import get_message_count

count = get_message_count(db, chat_id=1)
print(f"Chat has {count} messages")
```

---

### Settings CRUD

**File:** `crud/settings.py`

CRUD operations for Settings model.

#### Functions

##### `get_setting(db: Session, key: str) -> Settings | None`

Get a setting by key.

```python
from backend.crud.settings import get_setting
import json

setting = get_setting(db, key="llm.default_model")
if setting:
    value = json.loads(setting.value)
    print(f"Default model: {value}")
```

##### `get_settings_by_category(db: Session, category: str) -> List[Settings]`

Get all settings in a category.

```python
from backend.crud.settings import get_settings_by_category

rag_settings = get_settings_by_category(db, category="rag")

for setting in rag_settings:
    print(f"{setting.key}: {setting.value}")
```

##### `create_setting(db: Session, key: str, value: str, category: str, description: str | None = None) -> Settings`

Create a new setting.

```python
from backend.crud.settings import create_setting
import json

setting = create_setting(
    db,
    key="rag.chunk_size",
    value=json.dumps(1000),
    category="rag",
    description="Default chunk size for text splitting"
)
```

##### `update_setting(db: Session, key: str, value: str) -> Settings | None`

Update a setting's value.

```python
from backend.crud.settings import update_setting
import json

setting = update_setting(
    db,
    key="rag.chunk_size",
    value=json.dumps(1500)
)
```

##### `delete_setting(db: Session, key: str) -> bool`

Delete a setting.

```python
from backend.crud.settings import delete_setting

success = delete_setting(db, key="old.setting")
```

---

## Usage Examples

### Complete Workflow

```python
from backend.crud.project import create_project
from backend.crud.document import create_document, update_document_status
from backend.crud.chat import create_chat, create_message
from backend.core.database import SessionLocal

db = SessionLocal()

try:
    # 1. Create project
    project = create_project(
        db,
        name="AI Research",
        description="Machine learning papers"
    )

    # 2. Add documents
    doc = create_document(
        db,
        project_id=project.id,
        filename="paper.pdf",
        file_path="/storage/docs/paper.pdf",
        file_type="pdf",
        file_size=500000
    )

    # 3. Update document after processing
    doc = update_document_status(
        db,
        document_id=doc.id,
        status="completed"
    )

    # 4. Create chat
    chat = create_chat(
        db,
        project_id=project.id,
        title="Discussion about ML"
    )

    # 5. Add messages
    user_msg = create_message(
        db,
        chat_id=chat.id,
        role="user",
        content="What is ML?"
    )

    ai_msg = create_message(
        db,
        chat_id=chat.id,
        role="assistant",
        content="Machine learning is...",
        metadata={"sources": [...]}
    )

    db.commit()
    print("Workflow completed successfully")

except Exception as e:
    db.rollback()
    print(f"Error: {e}")
    raise

finally:
    db.close()
```

### Pagination

```python
from backend.crud.project import get_projects

# Paginate through all projects
page_size = 10
page = 0

while True:
    projects = get_projects(db, skip=page * page_size, limit=page_size)

    if not projects:
        break

    for project in projects:
        print(f"Page {page}: {project.name}")

    page += 1
```

### Filtering and Searching

```python
from backend.models.document import Document
from sqlalchemy import and_, or_

# Complex query using CRUD + SQLAlchemy
from backend.crud.document import get_documents

# Get completed PDF documents
docs = db.query(Document).filter(
    and_(
        Document.project_id == 1,
        Document.status == "completed",
        Document.file_type == "pdf"
    )
).all()

# Search documents by filename
search_term = "research"
docs = db.query(Document).filter(
    Document.filename.ilike(f"%{search_term}%")
).all()
```

### Batch Operations

```python
from backend.crud.document import create_document

# Batch create documents
documents_to_create = [
    {"filename": "doc1.pdf", "file_path": "/path/1.pdf", ...},
    {"filename": "doc2.pdf", "file_path": "/path/2.pdf", ...},
]

created_docs = []
for doc_data in documents_to_create:
    doc = create_document(db, project_id=1, **doc_data)
    created_docs.append(doc)

db.commit()  # Commit all at once
```

---

## Best Practices

### 1. Session Management

Never create sessions inside CRUD functions. Always receive as parameter:

```python
# Good
def get_project(db: Session, project_id: int) -> Project | None:
    return db.query(Project).filter(Project.id == project_id).first()

# Bad - Creates new session
def get_project_bad(project_id: int) -> Project | None:
    db = SessionLocal()  # Don't do this
    return db.query(Project).filter(Project.id == project_id).first()
```

### 2. Type Hints

Always use type hints for better IDE support and error detection:

```python
from typing import List, Optional
from sqlalchemy.orm import Session

def get_projects(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[Project]:
    return db.query(Project).offset(skip).limit(limit).all()
```

### 3. Error Handling

Let exceptions bubble up to the service/route layer:

```python
# Good - Simple and clean
def get_project(db: Session, project_id: int) -> Project | None:
    return db.query(Project).filter(Project.id == project_id).first()

# Bad - Too much error handling in CRUD layer
def get_project_bad(db: Session, project_id: int):
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404)  # Don't handle HTTP in CRUD
        return project
    except Exception as e:
        logger.error(e)  # Logging is OK, but don't catch everything
        return None
```

### 4. Return Values

Be consistent with return values:

```python
# Return None if not found
def get_project(db: Session, project_id: int) -> Project | None:
    return db.query(Project).filter(Project.id == project_id).first()

# Return boolean for delete operations
def delete_project(db: Session, project_id: int) -> bool:
    project = get_project(db, project_id)
    if project:
        db.delete(project)
        db.commit()
        return True
    return False

# Return created object for create operations
def create_project(db: Session, name: str) -> Project:
    project = Project(name=name)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
```

### 5. Commit Strategy

Generally, don't commit inside CRUD functions (except for create operations):

```python
# Good - No commit, let caller handle
def update_project(db: Session, project_id: int, name: str) -> Project | None:
    project = get_project(db, project_id)
    if project:
        project.name = name
        # No commit here
    return project

# Good - Commit in create operations
def create_project(db: Session, name: str) -> Project:
    project = Project(name=name)
    db.add(project)
    db.commit()  # Commit is OK for creates
    db.refresh(project)
    return project
```

### 6. Query Optimization

Use select_in_load or joined_load for relationships:

```python
from sqlalchemy.orm import joinedload

def get_project_with_documents(db: Session, project_id: int) -> Project | None:
    return db.query(Project).options(
        joinedload(Project.documents)
    ).filter(Project.id == project_id).first()
```

### 7. Input Validation

Validate inputs before database operations:

```python
def create_project(db: Session, name: str, description: str | None = None) -> Project:
    # Validate
    if not name or not name.strip():
        raise ValueError("Project name cannot be empty")

    if len(name) > 255:
        raise ValueError("Project name too long (max 255 characters)")

    # Create
    project = Project(name=name.strip(), description=description)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project
```

---

## Testing CRUD Functions

```python
import pytest
from backend.crud.project import create_project, get_project, delete_project
from backend.core.database import SessionLocal

@pytest.fixture
def db():
    db = SessionLocal()
    yield db
    db.close()

def test_create_project(db):
    project = create_project(db, name="Test Project")
    assert project.id is not None
    assert project.name == "Test Project"

def test_get_project(db):
    # Create
    created = create_project(db, name="Test")

    # Get
    retrieved = get_project(db, created.id)
    assert retrieved is not None
    assert retrieved.id == created.id

def test_delete_project(db):
    # Create
    project = create_project(db, name="To Delete")

    # Delete
    success = delete_project(db, project.id)
    assert success is True

    # Verify deleted
    deleted = get_project(db, project.id)
    assert deleted is None
```

---

## Additional Resources

- [SQLAlchemy Query API](https://docs.sqlalchemy.org/en/20/orm/queryguide/)
- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/20/orm/session_basics.html)
- [FastAPI Database Guide](https://fastapi.tiangolo.com/tutorial/sql-databases/)
