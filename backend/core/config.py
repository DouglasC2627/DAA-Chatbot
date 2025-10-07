from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application Info
    APP_NAME: str = "DAA Chatbot"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True

    # Ollama Configuration
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    EMBEDDING_MODEL: str = "nomic-embed-text"

    # Database Configuration
    DATABASE_URL: str = "sqlite:///./storage/sqlite/app.db"

    # ChromaDB Configuration
    CHROMA_PERSIST_DIR: str = "./storage/chroma"

    # Storage Configuration
    UPLOAD_DIR: str = "./storage/documents"
    MAX_FILE_SIZE: int = 10485760  # 10MB in bytes

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # CORS Configuration
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        dirs = [
            Path(self.CHROMA_PERSIST_DIR),
            Path(self.UPLOAD_DIR),
            Path(self.DATABASE_URL.replace("sqlite:///", "")).parent
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)


# Create global settings instance
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories()
