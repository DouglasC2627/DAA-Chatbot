# Database Models Documentation

This document provides comprehensive documentation for all SQLAlchemy database models in the DAA Chatbot backend.

## Table of Contents

- [Overview](#overview)
- [Database Schema](#database-schema)
- [Models](#models)
  - [Project](#project)
  - [Document](#document)
  - [Chat](#chat)
  - [Message](#message)
  - [Settings](#settings)
- [Relationships](#relationships)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)

## Overview

The `models/` directory contains SQLAlchemy ORM (Object-Relational Mapping) models that define the database schema and relationships. All models inherit from a declarative base and use SQLite as the database backend.

```
backend/models/
├── __init__.py
├── project.py       # Project model
├── document.py      # Document model
├── chat.py          # Chat and Message models
└── settings.py      # Application settings model
```

**Technology Stack:**
- **ORM**: SQLAlchemy 2.0
- **Database**: SQLite (for local storage)
- **Migrations**: Alembic
- **Type Hints**: Full Python type annotations

## Database Schema

```
┌─────────────────┐
│    Settings     │
│ (app config)    │
└─────────────────┘

┌─────────────────┐
│    Project      │
│  id (PK)        │
│  name           │
│  description    │
│  created_at     │
│  updated_at     │
└────────┬────────┘
         │
         │ 1:N
         │
    ┌────┴─────────────────────┐
    │                          │
┌───▼──────────┐       ┌──────▼──────┐
│  Document    │       │    Chat     │
│  id (PK)     │       │  id (PK)    │
│  project_id  │       │  project_id │
│  filename    │       │  title      │
│  file_path   │       │  created_at │
│  file_type   │       │  updated_at │
│  status      │       └──────┬──────┘
│  metadata    │              │
│  created_at  │              │ 1:N
└──────────────┘              │
                         ┌────▼──────┐
                         │  Message  │
                         │  id (PK)  │
                         │  chat_id  │
                         │  role     │
                         │  content  │
                         │  metadata │
                         └───────────┘
```

## Models

### Project

**File:** `models/project.py`

Represents an isolated workspace containing documents and chats.

#### Schema

```python
class Project(Base):
    __tablename__ = "projects"

    id: int                    # Primary key (auto-increment)
    name: str                  # Project name (required, max 255 chars)
    description: str | None    # Optional description (text field)
    created_at: datetime       # Creation timestamp (auto-set)
    updated_at: datetime       # Last modification timestamp (auto-update)

    # Relationships
    documents: List[Document]  # One-to-many with Document
    chats: List[Chat]          # One-to-many with Chat
```

#### Field Details

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | Primary Key, Auto-increment | Unique identifier |
| `name` | String(255) | NOT NULL, Indexed | Project name |
| `description` | Text | Nullable | Project description |
| `created_at` | DateTime | NOT NULL, Default: now() | Creation timestamp |
| `updated_at` | DateTime | NOT NULL, Default: now(), onupdate: now() | Last update timestamp |

#### Indexes

- `ix_projects_name`: Index on `name` for faster lookup
- `ix_projects_created_at`: Index on `created_at` for chronological queries

#### Example Usage

```python
from backend.models.project import Project
from backend.core.database import SessionLocal
from datetime import datetime

# Create a new project
project = Project(
    name="AI Research",
    description="Collection of AI and ML research papers"
)

db = SessionLocal()
db.add(project)
db.commit()
db.refresh(project)

print(f"Created project {project.id}: {project.name}")
print(f"Created at: {project.created_at}")

# Query projects
projects = db.query(Project).filter(Project.name.like("%AI%")).all()

# Access related documents
for doc in project.documents:
    print(f"  Document: {doc.filename}")

# Access related chats
for chat in project.chats:
    print(f"  Chat: {chat.title}")
```

#### Cascade Deletion

When a project is deleted, all related records are also deleted:
- All documents (and their files)
- All chats and messages
- ChromaDB collection

---

### Document

**File:** `models/document.py`

Represents an uploaded document that has been processed and embedded.

#### Schema

```python
class Document(Base):
    __tablename__ = "documents"

    id: int                    # Primary key
    project_id: int            # Foreign key to Project
    filename: str              # Original filename
    file_path: str             # Storage path on disk
    file_type: str             # File extension (pdf, docx, etc.)
    file_size: int             # Size in bytes
    status: str                # processing, completed, failed
    error_message: str | None  # Error details if failed
    metadata: dict | None      # JSON field for file metadata
    created_at: datetime       # Upload timestamp
    processed_at: datetime     # Processing completion timestamp

    # Relationships
    project: Project           # Many-to-one with Project
```

#### Field Details

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | Primary Key | Unique identifier |
| `project_id` | Integer | Foreign Key (projects.id), NOT NULL, Indexed | Parent project |
| `filename` | String(255) | NOT NULL | Original filename |
| `file_path` | String(512) | NOT NULL, Unique | Storage path |
| `file_type` | String(50) | NOT NULL | File extension |
| `file_size` | BigInteger | NOT NULL | Size in bytes |
| `status` | String(50) | NOT NULL, Default: "processing" | Processing status |
| `error_message` | Text | Nullable | Error details |
| `metadata` | JSON | Nullable | File-specific metadata |
| `created_at` | DateTime | NOT NULL, Default: now() | Upload time |
| `processed_at` | DateTime | Nullable | Processing completion time |

#### Status Values

- `processing`: Document is being processed
- `completed`: Successfully processed and embedded
- `failed`: Processing failed (see `error_message`)

#### Metadata Structure

The `metadata` JSON field stores file-specific information:

```python
# PDF metadata
{
    "page_count": 10,
    "word_count": 5000,
    "char_count": 30000,
    "chunk_count": 25,
    "has_images": true,
    "language": "en"
}

# DOCX metadata
{
    "paragraph_count": 45,
    "table_count": 3,
    "section_count": 5,
    "word_count": 3000,
    "chunk_count": 15
}

# CSV metadata
{
    "row_count": 1000,
    "column_count": 10,
    "columns": ["Name", "Age", "City"],
    "chunk_count": 50
}
```

#### Example Usage

```python
from backend.models.document import Document
from backend.models.project import Project

# Create a document
document = Document(
    project_id=1,
    filename="research_paper.pdf",
    file_path="/storage/documents/project_1/abc123.pdf",
    file_type="pdf",
    file_size=1024000,
    status="processing"
)

db.add(document)
db.commit()

# Update after processing
document.status = "completed"
document.processed_at = datetime.utcnow()
document.metadata = {
    "page_count": 15,
    "word_count": 7500,
    "chunk_count": 38
}
db.commit()

# Query documents by project
docs = db.query(Document).filter(
    Document.project_id == 1,
    Document.status == "completed"
).all()

# Query failed documents
failed = db.query(Document).filter(
    Document.status == "failed"
).all()

for doc in failed:
    print(f"Failed: {doc.filename} - {doc.error_message}")
```

#### Indexes

- `ix_documents_project_id`: Fast lookup by project
- `ix_documents_status`: Fast filtering by status
- `ix_documents_created_at`: Chronological queries

---

### Chat

**File:** `models/chat.py`

Represents a conversation thread within a project.

#### Schema

```python
class Chat(Base):
    __tablename__ = "chats"

    id: int                    # Primary key
    project_id: int            # Foreign key to Project
    title: str                 # Conversation title
    created_at: datetime       # Creation timestamp
    updated_at: datetime       # Last message timestamp

    # Relationships
    project: Project           # Many-to-one with Project
    messages: List[Message]    # One-to-many with Message
```

#### Field Details

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | Primary Key | Unique identifier |
| `project_id` | Integer | Foreign Key (projects.id), NOT NULL, Indexed | Parent project |
| `title` | String(255) | NOT NULL | Conversation title |
| `created_at` | DateTime | NOT NULL, Default: now() | Creation time |
| `updated_at` | DateTime | NOT NULL, Default: now(), onupdate: now() | Last activity |

#### Example Usage

```python
from backend.models.chat import Chat, Message

# Create a chat
chat = Chat(
    project_id=1,
    title="Discussion about ML"
)

db.add(chat)
db.commit()

# Access messages
for msg in chat.messages:
    print(f"{msg.role}: {msg.content}")

# Get recent chats
recent = db.query(Chat).filter(
    Chat.project_id == 1
).order_by(Chat.updated_at.desc()).limit(10).all()

# Count messages in chat
message_count = db.query(Message).filter(Message.chat_id == chat.id).count()
print(f"Chat has {message_count} messages")
```

#### Indexes

- `ix_chats_project_id`: Fast lookup by project
- `ix_chats_updated_at`: Recent conversations first

---

### Message

**File:** `models/chat.py`

Represents a single message in a chat conversation.

#### Schema

```python
class Message(Base):
    __tablename__ = "messages"

    id: int                    # Primary key
    chat_id: int               # Foreign key to Chat
    role: str                  # user, assistant, system
    content: str               # Message text
    metadata: dict | None      # JSON field for sources, etc.
    created_at: datetime       # Message timestamp

    # Relationships
    chat: Chat                 # Many-to-one with Chat
```

#### Field Details

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | Primary Key | Unique identifier |
| `chat_id` | Integer | Foreign Key (chats.id), NOT NULL, Indexed | Parent chat |
| `role` | String(50) | NOT NULL | Message sender role |
| `content` | Text | NOT NULL | Message text content |
| `metadata` | JSON | Nullable | Additional data (sources, etc.) |
| `created_at` | DateTime | NOT NULL, Default: now() | Message timestamp |

#### Role Values

- `user`: Message from the user
- `assistant`: Message from the AI
- `system`: System message (instructions, errors)

#### Metadata Structure

For assistant messages, metadata contains source attribution:

```python
{
    "sources": [
        {
            "document_id": 1,
            "document_name": "ml_intro.pdf",
            "chunk_text": "Machine learning is...",
            "chunk_index": 5,
            "page": 3,
            "similarity": 0.92
        }
    ],
    "model": "llama3.2",
    "generation_time_ms": 1500,
    "retrieval_time_ms": 45
}
```

#### Example Usage

```python
from backend.models.chat import Message

# Create user message
user_msg = Message(
    chat_id=1,
    role="user",
    content="What is machine learning?"
)

db.add(user_msg)
db.commit()

# Create assistant message with sources
assistant_msg = Message(
    chat_id=1,
    role="assistant",
    content="Machine learning is a subset of AI...",
    metadata={
        "sources": [
            {
                "document_id": 1,
                "document_name": "ml_intro.pdf",
                "chunk_text": "ML is a subset of AI...",
                "similarity": 0.92
            }
        ]
    }
)

db.add(assistant_msg)
db.commit()

# Query chat history
history = db.query(Message).filter(
    Message.chat_id == 1
).order_by(Message.created_at.asc()).all()

for msg in history:
    print(f"[{msg.created_at}] {msg.role}: {msg.content}")
```

#### Indexes

- `ix_messages_chat_id`: Fast lookup by chat
- `ix_messages_created_at`: Chronological ordering

---

### Settings

**File:** `models/settings.py`

Stores application configuration and user preferences.

#### Schema

```python
class Settings(Base):
    __tablename__ = "settings"

    id: int                    # Primary key
    key: str                   # Setting key (unique)
    value: str                 # Setting value (JSON string)
    category: str              # Setting category
    description: str | None    # Human-readable description
    updated_at: datetime       # Last update timestamp
```

#### Field Details

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | Integer | Primary Key | Unique identifier |
| `key` | String(100) | NOT NULL, Unique | Setting key |
| `value` | Text | NOT NULL | Setting value (JSON) |
| `category` | String(50) | NOT NULL, Indexed | Setting category |
| `description` | Text | Nullable | Setting description |
| `updated_at` | DateTime | NOT NULL, Default: now(), onupdate: now() | Last update |

#### Categories

- `llm`: LLM-related settings (model, temperature, etc.)
- `rag`: RAG configuration (chunk size, retrieval_k, etc.)
- `ui`: UI preferences (theme, language, etc.)
- `system`: System settings (storage limits, etc.)

#### Example Usage

```python
from backend.models.settings import Settings
import json

# Create setting
setting = Settings(
    key="llm.default_model",
    value=json.dumps("llama3.2"),
    category="llm",
    description="Default LLM model for generation"
)

db.add(setting)
db.commit()

# Get setting
llm_model = db.query(Settings).filter(
    Settings.key == "llm.default_model"
).first()

model_value = json.loads(llm_model.value)
print(f"Default model: {model_value}")

# Update setting
llm_model.value = json.dumps("llama3.2:latest")
db.commit()

# Get all settings by category
rag_settings = db.query(Settings).filter(
    Settings.category == "rag"
).all()

for setting in rag_settings:
    print(f"{setting.key}: {json.loads(setting.value)}")
```

---

## Relationships

### Project ↔ Document (One-to-Many)

```python
# From Project
project = db.query(Project).first()
documents = project.documents  # List of all documents

# From Document
document = db.query(Document).first()
project = document.project  # Parent project
```

### Project ↔ Chat (One-to-Many)

```python
# From Project
project = db.query(Project).first()
chats = project.chats  # List of all chats

# From Chat
chat = db.query(Chat).first()
project = chat.project  # Parent project
```

### Chat ↔ Message (One-to-Many)

```python
# From Chat
chat = db.query(Chat).first()
messages = chat.messages  # List of all messages

# From Message
message = db.query(Message).first()
chat = message.chat  # Parent chat
```

### Cascade Deletion

Relationships use cascade deletion to maintain referential integrity:

```python
# Delete project → deletes all documents, chats, and messages
db.delete(project)
db.commit()

# Delete chat → deletes all messages
db.delete(chat)
db.commit()

# Delete document → removes from database only (file requires separate cleanup)
db.delete(document)
db.commit()
```

---

## Usage Examples

### Complete Workflow

```python
from backend.models.project import Project
from backend.models.document import Document
from backend.models.chat import Chat, Message
from backend.core.database import SessionLocal
from datetime import datetime

db = SessionLocal()

# 1. Create project
project = Project(
    name="AI Research Project",
    description="Collection of AI papers and discussions"
)
db.add(project)
db.commit()
db.refresh(project)

# 2. Add documents
doc1 = Document(
    project_id=project.id,
    filename="paper1.pdf",
    file_path="/storage/docs/paper1.pdf",
    file_type="pdf",
    file_size=500000,
    status="completed",
    metadata={"page_count": 10, "word_count": 5000}
)

doc2 = Document(
    project_id=project.id,
    filename="notes.txt",
    file_path="/storage/docs/notes.txt",
    file_type="txt",
    file_size=10000,
    status="completed",
    metadata={"line_count": 200}
)

db.add_all([doc1, doc2])
db.commit()

# 3. Create chat
chat = Chat(
    project_id=project.id,
    title="Questions about AI"
)
db.add(chat)
db.commit()
db.refresh(chat)

# 4. Add messages
user_msg = Message(
    chat_id=chat.id,
    role="user",
    content="What is deep learning?"
)

assistant_msg = Message(
    chat_id=chat.id,
    role="assistant",
    content="Deep learning is a subset of machine learning...",
    metadata={
        "sources": [
            {
                "document_id": doc1.id,
                "document_name": doc1.filename,
                "similarity": 0.95
            }
        ]
    }
)

db.add_all([user_msg, assistant_msg])
db.commit()

# 5. Query the structure
print(f"Project: {project.name}")
print(f"  Documents: {len(project.documents)}")
print(f"  Chats: {len(project.chats)}")
print(f"  Messages in first chat: {len(project.chats[0].messages)}")

db.close()
```

### Complex Queries

```python
from sqlalchemy import func, and_, or_

# Get projects with document count
projects = db.query(
    Project,
    func.count(Document.id).label("doc_count")
).outerjoin(Document).group_by(Project.id).all()

for project, count in projects:
    print(f"{project.name}: {count} documents")

# Get recent active chats
recent_chats = db.query(Chat).join(Message).filter(
    Message.created_at >= datetime.now() - timedelta(days=7)
).distinct().all()

# Get documents that failed processing
failed_docs = db.query(Document).filter(
    Document.status == "failed"
).all()

# Get chats with message count
chats = db.query(
    Chat,
    func.count(Message.id).label("msg_count")
).outerjoin(Message).group_by(Chat.id).all()

# Full-text search in messages
search_term = "machine learning"
results = db.query(Message).filter(
    Message.content.like(f"%{search_term}%")
).all()
```

---

## Best Practices

### 1. Session Management

Always use context managers or try-finally blocks:

```python
from backend.core.database import SessionLocal

db = SessionLocal()
try:
    # Do database operations
    project = Project(name="Test")
    db.add(project)
    db.commit()
except Exception:
    db.rollback()
    raise
finally:
    db.close()
```

### 2. Eager Loading

Use eager loading to avoid N+1 queries:

```python
from sqlalchemy.orm import joinedload

# Bad: N+1 queries
projects = db.query(Project).all()
for project in projects:
    print(project.documents)  # Separate query for each project

# Good: Single query with join
projects = db.query(Project).options(
    joinedload(Project.documents)
).all()

for project in projects:
    print(project.documents)  # Already loaded
```

### 3. Validation

Validate data before committing:

```python
from pydantic import BaseModel, validator

class ProjectCreate(BaseModel):
    name: str
    description: str | None

    @validator("name")
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        return v

# Use Pydantic model to validate
data = ProjectCreate(name="Test", description="")
project = Project(**data.dict())
db.add(project)
db.commit()
```

### 4. Soft Deletes

Consider using soft deletes for important data:

```python
from sqlalchemy import Boolean

class Project(Base):
    # ... other fields
    is_deleted: bool = False
    deleted_at: datetime | None = None

# Soft delete
project.is_deleted = True
project.deleted_at = datetime.utcnow()
db.commit()

# Query only active projects
active_projects = db.query(Project).filter(
    Project.is_deleted == False
).all()
```

### 5. Indexes

Add indexes for frequently queried fields:

```python
from sqlalchemy import Index

class Document(Base):
    # ... fields

    __table_args__ = (
        Index('ix_doc_project_status', 'project_id', 'status'),
        Index('ix_doc_created', 'created_at'),
    )
```

### 6. Transactions

Use transactions for multi-step operations:

```python
from sqlalchemy import event

# Auto-update project.updated_at when documents change
@event.listens_for(Document, 'after_insert')
@event.listens_for(Document, 'after_update')
@event.listens_for(Document, 'after_delete')
def update_project_timestamp(mapper, connection, target):
    connection.execute(
        Project.__table__.update()
        .where(Project.id == target.project_id)
        .values(updated_at=datetime.utcnow())
    )
```

---

## Migration Guide

When modifying models, always create migrations:

```bash
# Create migration
alembic revision --autogenerate -m "Add metadata field to Document"

# Review generated migration
cat alembic/versions/xxx_add_metadata.py

# Apply migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

---

## Additional Resources

- [SQLAlchemy ORM Documentation](https://docs.sqlalchemy.org/en/20/orm/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
