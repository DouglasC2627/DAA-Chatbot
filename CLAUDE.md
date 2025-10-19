# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Task Completion Protocol

**IMPORTANT:** After completing any task assigned by the user, you MUST provide a comprehensive task summary that includes:

1. **Tasks Completed:** A clear, numbered list of all tasks that were accomplished
2. **Changes Made:** Specific files modified, created, or deleted with brief descriptions
3. **Reasoning & Decisions:** Explanation of the approach taken and why specific decisions were made
4. **Key Findings:** Any important discoveries, issues identified, or insights gained during the task
5. **Next Steps (if applicable):** Suggested follow-up actions or recommendations

**Format Example:**
```
## Task Summary

### Tasks Completed
1. Updated README.md files across the project
2. Fixed backend server commands to use socket_app
3. Created comprehensive frontend documentation

This summary helps maintain clarity, provides documentation of work done, and ensures transparent communication about the development process.

## Project Overview

DAA Chatbot is a fully-local, privacy-focused RAG (Retrieval-Augmented Generation) chatbot system. All data processing, storage, and inference happens locally using Ollama for LLM capabilities.

**Core Stack:**
- **Backend:** FastAPI + Python 3.11+, SQLAlchemy + SQLite, ChromaDB for vectors, Ollama for LLM
- **Frontend:** Next.js 14+ with App Router, TypeScript, Tailwind CSS, shadcn/ui
- **LLM Models:** Llama 3.2, Mistral, Mixtral via Ollama
- **Embeddings:** nomic-embed-text or mxbai-embed-large

## Development Commands

### Backend Setup & Development
```bash
# Initial setup
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Running the server (with WebSocket support)
uvicorn api.main:socket_app --reload  # Development mode with hot reload
uvicorn api.main:socket_app --host 0.0.0.0 --port 8000  # Production mode

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Testing
pytest                          # Run all tests
pytest backend/tests/test_rag_pipeline.py  # Run specific test file
pytest -v                       # Verbose output
pytest --cov=backend --cov-report=html  # Coverage report

# Code quality
black backend/                  # Format Python code
pylint backend/                 # Lint Python code
```

## Architecture Overview

### Backend Structure
```
backend/
├── api/
│   ├── main.py              # FastAPI app entry point with Socket.IO integration
│   ├── routes/              # API endpoints
│   │   ├── chat.py          # Chat conversation endpoints
│   │   ├── documents.py     # Document upload/management endpoints
│   │   ├── projects.py      # Project CRUD endpoints
│   │   └── llm.py           # LLM configuration and testing endpoints
│   └── websocket/
│       └── chat_ws.py       # WebSocket handlers for real-time chat streaming
├── core/
│   ├── config.py            # Settings and configuration (environment variables)
│   ├── database.py          # Database session management
│   ├── llm.py               # Ollama client wrapper and LLM interactions
│   ├── vectorstore.py       # ChromaDB operations and vector search
│   ├── rag_pipeline.py      # RAG orchestration: retrieval + generation
│   ├── embeddings.py        # Embedding generation via Ollama
│   └── chunking.py          # Text splitting strategies for documents
├── crud/                    # Database CRUD operations
│   ├── chat.py              # Chat and message CRUD
│   ├── document.py          # Document CRUD
│   ├── project.py           # Project CRUD
│   └── *.py                 # Other database operations
├── services/
│   ├── document_processor.py # Extract text from PDF, DOCX, TXT, CSV, XLSX
│   ├── chat_service.py       # Conversation management and history
│   ├── project_service.py    # Project CRUD and isolation logic
│   └── file_storage.py       # File system operations and storage management
├── models/                  # SQLAlchemy ORM models
│   ├── project.py           # Project model
│   ├── document.py          # Document model
│   ├── chat.py              # Chat and Message models
│   └── *.py                 # Other database models
├── tests/                   # Test suite
│   ├── test_rag_pipeline.py # RAG pipeline tests
│   ├── test_document_processor.py # Document processing tests
│   └── *.py                 # Other test files
├── alembic/                 # Database migrations
│   └── versions/            # Migration version files
├── utils/                   # Utility functions
│   └── *.py                 # Helper functions
├── storage/                 # Data storage directories
│   ├── sqlite/              # SQLite database files (metadata, chat history)
│   ├── chroma/              # ChromaDB vector database persistence
│   └── documents/           # Uploaded file storage
└── README/                  # Additional documentation
    ├── FILE_STORAGE_README.md  # File storage system documentation
    └── WEBSOCKET_GUIDE.md      # WebSocket implementation guide
