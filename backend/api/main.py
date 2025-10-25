from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import sys
from pathlib import Path
import socketio
import logging
from contextlib import asynccontextmanager
from sqlalchemy import inspect

# Add parent directory to path to import from core
sys.path.append(str(Path(__file__).parent.parent))

from core.config import settings
from api.routes import llm, chat, documents, projects, maintenance
from api.websocket.chat_ws import sio
from core.database import sync_engine, async_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.

    Startup:
    - Verifies database tables exist
    - Checks if migrations are up to date

    Shutdown:
    - Closes database connections
    """
    # Startup
    try:
        logger.info("🚀 Starting DAA Chatbot API...")

        # Verify tables exist
        inspector = inspect(sync_engine)
        tables = inspector.get_table_names()

        required_tables = ['projects', 'documents', 'chats', 'messages']
        missing_tables = [table for table in required_tables if table not in tables]

        if missing_tables:
            error_msg = (
                f"❌ Database not initialized. Missing tables: {', '.join(missing_tables)}\n"
                f"   Please run: alembic upgrade head"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info(f"✅ Database check passed - {len(tables)} tables found")

        # Create storage directories if they don't exist
        storage_dirs = [
            Path(settings.UPLOAD_DIR),
            Path(settings.CHROMA_PERSIST_DIR),
            Path(settings.DATABASE_URL.replace("sqlite:///", "")).parent,
        ]

        for directory in storage_dirs:
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"📁 Created storage directory: {directory}")

        logger.info("✅ Startup complete - API is ready")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down DAA Chatbot API...")
    await async_engine.dispose()
    logger.info("✅ Shutdown complete")


app = FastAPI(
    title="DAA Chatbot API",
    description="Local RAG Chatbot API for document-based conversations",
    version="0.1.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(llm.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(projects.router)
app.include_router(maintenance.router)


class HealthResponse(BaseModel):
    status: str
    message: str
    version: str


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint"""
    return {"message": "DAA Chatbot API - Use /docs for API documentation"}


@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="DAA Chatbot API is running",
        version="0.1.0"
    )


@app.get("/api/health")
async def api_health() -> Dict[str, str]:
    """
    Enhanced API health check endpoint.

    Returns:
        Health status including database connection and table verification
    """
    health_status = {
        "status": "ok",
        "ollama_configured": settings.OLLAMA_HOST,
        "database_path": settings.DATABASE_URL,
    }

    # Check database connection and tables
    try:
        # Verify we can connect and query
        inspector = inspect(sync_engine)
        tables = inspector.get_table_names()

        required_tables = ['projects', 'documents', 'chats', 'messages']
        missing_tables = [table for table in required_tables if table not in tables]

        if missing_tables:
            health_status["database_status"] = "error"
            health_status["database_error"] = f"Missing tables: {', '.join(missing_tables)}"
            health_status["status"] = "degraded"
        else:
            health_status["database_status"] = "connected"
            health_status["tables_count"] = len(tables)

    except Exception as e:
        health_status["database_status"] = "error"
        health_status["database_error"] = str(e)
        health_status["status"] = "degraded"

    return health_status


# Create combined ASGI application with Socket.IO
# This wraps the FastAPI app with Socket.IO support
socket_app = socketio.ASGIApp(
    socketio_server=sio,
    other_asgi_app=app,
    socketio_path='/socket.io'
)

# Export socket_app as the main application for uvicorn
# Use: uvicorn api.main:socket_app --reload
# This ensures both FastAPI routes and WebSocket work together
application = socket_app


if __name__ == "__main__":
    import uvicorn
    # Run the combined Socket.IO + FastAPI application
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
