"""
Project model for organizing documents and chats.
"""
from typing import TYPE_CHECKING

from sqlalchemy import String, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .document import Document
    from .chat import Chat


class Project(Base, TimestampMixin, SoftDeleteMixin):
    """
    Project model for organizing documents and chats into isolated contexts.

    Each project has its own:
    - Set of documents
    - Chat histories
    - ChromaDB collection for vector storage
    - Configuration settings

    Attributes:
        id: Primary key
        name: Project name
        description: Optional project description
        chroma_collection_name: Name of the ChromaDB collection for this project
        document_count: Cached count of documents
        total_chunks: Cached count of embedded chunks
        settings: JSON field for project-specific settings (model, chunk size, etc.)
        created_at: Timestamp when project was created
        updated_at: Timestamp when project was last updated
        deleted_at: Timestamp when project was soft-deleted (null if active)
        documents: Relationship to documents in this project
        chats: Relationship to chats in this project
    """
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    chroma_collection_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True
    )

    # Cached statistics
    document_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chat_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_chunks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Project settings stored as JSON (will be handled by SQLAlchemy JSON type)
    # For now using Text, will upgrade to JSON type when needed
    settings: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    documents: Mapped[list["Document"]] = relationship(
        "Document",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    chats: Mapped[list["Chat"]] = relationship(
        "Chat",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', documents={self.document_count})>"

    def generate_collection_name(self) -> str:
        """
        Generate a unique ChromaDB collection name for this project.

        Returns:
            Formatted collection name
        """
        # ChromaDB collection names must be 3-63 chars, alphanumeric + underscore
        safe_name = "".join(c if c.isalnum() else "_" for c in self.name.lower())
        safe_name = safe_name[:50]  # Leave room for ID suffix
        return f"project_{self.id}_{safe_name}"

    def generate_storage_folder_name(self) -> str:
        """
        Generate a unique storage folder name for this project based on its name.

        The folder name is sanitized to be filesystem-safe and includes the project ID
        for uniqueness. Format: {sanitized_name}_{id}

        Returns:
            Formatted storage folder name (e.g., "my_research_project_1")
        """
        # Sanitize project name for filesystem use
        # Allow only alphanumeric, underscore, hyphen, and spaces (converted to underscore)
        safe_name = ""
        for char in self.name:
            if char.isalnum():
                safe_name += char.lower()
            elif char in (' ', '-', '_'):
                safe_name += '_'
            # Skip all other characters (symbols, special chars)

        # Remove consecutive underscores and trim
        import re
        safe_name = re.sub(r'_+', '_', safe_name).strip('_')

        # Limit length to avoid filesystem issues (max 50 chars for name part)
        safe_name = safe_name[:50].strip('_')

        # If name is empty after sanitization, use a default
        if not safe_name:
            safe_name = "project"

        # Append ID for uniqueness
        return f"{safe_name}_{self.id}"