```

### Frontend Structure
```
frontend/
├── src/
│   ├── app/                     # Next.js App Router pages
│   │   ├── layout.tsx          # Root layout with providers (QueryClientProvider, Toaster)
│   │   ├── page.tsx            # Home/landing page
│   │   ├── globals.css         # Global styles and Tailwind CSS imports
│   │   ├── chat/               # Chat interface pages
│   │   ├── projects/           # Project management pages
│   │   └── documents/          # Document management pages
│   ├── components/             # React components
│   │   ├── ui/                 # shadcn/ui primitives (Button, Card, Dialog, Input, etc.)
│   │   ├── chat/               # Chat-specific components
│   │   │   ├── MessageList.tsx         # Display chat messages
│   │   │   ├── MessageInput.tsx        # Message input form
│   │   │   └── SourceReferences.tsx    # RAG source citations
│   │   ├── documents/          # Document management components
│   │   │   ├── DocumentUpload.tsx      # File upload with drag-and-drop
│   │   │   └── DocumentList.tsx        # Document listing
│   │   ├── projects/           # Project components
│   │   │   ├── ProjectCard.tsx         # Project display card
│   │   │   └── CreateProject.tsx       # Project creation form
│   │   ├── layout/             # Layout components (Header, Sidebar, Navigation)
│   │   ├── notifications/      # Notification/toast components
│   │   ├── providers/          # React context providers
│   │   └── theme-provider.tsx  # Theme/dark mode provider
│   ├── lib/                    # Utilities and configurations
│   │   ├── api.ts              # Axios client and API functions
│   │   ├── websocket.ts        # Socket.IO client setup
│   │   └── utils.ts            # Helper functions (cn, formatters, etc.)
│   ├── stores/                 # Zustand state management stores
│   │   ├── chatStore.ts        # Chat messages and streaming state
│   │   ├── projectStore.ts     # Project data and current project
│   │   └── documentStore.ts    # Document management and upload progress
│   ├── types/                  # TypeScript type definitions
│   │   ├── index.ts            # Shared types and interfaces
│   │   └── types.d.ts          # Global type declarations
│   └── hooks/                  # Custom React hooks
│       └── useWebSocket.ts     # WebSocket connection management hook
├── public/                     # Static assets (images, icons)
├── README/                     # Frontend documentation
│   └── README.md              # Comprehensive frontend guide
├── package.json               # Dependencies and scripts
├── tailwind.config.ts         # Tailwind CSS configuration
├── components.json            # shadcn/ui configuration
├── next.config.mjs            # Next.js configuration
├── tsconfig.json              # TypeScript configuration
└── .env.local                 # Environment variables (not in git)
```

### RAG Pipeline Flow
1. **Document Ingestion:** User uploads documents → `document_processor.py` extracts text
2. **Chunking:** Text split into overlapping chunks → `chunking.py` (configurable size/overlap)
3. **Embedding:** Chunks embedded via Ollama → stored in ChromaDB with metadata
4. **Retrieval:** User question embedded → similarity search in ChromaDB → top-k relevant chunks
5. **Generation:** Chunks + question → prompt template → Ollama LLM → response with source attribution
6. **Streaming:** Response streamed via WebSocket to frontend for real-time display

### Project Isolation
- Each project has its own ChromaDB collection (namespace)
- Projects contain isolated sets of documents and chat histories
- Switching projects changes the active context for RAG retrieval
- Database relationships enforce project-document-chat associations

## Key Implementation Details

### RAG Context Management
- **Chunking Strategy:** Recursive text splitter with overlap (default: 1000 chars, 200 overlap)
- **Retrieval:** Top-k similarity search (default k=5) with metadata filtering by project
- **Prompt Template:** System prompt + context chunks + user question + chat history (last N turns)
- **Source Attribution:** Each chunk tracks document_id, page/section, and chunk_index for citation

### Document Processing
- **Supported Formats:** PDF (pypdf), DOCX (python-docx), TXT/MD (direct), CSV/XLSX (openpyxl)
- **Metadata Extraction:** File name, type, size, upload date, page count, word count
- **Processing Pipeline:** Upload → validation → text extraction → chunking → embedding → storage
- **Error Handling:** Failed documents marked with error status, not blocked from retry

### WebSocket Streaming
- **Backend:** python-socketio with FastAPI, rooms per chat session
- **Frontend:** Socket.io-client with auto-reconnect logic
- **Flow:** Client sends message → backend streams tokens → frontend updates UI incrementally
- **Connection Management:** Auth verification on connect, cleanup on disconnect

### State Management
- **Zustand:** Global state for chat messages, projects, documents
- **React Query:** Server state caching, auto-refetch, optimistic updates
- **WebSocket:** Real-time updates bypass React Query for streaming
- **Persistence:** Chat history stored in SQLite, loaded on page load

## Development Workflow

### Adding a New Document Format
1. Add parser in `backend/services/document_processor.py`
2. Update `supported_formats` in config
3. Add format-specific chunking strategy if needed in `backend/core/chunking.py`
4. Update frontend file validation in `components/documents/DocumentUpload.tsx`
5. Test with sample files

### Adding a New API Endpoint
1. Define route in appropriate file in `backend/api/routes/`
2. Implement service logic in `backend/services/`
3. Add request/response Pydantic models
4. Create frontend API client method in `frontend/lib/api.ts`
5. Add React Query hook if needed
6. Update API documentation

### Adding a New UI Component
1. Use shadcn/ui primitives from `components/ui/`
2. Create feature component in appropriate directory (`chat/`, `documents/`, `projects/`)
3. Use Zustand stores for state management
4. Implement loading/error states
5. Add TypeScript types in `frontend/types/`
6. Test responsiveness and accessibility

## Common Gotchas

1. **Ollama Connection:** Ensure Ollama is running (`ollama serve`) before starting backend
2. **Embeddings Model:** Must pull embedding model separately (`ollama pull nomic-embed-text`)
3. **ChromaDB Persistence:** Set `persist_directory` in config or data will be lost on restart
4. **CORS:** Frontend-backend CORS configured in `backend/api/main.py` (CORSMiddleware)
5. **File Size Limits:** Default 10MB per file, configurable in `backend/core/config.py`
6. **WebSocket Ports:** Backend WebSocket uses same port as HTTP (default 8000)
7. **WebSocket App:** Must use `uvicorn api.main:socket_app` (not `app`) to enable WebSocket support
8. **Vector Store per Project:** Each project creates separate ChromaDB collection
9. **Frontend .env:** No `.env.local.example` file exists; create `.env.local` manually with API URLs
10. **Database Migrations:** Run `alembic upgrade head` after pulling changes that modify models

## Environment Configuration

### Backend (.env)
```bash
# Required
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
EMBEDDING_MODEL=nomic-embed-text

