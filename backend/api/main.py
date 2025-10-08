from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict
import sys
from pathlib import Path

# Add parent directory to path to import from core
sys.path.append(str(Path(__file__).parent.parent))

from core.config import settings

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
