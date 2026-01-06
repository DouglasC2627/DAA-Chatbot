# Testing Documentation

This document provides comprehensive guidelines for testing the DAA Chatbot backend, including unit tests, integration tests, and best practices.

## Table of Contents

- [Overview](#overview)
- [Testing Stack](#testing-stack)
- [Test Structure](#test-structure)
- [Running Tests](#running-tests)
- [Test Types](#test-types)
  - [Unit Tests](#unit-tests)
  - [Integration Tests](#integration-tests)
  - [End-to-End Tests](#end-to-end-tests)
- [Testing Patterns](#testing-patterns)
- [Mocking and Fixtures](#mocking-and-fixtures)
- [Test Coverage](#test-coverage)
- [CI/CD Integration](#cicd-integration)
- [Best Practices](#best-practices)

## Overview

The DAA Chatbot backend uses **pytest** as the primary testing framework, with additional tools for async testing, mocking, and coverage reporting. Tests are organized by component and test type to ensure comprehensive coverage of functionality.

**Testing Goals:**
- Ensure code correctness and reliability
- Prevent regressions when adding features
- Document expected behavior
- Enable confident refactoring
- Maintain code quality standards

## Testing Stack

**Core Testing Tools:**
- **pytest** (8.4+): Main testing framework
- **pytest-asyncio** (1.2+): Async test support
- **pytest-cov** (7.0+): Coverage reporting
- **pytest-mock**: Mocking utilities
- **httpx**: Async HTTP client for API testing

**Additional Tools:**
- **faker**: Generate test data
- **factory-boy**: Model factories for testing
- **freezegun**: Time mocking

## Test Structure

```
backend/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures and configuration
│   │
│   ├── unit/                          # Unit tests
│   │   ├── test_chunking.py          # Text chunking tests
│   │   ├── test_embeddings.py        # Embedding generation tests
│   │   ├── test_document_processor.py # Document processing tests
│   │   └── test_vectorstore.py       # Vector store tests
│   │
│   ├── integration/                   # Integration tests
│   │   ├── test_rag_pipeline.py      # Full RAG pipeline tests
│   │   ├── test_chat_service.py      # Chat service tests
│   │   ├── test_document_upload.py   # Document upload flow tests
│   │   └── test_project_isolation.py  # Project isolation tests
│   │
│   ├── api/                           # API endpoint tests
│   │   ├── test_projects.py          # Project endpoints
│   │   ├── test_documents.py         # Document endpoints
│   │   ├── test_chat.py              # Chat endpoints
│   │   └── test_analytics.py         # Analytics endpoints
│   │
│   ├── fixtures/                      # Test data and files
│   │   ├── sample.pdf
│   │   ├── test.docx
│   │   ├── data.csv
│   │   └── mock_responses.json
│   │
│   └── utils/                         # Test utilities
│       ├── factories.py               # Model factories
│       ├── mocks.py                   # Mock objects
│       └── helpers.py                 # Test helper functions
│
└── pytest.ini                         # Pytest configuration
```

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_chunking.py

# Run specific test function
pytest tests/unit/test_chunking.py::test_chunk_text_basic

# Run tests matching pattern
pytest -k "chunk"

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

### With Coverage

```bash
# Run tests with coverage report
pytest --cov=backend

# Generate HTML coverage report
pytest --cov=backend --cov-report=html

# View HTML report
open htmlcov/index.html

# Show missing lines
pytest --cov=backend --cov-report=term-missing

# Generate coverage badge
pytest --cov=backend --cov-report=xml
```

### Test Selection

```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run only API tests
pytest tests/api/

# Skip slow tests
pytest -m "not slow"

# Run only marked tests
pytest -m "integration"
```

### Watch Mode

```bash
# Install pytest-watch
pip install pytest-watch

# Run tests on file changes
ptw
```

---

## Test Types

### Unit Tests

Unit tests verify individual functions and classes in isolation.

**Location:** `tests/unit/`

**Example: Testing Text Chunking**

**File:** `tests/unit/test_chunking.py`

```python
import pytest
from backend.core.chunking import TextChunker

class TestTextChunker:
    """Test TextChunker class"""

    def test_chunk_text_basic(self):
        """Test basic text chunking"""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)

        text = "This is a test. " * 20  # 300 chars
        chunks = chunker.chunk_text(text)

        # Assertions
        assert len(chunks) > 1
        assert all(len(chunk["text"]) <= 120 for chunk in chunks)  # Size + overlap
        assert all("chunk_index" in chunk for chunk in chunks)

    def test_chunk_with_metadata(self):
        """Test chunking with metadata preservation"""
        chunker = TextChunker(chunk_size=100, chunk_overlap=20)

        metadata = {"document_id": 1, "page": 5}
        chunks = chunker.chunk_text("Short text", metadata=metadata)

        assert chunks[0]["metadata"]["document_id"] == 1
        assert chunks[0]["metadata"]["page"] == 5
        assert chunks[0]["metadata"]["chunk_index"] == 0

    def test_empty_text(self):
        """Test handling of empty text"""
        chunker = TextChunker()

        chunks = chunker.chunk_text("")

        assert len(chunks) == 0

    @pytest.mark.parametrize("chunk_size,expected_min_chunks", [
        (50, 10),
        (100, 5),
        (200, 3),
    ])
    def test_chunk_sizes(self, chunk_size, expected_min_chunks):
        """Test different chunk sizes"""
        chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=10)

        text = "Word " * 200  # 1000 chars
        chunks = chunker.chunk_text(text)

        assert len(chunks) >= expected_min_chunks
```

**Example: Testing Document Processor**

**File:** `tests/unit/test_document_processor.py`

```python
import pytest
from backend.services.document_processor import process_document, DocumentProcessingError

class TestDocumentProcessor:
    """Test document processing functions"""

    def test_process_pdf(self):
        """Test PDF processing"""
        result = process_document("tests/fixtures/sample.pdf", "pdf")

        assert "text" in result
        assert len(result["text"]) > 0
        assert result["metadata"]["page_count"] > 0

    def test_process_docx(self):
        """Test DOCX processing"""
        result = process_document("tests/fixtures/test.docx", "docx")

        assert "text" in result
        assert result["metadata"]["paragraph_count"] >= 0

    def test_process_txt(self):
        """Test plain text processing"""
        result = process_document("tests/fixtures/sample.txt", "txt")

        assert "text" in result
        assert result["metadata"]["line_count"] > 0

    def test_unsupported_format(self):
        """Test error on unsupported format"""
        with pytest.raises(DocumentProcessingError):
            process_document("test.xyz", "xyz")

    def test_missing_file(self):
        """Test error on missing file"""
        with pytest.raises(FileNotFoundError):
            process_document("nonexistent.pdf", "pdf")
```

---

### Integration Tests

Integration tests verify that multiple components work together correctly.

**Location:** `tests/integration/`

**Example: Testing RAG Pipeline**

**File:** `tests/integration/test_rag_pipeline.py`

```python
import pytest
from backend.core.rag_pipeline import RAGPipeline
from backend.core.vectorstore import VectorStore
from backend.core.embeddings import EmbeddingGenerator
from backend.models.project import Project
from backend.core.database import SessionLocal

@pytest.mark.integration
@pytest.mark.asyncio
class TestRAGPipeline:
    """Integration tests for RAG pipeline"""

    @pytest.fixture
    async def setup_project(self, db):
        """Create test project with documents"""
        # Create project
        project = Project(name="Test Project")
        db.add(project)
        db.commit()
        db.refresh(project)

        # Add test documents to vector store
        vectorstore = VectorStore()
        embedder = EmbeddingGenerator()

        chunks = [
            {
                "id": f"test_chunk_{i}",
                "text": f"This is test chunk {i} about machine learning",
                "embedding": await embedder.embed_text(f"test chunk {i}"),
                "metadata": {"document_id": 1, "chunk_index": i}
            }
            for i in range(5)
        ]

        await vectorstore.add_documents(project.id, chunks)

        yield project

        # Cleanup
        await vectorstore.delete_project(project.id)
        db.delete(project)
        db.commit()

    async def test_generate_response(self, setup_project):
        """Test complete RAG response generation"""
        project = setup_project
        rag = RAGPipeline()

        response = await rag.generate_response(
            query="What is machine learning?",
            project_id=project.id
        )

        assert response is not None
        assert len(response) > 0
        assert isinstance(response, str)

    async def test_stream_response(self, setup_project):
        """Test streaming RAG response"""
        project = setup_project
        rag = RAGPipeline()

        chunks = []
        async for chunk in rag.stream_response(
            query="Explain ML",
            project_id=project.id
        ):
            chunks.append(chunk)

        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert len(full_response) > 0

    async def test_retrieval_accuracy(self, setup_project):
        """Test retrieval returns relevant chunks"""
        project = setup_project
        vectorstore = VectorStore()

        # Query
        embedder = EmbeddingGenerator()
        query_embedding = await embedder.embed_text("machine learning")

        results = await vectorstore.query(
            project_id=project.id,
            query_embedding=query_embedding,
            k=3
        )

        assert len(results) <= 3
        assert all("machine learning" in r["text"].lower() for r in results)
```

**Example: Testing Chat Service**

**File:** `tests/integration/test_chat_service.py`

```python
import pytest
from backend.services.chat_service import create_chat, send_message
from backend.models.project import Project
from backend.models.chat import Chat

@pytest.mark.integration
class TestChatService:
    """Integration tests for chat service"""

    @pytest.fixture
    def project(self, db):
        """Create test project"""
        project = Project(name="Chat Test Project")
        db.add(project)
        db.commit()
        db.refresh(project)
        return project

    def test_create_and_send_message(self, db, project):
        """Test creating chat and sending message"""
        # Create chat
        chat = create_chat(
            project_id=project.id,
            title="Test Chat",
            db=db
        )

        assert chat.id is not None
        assert chat.title == "Test Chat"

        # Send message
        response = await send_message(
            chat_id=chat.id,
            message="Hello, how are you?",
            db=db
        )

        assert "user_message" in response
        assert "assistant_message" in response
        assert response["user_message"].content == "Hello, how are you?"
        assert len(response["assistant_message"].content) > 0

    def test_chat_history_preserved(self, db, project):
        """Test chat history is maintained"""
        chat = create_chat(project.id, "History Test", db)

        # Send multiple messages
        await send_message(chat.id, "First message", db)
        await send_message(chat.id, "Second message", db)
        await send_message(chat.id, "Third message", db)

        # Get history
        from backend.services.chat_service import get_chat_history
        history = get_chat_history(chat.id, limit=10, db=db)

        assert len(history) >= 6  # 3 user + 3 assistant
        assert history[0].content == "First message"
```

---

### End-to-End Tests

E2E tests verify complete user workflows through the API.

**Location:** `tests/api/`

**Example: Testing Project API**

**File:** `tests/api/test_projects.py`

```python
import pytest
from fastapi.testclient import TestClient
from backend.api.main import app

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

class TestProjectAPI:
    """Test project API endpoints"""

    def test_create_project(self, client):
        """Test POST /api/projects"""
        response = client.post(
            "/api/projects",
            json={"name": "Test Project", "description": "Test"}
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Project"
        assert "id" in data

    def test_get_projects(self, client):
        """Test GET /api/projects"""
        # Create test project
        client.post("/api/projects", json={"name": "Project 1"})

        # Get all projects
        response = client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_get_project_by_id(self, client):
        """Test GET /api/projects/{id}"""
        # Create project
        create_response = client.post(
            "/api/projects",
            json={"name": "Specific Project"}
        )
        project_id = create_response.json()["id"]

        # Get project
        response = client.get(f"/api/projects/{project_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["name"] == "Specific Project"

    def test_update_project(self, client):
        """Test PUT /api/projects/{id}"""
        # Create project
        create_response = client.post(
            "/api/projects",
            json={"name": "Original Name"}
        )
        project_id = create_response.json()["id"]

        # Update project
        response = client.put(
            f"/api/projects/{project_id}",
            json={"name": "Updated Name"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"

    def test_delete_project(self, client):
        """Test DELETE /api/projects/{id}"""
        # Create project
        create_response = client.post(
            "/api/projects",
            json={"name": "To Delete"}
        )
        project_id = create_response.json()["id"]

        # Delete project
        response = client.delete(f"/api/projects/{project_id}")

        assert response.status_code == 200

        # Verify deleted
        get_response = client.get(f"/api/projects/{project_id}")
        assert get_response.status_code == 404

    def test_create_project_validation(self, client):
        """Test validation on project creation"""
        # Empty name
        response = client.post(
            "/api/projects",
            json={"name": ""}
        )

        assert response.status_code == 400
```

---

## Testing Patterns

### Arrange-Act-Assert (AAA)

```python
def test_chunk_text():
    # Arrange: Set up test data
    chunker = TextChunker(chunk_size=100, chunk_overlap=20)
    text = "Test text here..."

    # Act: Execute the function
    result = chunker.chunk_text(text)

    # Assert: Verify expectations
    assert len(result) > 0
    assert result[0]["chunk_index"] == 0
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input_text,expected_chunks", [
    ("Short text", 1),
    ("Medium " * 50, 3),
    ("Very long " * 200, 10),
])
def test_chunk_count(input_text, expected_chunks):
    chunker = TextChunker(chunk_size=100)
    chunks = chunker.chunk_text(input_text)
    assert len(chunks) >= expected_chunks
```

### Test Classes

```python
class TestDocumentProcessor:
    """Group related tests together"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Run before each test"""
        self.processor = DocumentProcessor()

    def test_pdf_processing(self):
        result = self.processor.process("test.pdf")
        assert result is not None

    def test_docx_processing(self):
        result = self.processor.process("test.docx")
        assert result is not None
```

---

## Mocking and Fixtures

### Fixtures

**File:** `tests/conftest.py`

```python
import pytest
from backend.core.database import SessionLocal, Base, engine
from backend.models import *

@pytest.fixture(scope="function")
def db():
    """Create test database session"""
    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop all tables
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def sample_project(db):
    """Create a sample project"""
    from backend.models.project import Project

    project = Project(name="Test Project", description="For testing")
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@pytest.fixture
def mock_ollama(monkeypatch):
    """Mock Ollama API calls"""
    async def mock_generate(prompt, **kwargs):
        return "Mocked response"

    from backend.core import llm
    monkeypatch.setattr(llm.OllamaClient, "generate", mock_generate)
```

### Mocking External Services

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_llm_generation_with_mock():
    """Test LLM generation with mocked Ollama"""
    with patch('backend.core.llm.OllamaClient.generate') as mock_generate:
        mock_generate.return_value = "Mocked AI response"

        from backend.core.llm import OllamaClient
        llm = OllamaClient()
        response = await llm.generate("Test prompt")

        assert response == "Mocked AI response"
        mock_generate.assert_called_once()
```

### Factory Pattern

**File:** `tests/utils/factories.py`

```python
import factory
from backend.models.project import Project
from backend.models.document import Document
from backend.core.database import SessionLocal

class ProjectFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Project
        sqlalchemy_session = SessionLocal()

    name = factory.Faker('company')
    description = factory.Faker('text')

class DocumentFactory(factory.alchemy.SQLAlchemyModelFactory):
    class Meta:
        model = Document
        sqlalchemy_session = SessionLocal()

    project_id = factory.SubFactory(ProjectFactory)
    filename = factory.Faker('file_name', extension='pdf')
    file_type = 'pdf'
    file_size = factory.Faker('random_int', min=1000, max=10000000)
    status = 'completed'
```

**Usage:**
```python
from tests.utils.factories import ProjectFactory, DocumentFactory

def test_with_factories():
    project = ProjectFactory()
    document = DocumentFactory(project_id=project.id)

    assert document.project_id == project.id
```

---

## Test Coverage

### Viewing Coverage

```bash
# Generate coverage report
pytest --cov=backend --cov-report=html

# Open in browser
open htmlcov/index.html
```

### Coverage Goals

- **Overall Coverage**: 80%+
- **Core Modules**: 90%+
- **CRUD Operations**: 85%+
- **API Routes**: 80%+

### Coverage Configuration

**File:** `.coveragerc`

```ini
[run]
source = backend
omit =
    */tests/*
    */venv/*
    */migrations/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    if TYPE_CHECKING:
```

---

## CI/CD Integration

### GitHub Actions

**File:** `.github/workflows/tests.yml`

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2

    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt

    - name: Run tests with coverage
      run: |
        cd backend
        pytest --cov=backend --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        file: backend/coverage.xml
```

---

## Best Practices

### 1. Write Tests First (TDD)

```python
# Write test first
def test_new_feature():
    result = new_feature("input")
    assert result == "expected_output"

# Then implement feature
def new_feature(input):
    return "expected_output"
```

### 2. One Assert Per Test (when possible)

```python
# Good
def test_chunk_count():
    chunks = chunk_text("text")
    assert len(chunks) == 3

def test_chunk_content():
    chunks = chunk_text("text")
    assert all(len(c["text"]) > 0 for c in chunks)

# Acceptable for related assertions
def test_chunk_structure():
    chunks = chunk_text("text")
    assert len(chunks) > 0
    assert "text" in chunks[0]
    assert "chunk_index" in chunks[0]
```

### 3. Use Descriptive Test Names

```python
# Good
def test_empty_text_returns_empty_chunks():
    ...

def test_chunk_size_respects_max_length():
    ...

# Bad
def test_1():
    ...

def test_chunks():
    ...
```

### 4. Test Edge Cases

```python
def test_empty_input():
    assert chunk_text("") == []

def test_very_long_input():
    text = "word " * 10000
    chunks = chunk_text(text)
    assert all(len(c["text"]) <= MAX_SIZE for c in chunks)

def test_unicode_characters():
    text = "Hello 世界 🌍"
    chunks = chunk_text(text)
    assert chunks[0]["text"] == text
```

### 5. Clean Up After Tests

```python
@pytest.fixture
def temp_file():
    path = "temp_test_file.txt"
    yield path
    # Cleanup
    if os.path.exists(path):
        os.remove(path)
```

### 6. Use Markers

```python
@pytest.mark.slow
def test_large_document_processing():
    ...

@pytest.mark.integration
def test_full_rag_pipeline():
    ...

@pytest.mark.skip(reason="Not implemented yet")
def test_future_feature():
    ...
```

**Run marked tests:**
```bash
pytest -m integration
pytest -m "not slow"
```

---

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [FastAPI Testing Guide](https://fastapi.tiangolo.com/tutorial/testing/)