# Database
DATABASE_URL=sqlite:///./storage/sqlite/app.db
CHROMA_PERSIST_DIR=./storage/chroma

# Storage
UPLOAD_DIR=./storage/documents
MAX_FILE_SIZE=10485760  # 10MB in bytes

# Optional
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_secret
```

### Frontend (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## Testing Strategy

- **Unit Tests:** Test document processors, chunking logic, embedding generation, CRUD operations
- **Integration Tests:** Test full RAG pipeline, document upload → chat response flow
- **E2E Tests:** Test complete user workflows with Playwright (create project → upload docs → chat)
- **Mock Ollama:** Use mock responses in tests to avoid dependency on running Ollama instance

## Performance Considerations

- **Document Processing:** Process large files asynchronously with progress updates via WebSocket
- **Vector Search:** Batch embeddings during bulk upload, use metadata filters to reduce search space
- **Caching:** Cache frequently accessed chunks and chat histories with Redis (optional)
- **Lazy Loading:** Frontend virtualized lists for 1000+ documents/messages
- **Streaming:** Always stream LLM responses to improve perceived performance

## Security Notes

- **Input Validation:** Sanitize file uploads, check MIME types, scan for malicious content
- **Path Traversal:** Use secure file paths, validate user-provided paths
- **SQL Injection:** Use SQLAlchemy ORM, avoid raw queries
- **Rate Limiting:** Implement per-user rate limits for API endpoints
- **Authentication:** JWT tokens for session management (optional for single-user local deployment)
- **Local-Only:** No external API calls except optional Google Drive integration (requires explicit user auth)
