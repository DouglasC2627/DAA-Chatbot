from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import sys
from pathlib import Path
import socketio

# Add parent directory to path to import from core
sys.path.append(str(Path(__file__).parent.parent))

from core.config import settings
from api.routes import llm, chat, documents, projects
from api.websocket.chat_ws import sio

app = FastAPI(
    title="DAA Chatbot API",
    description="Local RAG Chatbot API for document-based conversations",
    version="0.1.0"
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
    """API health check endpoint"""
    return {
        "status": "ok",
        "ollama_configured": settings.OLLAMA_HOST,
        "database_path": settings.DATABASE_URL
    }


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
