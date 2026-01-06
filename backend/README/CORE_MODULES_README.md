# Core Modules Documentation

This document provides detailed documentation for the core modules that power the DAA Chatbot's RAG functionality.

## Table of Contents

- [Overview](#overview)
- [Module Architecture](#module-architecture)
- [Core Modules](#core-modules)
  - [RAG Pipeline](#rag-pipeline)
  - [LLM Client](#llm-client)
  - [Vector Store](#vector-store)
  - [Embeddings](#embeddings)
  - [Chunking](#chunking)
  - [Configuration](#configuration)
  - [Database](#database)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)

## Overview

The `core/` directory contains the fundamental building blocks of the RAG system. These modules handle everything from LLM interaction and embedding generation to vector storage and retrieval.

```
backend/core/
├── config.py           # Configuration and environment variables
├── database.py         # Database session management
├── llm.py             # Ollama client wrapper
├── vectorstore.py     # ChromaDB operations
├── rag_pipeline.py    # RAG orchestration
├── embeddings.py      # Embedding generation
└── chunking.py        # Text splitting strategies
```

## Module Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    API Routes                           │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                  RAG Pipeline                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  Retrieval   │→ │  Augment     │→ │  Generate    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└──────┬────────────────────┬────────────────────┬────────┘
       │                    │                    │
       ▼                    ▼                    ▼
┌──────────────┐  ┌──────────────┐    ┌──────────────┐
│ VectorStore  │  │  Embeddings  │    │  LLM Client  │
│  (ChromaDB)  │  │   (Ollama)   │    │   (Ollama)   │
└──────────────┘  └──────────────┘    └──────────────┘
       ▲                    ▲
       │                    │
       └────────┬───────────┘
                │
         ┌──────────────┐
         │   Chunking   │
         └──────────────┘
```

## Core Modules

### RAG Pipeline

**File:** `core/rag_pipeline.py`

The RAG pipeline orchestrates the entire retrieval-augmented generation process, combining document retrieval with LLM generation.

#### Key Classes

##### `RAGPipeline`

The main orchestrator for RAG operations.

**Initialization:**
```python
from backend.core.rag_pipeline import RAGPipeline
from backend.core.config import get_settings

settings = get_settings()
rag = RAGPipeline()
```

**Key Methods:**

**`generate_response(query: str, project_id: int, chat_history: List[Message] = None) -> str`**

Generates a response using RAG.

```python
response = await rag.generate_response(
    query="What is machine learning?",
    project_id=1,
    chat_history=previous_messages
)
```

**Process:**
1. Embed the user query
2. Retrieve top-k relevant chunks from vector store
3. Construct prompt with context and chat history
4. Generate response using LLM
5. Return response with source attribution

**`stream_response(query: str, project_id: int, chat_history: List[Message] = None) -> AsyncGenerator`**

Streams response tokens in real-time.

```python
async for chunk in rag.stream_response(
    query="Explain neural networks",
    project_id=1
):
    print(chunk, end="", flush=True)
```

**Configuration:**
- `retrieval_k`: Number of chunks to retrieve (default: 5)
- `chunk_overlap`: Include overlap in context (default: True)
- `max_history_turns`: Maximum chat history to include (default: 5)

---

### LLM Client

**File:** `core/llm.py`

Wrapper around Ollama for LLM inference operations.

#### Key Classes

##### `OllamaClient`

Manages all interactions with the Ollama service.

**Initialization:**
```python
from backend.core.llm import OllamaClient
from backend.core.config import get_settings

settings = get_settings()
llm = OllamaClient(
    host=settings.OLLAMA_HOST,
    model=settings.OLLAMA_MODEL
)
```

**Key Methods:**

**`generate(prompt: str, system: str = None) -> str`**

Generate a completion for a prompt.

```python
response = await llm.generate(
    prompt="What is the capital of France?",
    system="You are a helpful geography tutor."
)
# "The capital of France is Paris."
```

**`stream_generate(prompt: str, system: str = None) -> AsyncGenerator[str]`**

Stream tokens as they're generated.

```python
async for token in llm.stream_generate(prompt="Write a poem"):
    print(token, end="", flush=True)
```

**`list_models() -> List[Dict]`**

List all available models in Ollama.

```python
models = await llm.list_models()
# [{"name": "llama3.2", "size": "4.7GB", ...}, ...]
```

**`is_available() -> bool`**

Check if Ollama service is reachable.

```python
if await llm.is_available():
    print("Ollama is ready!")
```

**Configuration:**
- `temperature`: Randomness in generation (0.0-1.0, default: 0.7)
- `top_p`: Nucleus sampling threshold (default: 0.9)
- `max_tokens`: Maximum tokens to generate (default: 2048)

---

### Vector Store

**File:** `core/vectorstore.py`

Manages ChromaDB operations for storing and retrieving document embeddings.

#### Key Classes

##### `VectorStore`

Interface to ChromaDB for vector operations.

**Initialization:**
```python
from backend.core.vectorstore import VectorStore
from backend.core.config import get_settings

settings = get_settings()
vectorstore = VectorStore(
    persist_directory=settings.CHROMA_PERSIST_DIR
)
```

**Key Methods:**

**`add_documents(project_id: int, chunks: List[Dict]) -> None`**

Add document chunks to the vector store.

```python
await vectorstore.add_documents(
    project_id=1,
    chunks=[
        {
            "id": "doc1_chunk0",
            "text": "Machine learning is...",
            "embedding": [0.1, 0.2, ...],
            "metadata": {
                "document_id": 1,
                "document_name": "ml_intro.pdf",
                "chunk_index": 0,
                "page": 1
            }
        }
    ]
)
```

**`query(project_id: int, query_embedding: List[float], k: int = 5) -> List[Dict]`**

Retrieve top-k similar chunks.

```python
results = await vectorstore.query(
    project_id=1,
    query_embedding=query_vector,
    k=5
)
# [
#   {
#     "text": "Machine learning is...",
#     "metadata": {...},
#     "similarity": 0.92
#   }, ...
# ]
```

**`delete_document(project_id: int, document_id: int) -> None`**

Delete all chunks for a document.

```python
await vectorstore.delete_document(
    project_id=1,
    document_id=5
)
```

**`delete_project(project_id: int) -> None`**

Delete entire project collection.

```python
await vectorstore.delete_project(project_id=1)
```

**`get_all_embeddings(project_id: int) -> List[Dict]`**

Retrieve all embeddings for a project (used for analytics).

```python
embeddings = await vectorstore.get_all_embeddings(project_id=1)
```

**Collection Naming:**
- Each project gets its own collection: `project_{project_id}`
- Collections are isolated - queries only search within the project

---

### Embeddings

**File:** `core/embeddings.py`

Handles text-to-vector conversion using Ollama's embedding models.

#### Key Classes

##### `EmbeddingGenerator`

Generates embeddings for text using Ollama.

**Initialization:**
```python
from backend.core.embeddings import EmbeddingGenerator
from backend.core.config import get_settings

settings = get_settings()
embedder = EmbeddingGenerator(
    host=settings.OLLAMA_HOST,
    model=settings.EMBEDDING_MODEL
)
```

**Key Methods:**

**`embed_text(text: str) -> List[float]`**

Generate embedding for a single text.

```python
embedding = await embedder.embed_text(
    "Machine learning is a subset of AI"
)
# [0.123, -0.456, 0.789, ...]  # 768-dimensional vector
```

**`embed_batch(texts: List[str]) -> List[List[float]]`**

Generate embeddings for multiple texts efficiently.

```python
embeddings = await embedder.embed_batch([
    "First chunk of text",
    "Second chunk of text",
    "Third chunk of text"
])
# [[...], [...], [...]]  # List of embedding vectors
```

**`get_dimension() -> int`**

Get the dimensionality of the embedding model.

```python
dim = await embedder.get_dimension()
# 768 for nomic-embed-text
```

**Supported Models:**
- `nomic-embed-text`: 768 dimensions, optimized for retrieval
- `mxbai-embed-large`: 1024 dimensions, high quality

**Best Practices:**
- Use batch embedding for better performance
- Cache embeddings when possible
- Same model must be used for both document and query embeddings

---

### Chunking

**File:** `core/chunking.py`

Splits documents into optimally-sized chunks for embedding and retrieval.

#### Key Classes

##### `TextChunker`

Handles text splitting with various strategies.

**Initialization:**
```python
from backend.core.chunking import TextChunker
from backend.core.config import get_settings

settings = get_settings()
chunker = TextChunker(
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP
)
```

**Key Methods:**

**`chunk_text(text: str, metadata: Dict = None) -> List[Dict]`**

Split text into chunks with metadata.

```python
chunks = chunker.chunk_text(
    text="Long document text here...",
    metadata={
        "document_id": 1,
        "document_name": "doc.pdf",
        "page": 1
    }
)
# [
#   {
#     "text": "First chunk...",
#     "metadata": {
#       "document_id": 1,
#       "chunk_index": 0,
#       "page": 1
#     }
#   }, ...
# ]
```

**`chunk_by_tokens(text: str, max_tokens: int = 512) -> List[str]`**

Split text by token count (more accurate for LLM context limits).

```python
chunks = chunker.chunk_by_tokens(
    text="Document text...",
    max_tokens=512
)
```

**Chunking Strategies:**

1. **Fixed Size**: Default strategy with configurable size and overlap
2. **Recursive**: Tries to split on natural boundaries (paragraphs, sentences)
3. **Token-based**: Splits based on token count for precise context management

**Configuration:**
- `chunk_size`: Target characters per chunk (default: 1000)
- `chunk_overlap`: Overlap between chunks (default: 200)
- `separators`: Text split boundaries (default: ["\n\n", "\n", ". ", " "])

**Why Overlap?**
Overlap ensures context isn't lost at chunk boundaries. For example, a sentence spanning two chunks will appear in both.

---

### Configuration

**File:** `core/config.py`

Centralized configuration management using Pydantic Settings.

#### Key Classes

##### `Settings`

Application settings loaded from environment variables.

**Initialization:**
```python
from backend.core.config import get_settings

settings = get_settings()
```

**Configuration Categories:**

**Ollama Settings:**
```python
settings.OLLAMA_HOST          # "http://localhost:11434"
settings.OLLAMA_MODEL         # "llama3.2"
settings.EMBEDDING_MODEL      # "nomic-embed-text"
settings.OLLAMA_AUTO_START    # True
settings.OLLAMA_STARTUP_TIMEOUT  # 30
```

**Database Settings:**
```python
settings.DATABASE_URL         # "sqlite:///./storage/sqlite/app.db"
settings.CHROMA_PERSIST_DIR   # "./storage/chroma"
```

**File Storage:**
```python
settings.UPLOAD_DIR           # "./storage/documents"
settings.MAX_FILE_SIZE        # 10485760 (10MB)
```

**RAG Configuration:**
```python
settings.CHUNK_SIZE           # 1000
settings.CHUNK_OVERLAP        # 200
settings.RETRIEVAL_K          # 5
```

**Environment Variables:**
Create a `.env` file in the backend directory:

```bash
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
EMBEDDING_MODEL=nomic-embed-text
DATABASE_URL=sqlite:///./storage/sqlite/app.db
CHROMA_PERSIST_DIR=./storage/chroma
UPLOAD_DIR=./storage/documents
MAX_FILE_SIZE=10485760
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
RETRIEVAL_K=5
```

---

### Database

**File:** `core/database.py`

Database session management and connection handling.

#### Key Functions

**`get_db() -> Generator[Session]`**

Dependency for getting database sessions.

```python
from backend.core.database import get_db
from fastapi import Depends

@app.get("/projects")
def list_projects(db: Session = Depends(get_db)):
    projects = db.query(Project).all()
    return projects
```

**`init_db() -> None`**

Initialize database (create all tables).

```python
from backend.core.database import init_db

init_db()
```

**Session Management:**
- Sessions are automatically created and closed
- Use context managers for explicit control
- Always commit or rollback transactions

```python
from backend.core.database import SessionLocal

# Explicit session management
db = SessionLocal()
try:
    # Do database operations
    db.commit()
except Exception:
    db.rollback()
    raise
finally:
    db.close()
```

---

## Usage Examples

### Complete RAG Flow

```python
from backend.core.rag_pipeline import RAGPipeline
from backend.core.embeddings import EmbeddingGenerator
from backend.core.vectorstore import VectorStore
from backend.core.chunking import TextChunker

# 1. Chunk and embed a document
chunker = TextChunker(chunk_size=1000, chunk_overlap=200)
chunks = chunker.chunk_text(
    text=document_text,
    metadata={"document_id": 1, "document_name": "doc.pdf"}
)

# 2. Generate embeddings
embedder = EmbeddingGenerator()
texts = [chunk["text"] for chunk in chunks]
embeddings = await embedder.embed_batch(texts)

# 3. Store in vector database
vectorstore = VectorStore()
for chunk, embedding in zip(chunks, embeddings):
    chunk["embedding"] = embedding

await vectorstore.add_documents(project_id=1, chunks=chunks)

# 4. Query using RAG
rag = RAGPipeline()
response = await rag.generate_response(
    query="What does this document say about machine learning?",
    project_id=1
)

print(response)
```

### Streaming Chat

```python
from backend.core.rag_pipeline import RAGPipeline
from backend.models.chat import Message

rag = RAGPipeline()

# Chat history context
history = [
    Message(role="user", content="What is AI?"),
    Message(role="assistant", content="AI stands for..."),
]

# Stream response
async for chunk in rag.stream_response(
    query="Tell me more about machine learning",
    project_id=1,
    chat_history=history
):
    print(chunk, end="", flush=True)
```

### Custom Embedding Pipeline

```python
from backend.core.embeddings import EmbeddingGenerator
from backend.core.vectorstore import VectorStore

embedder = EmbeddingGenerator(model="mxbai-embed-large")
vectorstore = VectorStore()

# Embed and store custom data
texts = ["First fact", "Second fact", "Third fact"]
embeddings = await embedder.embed_batch(texts)

chunks = [
    {
        "id": f"custom_{i}",
        "text": text,
        "embedding": emb,
        "metadata": {"source": "custom", "index": i}
    }
    for i, (text, emb) in enumerate(zip(texts, embeddings))
]

await vectorstore.add_documents(project_id=1, chunks=chunks)
```

---

## Best Practices

### 1. Configuration Management

- Always use `get_settings()` to access configuration
- Never hardcode API URLs or credentials
- Use `.env` file for local development
- Validate settings on startup

### 2. Error Handling

```python
from backend.core.llm import OllamaClient

llm = OllamaClient()

try:
    if not await llm.is_available():
        raise RuntimeError("Ollama service is not available")

    response = await llm.generate(prompt="Hello")
except Exception as e:
    logger.error(f"LLM error: {e}")
    # Fallback logic
```

### 3. Chunking Strategy

- **Short documents (< 5 pages)**: Use smaller chunks (500-800 chars)
- **Long documents**: Use larger chunks (1000-1500 chars)
- **Code/structured data**: Use token-based chunking
- **Always use overlap** (15-20% of chunk size)

### 4. Embedding Performance

- **Batch processing**: Always use `embed_batch()` for multiple texts
- **Caching**: Cache document embeddings, regenerate query embeddings
- **Model selection**: Use `nomic-embed-text` for speed, `mxbai-embed-large` for quality

### 5. Vector Store Operations

- Use project-specific collections for isolation
- Delete old embeddings when updating documents
- Regularly backup ChromaDB data
- Monitor vector store size

### 6. RAG Pipeline Optimization

- **Context window**: Don't exceed model's context limit
- **Retrieved chunks**: Start with k=5, tune based on quality
- **Prompt engineering**: Clear instructions in system prompt
- **History management**: Limit chat history to prevent context overflow

### 7. Resource Management

- Close database sessions properly
- Use connection pooling for production
- Monitor Ollama memory usage
- Implement request timeouts

---

## Performance Considerations

### Embedding Generation

- **Single text**: ~50-100ms
- **Batch (10 texts)**: ~200-300ms
- **Batch (100 texts)**: ~1-2 seconds

### Vector Search

- **Small project (< 100 chunks)**: < 10ms
- **Medium project (100-1000 chunks)**: 10-50ms
- **Large project (> 1000 chunks)**: 50-200ms

### LLM Generation

- **Streaming**: First token in 100-500ms, then 20-50 tokens/second
- **Complete**: 2-10 seconds depending on response length

### Optimization Tips

1. **Use streaming** for better perceived performance
2. **Batch operations** when processing multiple documents
3. **Cache embeddings** to avoid recomputation
4. **Index vector store** for faster similarity search
5. **Limit context size** to reduce generation latency

---

## Troubleshooting

### Ollama Connection Issues

```python
from backend.core.llm import OllamaClient

llm = OllamaClient()
if not await llm.is_available():
    # Check if Ollama is running
    # Try: ollama serve
    pass
```

### ChromaDB Persistence

Ensure persist directory exists and has write permissions:
```bash
mkdir -p ./storage/chroma
chmod 755 ./storage/chroma
```

### Embedding Dimension Mismatch

All embeddings in a collection must have the same dimension. If changing embedding models:
1. Delete old project collection
2. Re-embed all documents with new model

### Out of Memory (Ollama)

- Reduce batch size for embedding
- Use smaller model
- Increase system memory allocation for Ollama

---

## Additional Resources

- [Ollama Documentation](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
