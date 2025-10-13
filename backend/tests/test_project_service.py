"""
Test cases for project service.

This test module verifies:
- Project CRUD operations
- Project folder management
- Project statistics
- Project isolation
"""

import pytest
import pytest_asyncio
import json
import sys
import os
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from models.base import Base
from services.project_service import project_service, ProjectServiceError


# Test database setup
@pytest_asyncio.fixture
async def db_engine():
    """Create test database engine."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    """Create an async test database session."""
    async_session = async_sessionmaker(
        db_engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()


# Test project CRUD operations
@pytest.mark.asyncio
async def test_create_project(db_session):
    """Test creating a new project."""
    project = await project_service.create_project(
        db=db_session,
        name="Test Project",
        description="A test project",
        settings_dict={"model": "llama3.2"}
    )

    assert project.id is not None
    assert project.name == "Test Project"
    assert project.description == "A test project"
    assert project.document_count == 0
    assert project.total_chunks == 0
    assert project.chroma_collection_name != ""

    # Check settings
    settings_dict = json.loads(project.settings)
    assert settings_dict["model"] == "llama3.2"


@pytest.mark.asyncio
async def test_create_duplicate_project(db_session):
    """Test that creating a project with duplicate name fails."""
    await project_service.create_project(
        db=db_session,
        name="Duplicate Project"
    )

    with pytest.raises(ProjectServiceError, match="already exists"):
        await project_service.create_project(
            db=db_session,
            name="Duplicate Project"
        )


@pytest.mark.asyncio
async def test_get_project(db_session):
    """Test retrieving a project by ID."""
    created_project = await project_service.create_project(
        db=db_session,
        name="Retrievable Project"
    )

    retrieved_project = await project_service.get_project(
        db=db_session,
        project_id=created_project.id
    )

    assert retrieved_project is not None
    assert retrieved_project.id == created_project.id
    assert retrieved_project.name == "Retrievable Project"


@pytest.mark.asyncio
async def test_get_nonexistent_project(db_session):
    """Test retrieving a non-existent project returns None."""
    project = await project_service.get_project(
        db=db_session,
        project_id=9999
    )

    assert project is None


@pytest.mark.asyncio
async def test_list_projects(db_session):
    """Test listing all projects."""
    # Create multiple projects
    await project_service.create_project(db=db_session, name="Project 1")
    await project_service.create_project(db=db_session, name="Project 2")
    await project_service.create_project(db=db_session, name="Project 3")

    projects = await project_service.list_projects(db=db_session)

    assert len(projects) == 3
    assert all(p.name in ["Project 1", "Project 2", "Project 3"] for p in projects)


@pytest.mark.asyncio
async def test_update_project(db_session):
    """Test updating a project."""
    project = await project_service.create_project(
        db=db_session,
        name="Original Name"
    )

    updated_project = await project_service.update_project(
        db=db_session,
        project_id=project.id,
        name="Updated Name",
        description="Updated description"
    )

    assert updated_project.name == "Updated Name"
    assert updated_project.description == "Updated description"


@pytest.mark.asyncio
async def test_update_project_with_folder_path(db_session):
    """Test updating project with folder path."""
    project = await project_service.create_project(
        db=db_session,
        name="Project with Folder"
    )

    test_folder = "/test/folder/path"
    updated_project = await project_service.update_project(
        db=db_session,
        project_id=project.id,
        folder_path=test_folder
    )

    settings_dict = json.loads(updated_project.settings)
    assert settings_dict["folder_path"] == test_folder


@pytest.mark.asyncio
async def test_soft_delete_project(db_session):
    """Test soft deleting a project."""
    project = await project_service.create_project(
        db=db_session,
        name="Project to Delete"
    )

    success = await project_service.delete_project(
        db=db_session,
        project_id=project.id,
        hard_delete=False
    )

    assert success is True

    # Project should not appear in normal listings
    projects = await project_service.list_projects(
        db=db_session,
        include_deleted=False
    )
    assert not any(p.id == project.id for p in projects)

    # But should appear when including deleted
    projects_with_deleted = await project_service.list_projects(
        db=db_session,
        include_deleted=True
    )
    assert any(p.id == project.id for p in projects_with_deleted)


@pytest.mark.asyncio
async def test_get_project_statistics(db_session):
    """Test getting project statistics."""
    project = await project_service.create_project(
        db=db_session,
        name="Stats Project"
    )

    stats = await project_service.get_project_statistics(
        db=db_session,
        project_id=project.id
    )

    assert stats["project_id"] == project.id
    assert stats["project_name"] == "Stats Project"
    assert stats["document_count"] == 0
    assert stats["total_chunks"] == 0
    assert stats["chat_count"] == 0
    assert stats["message_count"] == 0


@pytest.mark.asyncio
async def test_export_project(db_session, tmp_path):
    """Test exporting a project."""
    project = await project_service.create_project(
        db=db_session,
        name="Export Project",
        description="Project for export testing"
    )

    export_file = tmp_path / "export.json"

    result = await project_service.export_project(
        db=db_session,
        project_id=project.id,
        export_path=str(export_file)
    )

    assert result["project_name"] == "Export Project"
    assert Path(result["export_path"]).exists()

    # Verify export file contents
    with open(export_file, 'r') as f:
        export_data = json.load(f)

    assert export_data["version"] == "1.0"
    assert export_data["project"]["name"] == "Export Project"
    assert export_data["project"]["description"] == "Project for export testing"


@pytest.mark.asyncio
async def test_import_project(db_session, tmp_path):
    """Test importing a project."""
    # Create an export file
    export_data = {
        "version": "1.0",
        "export_date": "2024-01-01T00:00:00",
        "project": {
            "name": "Imported Project",
            "description": "Project from import",
            "settings": {"model": "llama3.2"},
            "created_at": "2024-01-01T00:00:00"
        }
    }

    import_file = tmp_path / "import.json"
    with open(import_file, 'w') as f:
        json.dump(export_data, f)

    # Import the project
    project = await project_service.import_project(
        db=db_session,
        import_path=str(import_file)
    )

    assert project.name == "Imported Project"
    assert project.description == "Project from import"

    settings_dict = json.loads(project.settings)
    assert settings_dict["model"] == "llama3.2"


@pytest.mark.asyncio
async def test_switch_project_context(db_session):
    """Test switching between project contexts."""
    project1 = await project_service.create_project(db=db_session, name="Project 1")
    project2 = await project_service.create_project(db=db_session, name="Project 2")

    result = await project_service.switch_project_context(
        db=db_session,
        from_project_id=project1.id,
        to_project_id=project2.id
    )

    assert result["previous_project"]["id"] == project1.id
    assert result["previous_project"]["name"] == "Project 1"
    assert result["current_project"]["id"] == project2.id
    assert result["current_project"]["name"] == "Project 2"


@pytest.mark.asyncio
async def test_get_project_folder(db_session):
    """Test getting project folder path."""
    folder_path = "/test/project/folder"

    project = await project_service.create_project(
        db=db_session,
        name="Folder Project",
        folder_path=folder_path
    )

    retrieved_folder = await project_service.get_project_folder(
        db=db_session,
        project_id=project.id
    )

    assert retrieved_folder == folder_path


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
