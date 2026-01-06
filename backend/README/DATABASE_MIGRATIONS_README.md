# Database and Migrations Documentation

This document provides comprehensive documentation for database setup, schema management, and migrations using Alembic in the DAA Chatbot backend.

## Table of Contents

- [Overview](#overview)
- [Database Architecture](#database-architecture)
- [Alembic Setup](#alembic-setup)
- [Migration Workflow](#migration-workflow)
- [Common Migration Operations](#common-migration-operations)
- [Database Management](#database-management)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

The DAA Chatbot uses **SQLite** as its database for local data storage and **Alembic** for managing database schema migrations. This setup provides version control for database changes and ensures consistency across development and deployment environments.

**Technology Stack:**
- **Database**: SQLite 3.x
- **ORM**: SQLAlchemy 2.0
- **Migrations**: Alembic 1.16+
- **Storage Location**: `backend/storage/sqlite/app.db`

## Database Architecture

### Storage Structure

```
backend/storage/
├── sqlite/
│   ├── app.db              # Main SQLite database
│   └── app.db-journal      # Transaction journal (auto-created)
├── chroma/                 # ChromaDB vector storage
│   └── project_*/          # Per-project collections
└── documents/              # Uploaded files
    └── project_*/          # Per-project document storage
```

### Database Schema

The database consists of the following main tables:

```
projects (Project workspace isolation)
    ├── id (PK)
    ├── name
    ├── description
    ├── created_at
    └── updated_at

documents (Uploaded files and metadata)
    ├── id (PK)
    ├── project_id (FK → projects.id)
    ├── filename
    ├── file_path
    ├── file_type
    ├── file_size
    ├── status
    ├── error_message
    ├── metadata (JSON)
    ├── created_at
    └── processed_at

chats (Conversation threads)
    ├── id (PK)
    ├── project_id (FK → projects.id)
    ├── title
    ├── created_at
    └── updated_at

messages (Individual chat messages)
    ├── id (PK)
    ├── chat_id (FK → chats.id)
    ├── role
    ├── content
    ├── metadata (JSON)
    └── created_at

settings (Application configuration)
    ├── id (PK)
    ├── key (UNIQUE)
    ├── value
    ├── category
    ├── description
    └── updated_at
```

### Foreign Key Constraints

```sql
documents.project_id → projects.id (CASCADE DELETE)
chats.project_id → projects.id (CASCADE DELETE)
messages.chat_id → chats.id (CASCADE DELETE)
```

When a project is deleted, all associated documents, chats, and messages are automatically deleted.

---

## Alembic Setup

### Directory Structure

```
backend/
├── alembic/
│   ├── versions/           # Migration version files
│   │   ├── 001_initial.py
│   │   ├── 002_add_metadata.py
│   │   └── ...
│   ├── env.py             # Alembic environment configuration
│   ├── script.py.mako     # Migration template
│   └── README
├── alembic.ini            # Alembic configuration file
└── models/                # SQLAlchemy models
```

### Configuration File

**File:** `alembic.ini`

Key settings:

```ini
[alembic]
# Migration script location
script_location = alembic

# Database URL (can be overridden by env variable)
sqlalchemy.url = sqlite:///./storage/sqlite/app.db

# Migration file naming template
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(slug)s

# Timezone for timestamps
timezone = UTC
```

### Environment Configuration

**File:** `alembic/env.py`

This file configures how Alembic connects to the database and discovers models:

```python
from backend.core.config import get_settings
from backend.core.database import Base
from backend.models import *  # Import all models

config = context.config
settings = get_settings()

# Override sqlalchemy.url from environment
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Set target metadata from Base
target_metadata = Base.metadata
```

---

## Migration Workflow

### 1. Initial Setup

Run once when setting up the project:

```bash
cd backend

# Create storage directories
mkdir -p storage/sqlite storage/chroma storage/documents

# Run initial migration
alembic upgrade head
```

This creates all tables defined in the models.

### 2. Creating a New Migration

When you modify a model (add/remove/change fields):

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add metadata field to Document"
```

**What happens:**
1. Alembic compares current database schema with model definitions
2. Generates a migration file in `alembic/versions/`
3. Creates `upgrade()` and `downgrade()` functions

**Example generated migration:**

```python
"""Add metadata field to Document

Revision ID: abc123def456
Revises: prev_revision_id
Create Date: 2025-01-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123def456'
down_revision = 'prev_revision_id'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Add metadata column
    op.add_column('documents',
        sa.Column('metadata', sa.JSON(), nullable=True)
    )

def downgrade() -> None:
    # Remove metadata column
    op.drop_column('documents', 'metadata')
```

### 3. Review and Edit Migration

**Always review generated migrations before applying:**

```bash
# View the generated migration file
cat alembic/versions/abc123_add_metadata.py
```

Edit if needed to:
- Add data migrations
- Set default values
- Handle edge cases
- Add custom SQL

### 4. Apply Migration

```bash
# Apply all pending migrations
alembic upgrade head

# Or apply specific version
alembic upgrade abc123def456
```

**Output:**
```
INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade prev -> abc123, Add metadata field to Document
```

### 5. Rollback Migration (if needed)

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade abc123def456

# Rollback all migrations
alembic downgrade base
```

---

## Common Migration Operations

### Adding a Column

```python
def upgrade() -> None:
    op.add_column('documents',
        sa.Column('new_field', sa.String(255), nullable=True)
    )

def downgrade() -> None:
    op.drop_column('documents', 'new_field')
```

### Modifying a Column

```python
def upgrade() -> None:
    # SQLite doesn't support ALTER COLUMN directly
    # Need to recreate table
    op.alter_column('documents', 'filename',
        type_=sa.String(500),  # Increase size
        existing_type=sa.String(255)
    )

def downgrade() -> None:
    op.alter_column('documents', 'filename',
        type_=sa.String(255),
        existing_type=sa.String(500)
    )
```

**Note:** SQLite has limited ALTER TABLE support. Complex changes may require table recreation.

### Adding an Index

```python
def upgrade() -> None:
    op.create_index(
        'ix_documents_status',
        'documents',
        ['status']
    )

def downgrade() -> None:
    op.drop_index('ix_documents_status', table_name='documents')
```

### Adding a Foreign Key

```python
def upgrade() -> None:
    op.create_foreign_key(
        'fk_documents_project_id',
        'documents', 'projects',
        ['project_id'], ['id'],
        ondelete='CASCADE'
    )

def downgrade() -> None:
    op.drop_constraint('fk_documents_project_id', 'documents', type_='foreignkey')
```

### Data Migration

```python
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column

def upgrade() -> None:
    # Add column
    op.add_column('documents',
        sa.Column('status', sa.String(50), nullable=True)
    )

    # Migrate data
    documents = table('documents',
        column('id', sa.Integer),
        column('status', sa.String)
    )

    op.execute(
        documents.update().values(status='completed')
    )

    # Make column non-nullable after data migration
    op.alter_column('documents', 'status',
        nullable=False,
        server_default='processing'
    )

def downgrade() -> None:
    op.drop_column('documents', 'status')
```

### Creating a New Table

```python
def upgrade() -> None:
    op.create_table(
        'new_table',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('ix_new_table_name', 'new_table', ['name'])

def downgrade() -> None:
    op.drop_index('ix_new_table_name', table_name='new_table')
    op.drop_table('new_table')
```

---

## Database Management

### Checking Migration Status

```bash
# Show current database version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic show head
```

**Example output:**
```
abc123def456 (head)
  └─ Add metadata field to Document
def456ghi789
  └─ Create initial tables
```

### Viewing SQL Without Applying

```bash
# Show SQL that would be executed
alembic upgrade head --sql

# Output to file
alembic upgrade head --sql > migration.sql
```

### Stamping Database Version

If you've manually created tables or need to mark the database as up-to-date:

```bash
# Mark database as being at head revision
alembic stamp head

# Mark as specific revision
alembic stamp abc123def456
```

### Database Backup

```bash
# Backup SQLite database
cp storage/sqlite/app.db storage/sqlite/app.db.backup

# Backup with timestamp
cp storage/sqlite/app.db "storage/sqlite/app.db.$(date +%Y%m%d_%H%M%S).backup"
```

### Database Reset

```bash
# WARNING: Destroys all data!

# Delete database
rm storage/sqlite/app.db

# Recreate from migrations
alembic upgrade head
```

### Inspecting Database

```bash
# Open SQLite shell
sqlite3 storage/sqlite/app.db

# List all tables
.tables

# Show table schema
.schema documents

# Query data
SELECT * FROM projects LIMIT 5;

# Exit
.quit
```

---

## Troubleshooting

### Problem: Migration fails with "table already exists"

**Solution:**
```bash
# Drop the table or stamp the database
alembic stamp head
```

### Problem: "Can't locate revision identified by 'abc123'"

**Cause:** Migration file deleted or version mismatch

**Solution:**
```bash
# Check migration history
alembic history

# If migration is missing, recreate it or stamp to a valid revision
alembic stamp prev_revision_id
```

### Problem: SQLite doesn't support ALTER COLUMN

**Solution:** Use batch operations or table recreation

```python
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('documents') as batch_op:
        batch_op.alter_column('filename',
            type_=sa.String(500),
            existing_type=sa.String(255)
        )
```

### Problem: Foreign key constraint violation

**Solution:**
```bash
# Check for orphaned records
sqlite3 storage/sqlite/app.db "SELECT * FROM documents WHERE project_id NOT IN (SELECT id FROM projects);"

# Delete orphaned records before migration
```

### Problem: Migration hung or timeout

**Solution:**
```bash
# Check for database locks
fuser storage/sqlite/app.db

# Kill blocking processes if safe
# Re-run migration
```

### Problem: Alembic version table missing

**Solution:**
```bash
# Initialize Alembic version table
alembic stamp base

# Then upgrade
alembic upgrade head
```

---

## Best Practices

### 1. Always Review Auto-Generated Migrations

```bash
# Generate migration
alembic revision --autogenerate -m "description"

# Review before applying
cat alembic/versions/*.py

# Edit if needed
vim alembic/versions/latest_migration.py

# Then apply
alembic upgrade head
```

### 2. Write Reversible Migrations

Always implement both `upgrade()` and `downgrade()`:

```python
def upgrade() -> None:
    # Forward migration
    op.add_column('table', sa.Column('new_col', sa.String()))

def downgrade() -> None:
    # Backward migration
    op.drop_column('table', 'new_col')
```

### 3. Test Migrations

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Test upgrade again
alembic upgrade head
```

### 4. Backup Before Migration

```bash
# Always backup before applying migrations in production
cp storage/sqlite/app.db storage/sqlite/app.db.pre_migration_backup

# Then migrate
alembic upgrade head
```

### 5. Use Descriptive Migration Messages

```bash
# Good
alembic revision --autogenerate -m "Add metadata JSON field to documents table"

# Bad
alembic revision --autogenerate -m "update"
```

### 6. One Logical Change Per Migration

```python
# Good - Single purpose
"""Add status field to documents"""

def upgrade():
    op.add_column('documents', sa.Column('status', sa.String(50)))

# Bad - Multiple unrelated changes
"""Add status and refactor messages"""

def upgrade():
    op.add_column('documents', sa.Column('status', sa.String(50)))
    op.alter_column('messages', 'content', type_=sa.Text())
    op.create_table('new_unrelated_table', ...)
```

### 7. Handle Data Carefully

```python
def upgrade():
    # 1. Add column as nullable
    op.add_column('documents', sa.Column('status', sa.String(50), nullable=True))

    # 2. Populate existing rows
    op.execute("UPDATE documents SET status = 'completed' WHERE processed_at IS NOT NULL")
    op.execute("UPDATE documents SET status = 'processing' WHERE processed_at IS NULL")

    # 3. Make column non-nullable
    op.alter_column('documents', 'status', nullable=False)
```

### 8. Version Control Migrations

```bash
# Always commit migration files to git
git add alembic/versions/*.py
git commit -m "Add migration for status field"
git push
```

### 9. Document Complex Migrations

```python
"""Add document processing status tracking

This migration adds a 'status' field to track document processing stages.
Existing documents are marked as 'completed' if they have a processed_at
timestamp, otherwise 'processing'.

Revision ID: abc123def456
Revises: prev_revision
Create Date: 2025-01-07 12:00:00
"""
```

### 10. Use Transactions

```python
from alembic import op

def upgrade():
    # Use transaction for atomic operations
    connection = op.get_bind()

    with connection.begin():
        op.add_column('documents', ...)
        op.execute("UPDATE documents SET ...")
        op.alter_column('documents', ...)
```

---

## Initialization Scripts

### Initial Database Setup

**File:** `backend/scripts/init_db.py`

```python
from backend.core.database import engine, Base
from backend.models import *  # Import all models
from alembic import command
from alembic.config import Config

def init_database():
    """Initialize database with migrations"""
    # Run Alembic migrations
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")

    print("Database initialized successfully")

if __name__ == "__main__":
    init_database()
```

**Usage:**
```bash
python scripts/init_db.py
```

### Database Verification Script

**File:** `backend/scripts/check_setup.py`

```python
from backend.core.database import SessionLocal, engine
from backend.models.project import Project
from sqlalchemy import inspect

def check_database():
    """Verify database setup"""
    inspector = inspect(engine)

    # Check tables exist
    required_tables = ['projects', 'documents', 'chats', 'messages', 'settings']

    existing_tables = inspector.get_table_names()

    for table in required_tables:
        if table in existing_tables:
            print(f"✓ Table '{table}' exists")
        else:
            print(f"✗ Table '{table}' missing - run migrations!")
            return False

    # Check database connectivity
    try:
        db = SessionLocal()
        db.query(Project).first()
        db.close()
        print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

    return True

if __name__ == "__main__":
    if check_database():
        print("\nDatabase setup is correct!")
    else:
        print("\nDatabase setup has issues - please run migrations")
```

---

## Additional Resources

- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/en/20/)
- [SQLite Documentation](https://www.sqlite.org/docs.html)
- [Database Migration Best Practices](https://docs.sqlalchemy.org/en/20/core/migration.html)

---

## Migration Checklist

Before applying migrations in production:

- [ ] Review auto-generated migration code
- [ ] Test upgrade and downgrade locally
- [ ] Backup database
- [ ] Verify no active connections
- [ ] Test application after migration
- [ ] Commit migration files to version control
- [ ] Document breaking changes
- [ ] Update API documentation if schema changes affect endpoints
