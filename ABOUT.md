# ABOUT - Local RAG Chatbot Project

## Project Vision

Build a fully local, privacy-focused RAG (Retrieval-Augmented Generation) chatbot system that enables users to interact with their documents and knowledge bases through an intelligent conversational interface. The system operates entirely on local infrastructure without requiring cloud services, ensuring complete data privacy and ownership.

### Core Philosophy
- **Privacy First**: All data processing, storage, and inference happens locally
- **User Ownership**: Users maintain complete control over their data and conversations
- **Accessible Intelligence**: Bringing LLM capabilities to personal/organizational documents without external dependencies
- **Modular Architecture**: Clean separation between frontend, backend, and data layers for maintainability

## Key Features

### 1. Document Management
- **Multi-file Upload**: Support for PDF, DOCX, TXT, MD, CSV, XLSX formats
- **File Size Limits**: Configurable per-file and total storage limits
- **External Integrations**: Google Drive connectivity for document import
- **Bulk Operations**: Upload and process multiple documents simultaneously
- **Document Metadata**: Track upload date, file type, size, and processing status

### 2. Intelligent Chat Interface
- **Context-Aware Responses**: RAG pipeline ensures responses are grounded in user's documents
- **Source Attribution**: Every response includes clickable references to source documents
- **Response Actions**: Copy, share, or export individual responses
- **Conversation Management**: Save, name, and organize chat histories
- **Real-time Streaming**: Stream responses as they're generated for better UX

### 3. Project Organization
- **Project Workspaces**: Create isolated projects with their own document sets and chat histories
- **Project Switching**: Seamlessly switch between different knowledge bases
- **Project Sharing**: Export/import project configurations and histories
- **Folder Structure**: Organize documents within projects using folders/tags

### 4. Data Persistence
- **Chat History**: Automatic saving with manual deletion options
- **Document Versioning**: Track changes and updates to documents
- **User Preferences**: Save UI settings, model preferences, and system configurations
- **Export Capabilities**: Export chats in MD, JSON, or PDF formats

### 5. Advanced Search & Retrieval
- **Semantic Search**: Vector-based similarity search across all documents
- **Metadata Filtering**: Filter by date, document type, or custom tags
- **Hybrid Search**: Combine keyword and semantic search for better results
- **Relevance Scoring**: Display confidence scores for retrieved chunks

## Technical Stack

### Backend (Python)
```
Core Framework:
- FastAPI (0.104+) - Modern async web framework
- Uvicorn - ASGI server
- Python 3.11+ - Language runtime

LLM Integration:
- Ollama - Local LLM runtime
- ollama-python - Python client for Ollama
- Models: Llama 3.2, Mistral, Mixtral (user selectable)

Vector Database:
- ChromaDB (0.4+) - Embedded vector database
- Embedding Models: nomic-embed-text or mxbai-embed-large

Document Processing:
- LangChain (0.1+) - RAG orchestration
- pypdf - PDF processing
- python-docx - Word document processing
- openpyxl - Excel processing
- python-multipart - File upload handling
- unstructured - Universal document parser

Data Storage:
- SQLAlchemy 2.0+ - ORM for relational data
- SQLite - Local database for metadata
- Filesystem - Document storage

External Integrations:
- google-api-python-client - Google Drive API
- google-auth-httplib2 - Authentication
- google-auth-oauthlib - OAuth flow

Utilities:
- pydantic 2.0+ - Data validation
- python-jose - JWT tokens for auth
- python-dotenv - Environment management
- aiofiles - Async file operations
```

### Frontend (React/Next.js)
```
Core:
- Next.js 14+ - React framework with App Router
- React 18+ - UI library
- TypeScript 5+ - Type safety

UI/UX:
- Tailwind CSS - Utility-first styling
- shadcn/ui - Component library
- Radix UI - Headless components
- Lucide Icons - Icon set
- Framer Motion - Animations

State Management:
- Zustand - Global state management
- TanStack Query - Server state/caching
- React Hook Form - Form management

Communication:
- Axios - HTTP client
- Socket.io-client - WebSocket for real-time updates

Utilities:
- date-fns - Date formatting
- react-markdown - Markdown rendering
- react-syntax-highlighter - Code highlighting
- react-dropzone - File upload UI
```

### Development Tools
```
Version Control:
- Git with GitHub integration in VSCode
- Conventional commits

AI Assistants:
- Gemini Code Assist - Code completion
- Claude Code - Complex problem solving

Code Quality:
- ESLint - JavaScript linting
- Black - Python formatting
- Prettier - Frontend formatting
- pytest - Python testing
- Jest - JavaScript testing
```

## Project Structure

