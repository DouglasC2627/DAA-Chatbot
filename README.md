# DAA Chatbot

A fully-local, privacy-focused RAG (Retrieval-Augmented Generation) chatbot system. All data processing, storage, and inference happens locally using Ollama for LLM capabilities.

***Project currently under construction!***

## Features

- **100% Local**: All data stays on your machine
- **RAG-Powered**: Retrieval-Augmented Generation for accurate, context-aware responses
- **Multi-Format Support**: PDF, DOCX, TXT, MD, CSV, XLSX
- **Project Isolation**: Organize documents and conversations by project
- **Real-time Streaming**: WebSocket-based streaming responses

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: SQLAlchemy + SQLite
- **Vector Store**: ChromaDB
- **LLM**: Ollama (Llama 3.2)
- **Embeddings**: nomic-embed-text or mxbai-embed-large

### Frontend
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **State Management**: Zustand + React Query
- **Real-time**: Socket.io

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.11 or higher
- Node.js 18+ and npm
- Git
- Ollama (for local LLM inference)

## Quick Start

### 1. Install Ollama and Models

```bash
# Install Ollama from https://ollama.com

# Pull required models
ollama pull llama3.2
ollama pull nomic-embed-text
```

### 2. Clone and Setup Backend

#### Option A: Automated Setup (Recommended)
```bash
# Clone the repository
git clone <your-repo-url>
cd daa-chatbot/backend

# Run automated setup script
./scripts/setup.sh

# Start the backend server
source venv/bin/activate
uvicorn api.main:socket_app --reload
```

#### Option B: Manual Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd daa-chatbot

# Set up backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env  # Edit with your settings

# **IMPORTANT: Run database migrations**
alembic upgrade head

# Initialize database with default settings
python scripts/init_db.py

# Verify setup (optional but recommended)
python scripts/check_setup.py

# Run backend server (with WebSocket support)
uvicorn api.main:socket_app --reload
```

Backend will be available at http://localhost:8000

### 3. Setup Frontend

```bash
# In a new terminal
cd frontend
npm install

# Create .env.local file
echo "NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000" > .env.local

# Run frontend dev server
npm run dev
```

Frontend will be available at http://localhost:3000

## Development Setup

### Backend Development

```bash
cd backend
source venv/bin/activate

# Install development dependencies
pip install -r requirements.txt

# Run database migrations (after model changes)
alembic revision --autogenerate -m "description"
alembic upgrade head

# Verify setup before starting
python scripts/check_setup.py

# Run with hot reload (with WebSocket support)
uvicorn api.main:socket_app --reload --host 0.0.0.0 --port 8000

# Format code
black backend/

# Lint code
pylint backend/

# Run tests
pytest
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev

# Lint and format
npm run lint
npm run format

# Build for production
npm run build
npm start
```

### VSCode Setup

This project includes VSCode workspace settings for optimal development experience:

- Auto-formatting on save (Black for Python, Prettier for TypeScript)
- ESLint and Pylint integration
- Recommended extensions (see `.vscode/extensions.json`)

Install recommended extensions when prompted by VSCode.

### Pre-commit Hooks

Git hooks are configured to run code quality checks before commits:

```bash
# Hooks are automatically set up in .git/hooks/pre-commit
# They will check:
# - Python: Black formatting, Pylint linting
# - TypeScript: ESLint, Prettier formatting
# - General: trailing whitespace, file size, merge conflicts
```

## Project Structure

```
daa-chatbot/
├── backend/              # FastAPI backend
│   ├── api/
│   │   ├── routes/      # API endpoints (chat, documents, projects, llm)
│   │   ├── websocket/   # WebSocket handlers for real-time chat
│   │   └── main.py      # FastAPI app entry point with Socket.IO
│   ├── core/            # Core functionality
│   │   ├── rag_pipeline.py    # RAG orchestration
│   │   ├── llm.py             # Ollama client wrapper
│   │   ├── vectorstore.py     # ChromaDB operations
│   │   ├── embeddings.py      # Embedding generation
│   │   └── chunking.py        # Text splitting strategies
│   ├── models/          # SQLAlchemy database models
│   ├── services/        # Business logic
│   │   ├── chat_service.py       # Conversation management
│   │   ├── document_processor.py # Document text extraction
│   │   ├── project_service.py    # Project CRUD operations
│   │   └── file_storage.py       # File management
│   ├── crud/            # Database CRUD operations
│   └── storage/         # Data storage (SQLite, ChromaDB, uploads)
├── frontend/            # Next.js frontend
│   └── src/
│       ├── app/         # Next.js app router
│       │   ├── page.tsx           # Home page
│       │   ├── layout.tsx         # Root layout
│       │   ├── chat/              # Chat pages
│       │   ├── projects/          # Project management
│       │   └── documents/         # Document management
│       ├── components/  # React components
│       │   ├── ui/                # shadcn/ui components
│       │   ├── chat/              # Chat interface components
│       │   ├── documents/         # Document upload components
│       │   └── projects/          # Project components
│       ├── lib/         # Utilities and API clients
│       ├── stores/      # Zustand state management
│       └── types/       # TypeScript type definitions
└── docker-compose.yml   # Docker configuration
```

## Environment Variables

### Backend (.env)

```bash
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2
EMBEDDING_MODEL=nomic-embed-text
DATABASE_URL=sqlite:///./storage/sqlite/app.db
CHROMA_PERSIST_DIR=./storage/chroma
UPLOAD_DIR=./storage/documents
MAX_FILE_SIZE=10485760  # 10MB
```

### Frontend (.env.local)

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## API Documentation

Once the backend is running, visit:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

### Backend Tests

```bash
cd backend
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest --cov=backend      # With coverage
```

### Frontend Tests

```bash
cd frontend
npm test                  # Run tests
npm run test:watch        # Watch mode
```

## Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in background
docker-compose up -d

# Stop services
docker-compose down
```

**Note**: Ollama must be running on the host machine. The docker-compose.yml is configured to connect to Ollama via `host.docker.internal`.

## Common Issues

### Database Tables Missing (400 Bad Request on Project Creation)
**Symptom**: API returns 400 error when creating projects, or server fails to start with "Missing tables" error.

**Solution**:
```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

The server now includes startup validation that will prevent it from starting if migrations haven't been run.

### Ollama Connection Error
- Ensure Ollama is running: `ollama serve`
- Check if models are pulled: `ollama list`

### Port Already in Use
- Backend (8000): Change port in uvicorn command
- Frontend (3000): Set PORT=3001 in .env.local

### Module Not Found
- Backend: Ensure virtual environment is activated
- Frontend: Run `npm install`

### Setup Verification
Run the pre-flight check script to verify your backend setup:
```bash
cd backend
source venv/bin/activate
python scripts/check_setup.py
```

This will check:
- Database tables exist
- Storage directories are created
- Configuration files are present
- Ollama connection (optional)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request

## License

[MIT License](LICENSE)

## Acknowledgments

- Built with [Ollama](https://ollama.com)
- UI components from [shadcn/ui](https://ui.shadcn.com)
- Powered by [FastAPI](https://fastapi.tiangolo.com) and [Next.js](https://nextjs.org)
