"""
User settings model for application-wide configuration.
"""
from sqlalchemy import String, Text, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class UserSettings(Base, TimestampMixin):
    """
    User settings model for global application configuration.

    For single-user local deployment, there will typically be only one row.
    Settings include default models, chunk sizes, UI preferences, etc.

    Attributes:
        id: Primary key
        user_id: User identifier (for future multi-user support)
        default_llm_model: Default LLM model name (e.g., "llama3.2")
        default_embedding_model: Default embedding model
        default_chunk_size: Default chunk size for text splitting
        default_chunk_overlap: Default overlap between chunks
        default_retrieval_k: Default number of chunks to retrieve
        theme: UI theme preference (light/dark)
        google_drive_enabled: Whether Google Drive integration is enabled
        google_drive_token: Encrypted Google Drive OAuth token
        settings_json: Additional settings stored as JSON
        created_at: Timestamp when settings were created
        updated_at: Timestamp when settings were last updated
    """
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        default="default_user",
        index=True
    )

    # LLM Configuration
    default_llm_model: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="llama3.2"
    )
    default_embedding_model: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="nomic-embed-text"
    )

    # RAG Configuration
    default_chunk_size: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1000
    )
    default_chunk_overlap: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=200
    )
    default_retrieval_k: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5
    )

    # UI Preferences
    theme: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="light"
    )

    # Integration Settings
    google_drive_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False
    )
    google_drive_token: Mapped[str | None] = mapped_column(
        Text,
        nullable=True  # Encrypted token storage
    )

    # Additional settings as JSON
    settings_json: Mapped[str | None] = mapped_column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"<UserSettings(id={self.id}, user_id='{self.user_id}', model='{self.default_llm_model}')>"

    @property
    def is_google_drive_connected(self) -> bool:
        """Check if Google Drive is connected."""
        return self.google_drive_enabled and self.google_drive_token is not None

    def disconnect_google_drive(self) -> None:
        """Disconnect Google Drive integration."""
        self.google_drive_enabled = False
        self.google_drive_token = None

    def update_model_defaults(self, llm_model: str | None = None, embedding_model: str | None = None) -> None:
        """
        Update default model settings.

        Args:
            llm_model: New default LLM model
            embedding_model: New default embedding model
        """
        if llm_model:
            self.default_llm_model = llm_model
        if embedding_model:
            self.default_embedding_model = embedding_model

    def update_rag_defaults(
        self,
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
        retrieval_k: int | None = None
    ) -> None:
        """
        Update RAG configuration defaults.

        Args:
            chunk_size: New default chunk size
            chunk_overlap: New default chunk overlap
            retrieval_k: New default retrieval count
        """
        if chunk_size is not None:
            self.default_chunk_size = chunk_size
        if chunk_overlap is not None:
            self.default_chunk_overlap = chunk_overlap
        if retrieval_k is not None:
            self.default_retrieval_k = retrieval_k