```
rag-chatbot/
├── backend/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry
│   │   ├── routes/
│   │   │   ├── chat.py          # Chat endpoints
│   │   │   ├── documents.py     # Document management
│   │   │   ├── projects.py      # Project management
│   │   │   ├── auth.py          # Authentication
│   │   │   └── integrations.py  # External services
│   │   ├── middleware/
│   │   │   ├── cors.py
│   │   │   ├── auth.py
│   │   │   └── rate_limit.py
│   │   └── websocket/
│   │       └── chat_ws.py       # WebSocket handlers
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py            # Settings management
│   │   ├── llm.py               # Ollama integration
│   │   ├── vectorstore.py       # ChromaDB operations
│   │   ├── rag_pipeline.py      # RAG orchestration
│   │   ├── embeddings.py        # Embedding generation
│   │   └── chunking.py          # Text splitting strategies
│   ├── services/
│   │   ├── document_processor.py
│   │   ├── chat_service.py
│   │   ├── project_service.py
│   │   └── google_drive.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base.py              # Base SQLAlchemy model
│   │   ├── project.py           # Project model
│   │   ├── chat.py              # Chat/message models
│   │   ├── document.py          # Document model
│   │   └── user.py              # User preferences
│   ├── storage/
│   │   ├── sqlite/              # SQLite database files
│   │   ├── chroma/              # ChromaDB persistence
│   │   └── documents/           # Uploaded files
│   ├── utils/
│   │   ├── validators.py
│   │   ├── exceptions.py
│   │   └── helpers.py
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── Dockerfile
├── frontend/
│   ├── app/                     # Next.js App Router
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── projects/
│   │   │   ├── page.tsx
│   │   │   └── [id]/
│   │   │       └── page.tsx
│   │   ├── chat/
│   │   │   └── [projectId]/
│   │   │       └── page.tsx
│   │   └── api/                 # API route handlers
│   ├── components/
│   │   ├── ui/                  # shadcn/ui components
│   │   ├── chat/
│   │   │   ├── ChatInterface.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   └── SourceReferences.tsx
│   │   ├── documents/
│   │   │   ├── DocumentUpload.tsx
│   │   │   ├── DocumentList.tsx
│   │   │   └── DocumentViewer.tsx
│   │   ├── projects/
│   │   │   ├── ProjectList.tsx
│   │   │   ├── ProjectCreate.tsx
│   │   │   └── ProjectSettings.tsx
│   │   └── layout/
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── Footer.tsx
│   ├── lib/
│   │   ├── api.ts               # API client
│   │   ├── websocket.ts         # WebSocket client
│   │   └── utils.ts
│   ├── stores/
│   │   ├── chatStore.ts
│   │   ├── projectStore.ts
│   │   └── documentStore.ts
│   ├── types/
│   │   └── index.ts
│   ├── styles/
│   │   └── globals.css
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── .env.local.example
│   └── Dockerfile
├── docker-compose.yml
├── .gitignore
├── README.md
└── ABOUT.md
```

## Implementation Roadmap

### Phase 1: Foundation
1. **Backend Setup**
   - Initialize FastAPI application with basic structure
   - Set up SQLAlchemy models and SQLite database
   - Configure Ollama connection and test LLM inference
   - Implement basic document upload and storage

2. **Vector Store Setup**
   - Initialize ChromaDB with persistent storage
   - Implement document chunking strategies
   - Create embedding pipeline
   - Test basic similarity search

3. **Basic RAG Pipeline**
   - Connect document retrieval with LLM
   - Implement simple prompt templates
   - Create basic chat endpoint
   - Test end-to-end RAG flow

### Phase 2: Core Features
1. **Document Processing**
   - Implement multi-format support (PDF, DOCX, TXT)
   - Add metadata extraction
   - Create document management endpoints
   - Implement file size validation

2. **Chat System**
   - Build chat history persistence
   - Add conversation management
   - Implement source attribution
   - Create WebSocket for real-time streaming

3. **Frontend Foundation**
   - Set up Next.js with TypeScript
   - Configure Tailwind and shadcn/ui
   - Create basic layout components
   - Implement routing structure

### Phase 3: Project Management
1. **Project System**
   - Implement project CRUD operations
   - Add project-document associations
   - Create project switching logic
   - Build isolation between projects

2. **Frontend Integration**
   - Build chat interface components
   - Implement document upload UI
   - Create project management views
   - Add state management with Zustand

3. **Real-time Features**
   - Integrate WebSocket client
   - Implement streaming responses
   - Add live document processing status
   - Create notification system

### Phase 4: Advanced Features
1. **External Integrations**
   - Implement Google Drive OAuth
   - Build document import from Drive
   - Add integration management UI
   - Create sync mechanisms

2. **Search & Retrieval**
   - Implement hybrid search
   - Add metadata filtering
   - Create advanced query options
   - Build search UI components

3. **Export & Sharing**
   - Implement chat export (MD, JSON, PDF)
   - Add project export/import
   - Create shareable links
   - Build collaboration features

### Phase 5: Polish & Optimization
1. **Performance**
   - Optimize chunking strategies
   - Implement caching layers
   - Add lazy loading for documents
   - Optimize vector search queries

2. **User Experience**
   - Add loading states and skeletons
   - Implement error boundaries
   - Create onboarding flow
   - Add keyboard shortcuts

3. **Testing & Documentation**
   - Write unit tests for critical paths
   - Create integration tests
   - Document API endpoints
   - Write user guide

## API Endpoints Design

### Authentication
```
POST   /api/auth/login
POST   /api/auth/logout  
GET    /api/auth/me
```

### Projects
```
GET    /api/projects                 # List all projects
POST   /api/projects                 # Create project
GET    /api/projects/{id}           # Get project details
PUT    /api/projects/{id}           # Update project
DELETE /api/projects/{id}           # Delete project
POST   /api/projects/{id}/export    # Export project
POST   /api/projects/import         # Import project
```

### Documents
```
GET    /api/projects/{id}/documents      # List documents
POST   /api/projects/{id}/documents      # Upload documents
GET    /api/documents/{id}               # Get document
DELETE /api/documents/{id}               # Delete document
GET    /api/documents/{id}/content       # Get document content
POST   /api/documents/process            # Process uploaded documents
```

### Chat
```
GET    /api/projects/{id}/chats          # List chats
POST   /api/projects/{id}/chats          # Create chat
GET    /api/chats/{id}                   # Get chat history
POST   /api/chats/{id}/messages          # Send message
DELETE /api/chats/{id}                   # Delete chat
POST   /api/chats/{id}/export            # Export chat
WS     /ws/chat/{id}                     # WebSocket for streaming
```

### Integrations
```
GET    /api/integrations                 # List integrations
POST   /api/integrations/google/auth     # Start Google OAuth
GET    /api/integrations/google/callback # OAuth callback
GET    /api/integrations/google/files    # List Google Drive files
POST   /api/integrations/google/import   # Import from Drive
```

### System
```
GET    /api/system/models               # List available LLM models
GET    /api/system/stats                # System statistics
POST   /api/system/settings             # Update settings
GET    /api/health                      # Health check
```

## Development Guidelines

### Code Standards
1. **Python Backend**
   - Follow PEP 8 style guide
   - Use type hints for all functions
   - Write docstrings for classes and complex functions
   - Handle exceptions gracefully
   - Use async/await for I/O operations

2. **React/TypeScript Frontend**
   - Use functional components with hooks
   - Implement proper TypeScript types
   - Follow React best practices
   - Use proper error boundaries
   - Implement loading and error states

3. **General**
   - Write self-documenting code
   - Keep functions small and focused
   - Use meaningful variable names
   - Comment complex logic
   - Maintain consistent formatting

### Testing Strategy
1. **Unit Tests**
   - Test document processing functions
   - Test RAG pipeline components
   - Test API endpoint handlers
   - Test React components

2. **Integration Tests**
   - Test full RAG flow
   - Test document upload and processing
   - Test chat conversation flow
   - Test external integrations

3. **E2E Tests**
   - Test complete user workflows
   - Test project creation and management
   - Test document upload and chat

### Security Considerations
1. **Data Protection**
   - Sanitize all user inputs
   - Implement file type validation
   - Use parameterized database queries
   - Encrypt sensitive configuration

2. **Access Control**
   - Implement basic authentication
   - Use JWT tokens for sessions
   - Validate file uploads
   - Rate limit API endpoints

3. **Local Security**
   - Secure storage directories
   - Implement backup mechanisms
   - Log security events
   - Regular security updates

## Performance Targets

### Backend
- Document processing: < 5 seconds per MB
- Vector search: < 500ms for 10k documents
- Chat response start: < 2 seconds
- API response time: < 200ms average

### Frontend
- Initial page load: < 3 seconds
- Route transitions: < 100ms
- File upload feedback: Immediate
- Chat message rendering: Real-time

### System Requirements
- RAM: Minimum 8GB, Recommended 16GB
- Storage: 50GB+ for documents and models
- CPU: 4+ cores recommended
- GPU: Optional but improves LLM performance

## Success Metrics

1. **Functionality**
   - All file formats supported
   - RAG accuracy > 90% for factual queries
   - Source attribution 100% accurate
   - Zero data loss incidents

2. **Performance**
   - Meet all performance targets
   - Support 1000+ documents per project
   - Handle 10+ concurrent chat sessions

3. **User Experience**
   - Intuitive interface requiring no manual
   - Responsive design for all screen sizes
   - Clear error messages and recovery
   - Smooth animations and transitions

## Notes

When building this project:

1. **Start Simple**: Begin with basic functionality and iterate
2. **Test Frequently**: Verify each component works before moving on
3. **Document as You Go**: Keep code well-commented
4. **Handle Errors**: Implement proper error handling from the start
5. **Think Modular**: Build reusable components and functions
6. **Consider UX**: Always think about the end-user experience
7. **Optimize Later**: Focus on functionality first, then optimize
8. **Security First**: Implement security measures early
9. **Use Types**: Leverage TypeScript and Python type hints
10. **Follow Patterns**: Maintain consistent patterns throughout

This is a comprehensive project that balances functionality with local deployment constraints. The key is maintaining clean architecture while ensuring smooth user experience.