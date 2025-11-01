"""
Document model for storing uploaded files and their metadata.
"""
from typing import TYPE_CHECKING
from enum import Enum

from sqlalchemy import String, Text, Integer, ForeignKey, Enum as SQLEnum, BigInteger
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .project import Project


class DocumentStatus(str, Enum):
    """Status of document processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    ERROR = "error"


class DocumentType(str, Enum):
    """Supported document types."""
    PDF = "pdf"
    DOCX = "docx"
    TXT = "txt"
    MD = "md"
    CSV = "csv"
    XLSX = "xlsx"
    OTHER = "other"


class Document(Base, TimestampMixin, SoftDeleteMixin):
    """
    Document model for uploaded files and their processing metadata.

    Attributes:
        id: Primary key
        project_id: Foreign key to parent project
        filename: Original filename
        file_path: Path to stored file on disk
        file_size: Size in bytes
        file_type: Type of document (pdf, docx, etc.)
        mime_type: MIME type of the file
        status: Processing status
        error_message: Error details if processing failed
        page_count: Number of pages (for PDFs)
        word_count: Approximate word count
        chunk_count: Number of chunks created from this document
        metadata: Additional metadata stored as JSON (author, title, etc.)
        created_at: Upload timestamp
        updated_at: Last updated timestamp
        deleted_at: Soft delete timestamp
        project: Relationship to parent project
    """
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # File information
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    file_type: Mapped[DocumentType] = mapped_column(
        SQLEnum(DocumentType),
        nullable=False,
        index=True
    )
    mime_type: Mapped[str] = mapped_column(String(255), nullable=False)

    # Processing status
    status: Mapped[DocumentStatus] = mapped_column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.PENDING,
        nullable=False,
        index=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Document statistics
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    word_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Metadata stored as JSON (will be upgraded to JSON type later)
    # Note: "metadata" is reserved by SQLAlchemy, so we use "doc_metadata"
    doc_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="documents"
    )

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, filename='{self.filename}', status={self.status.value})>"

    @property
    def file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size / (1024 * 1024)

    @property
    def is_processed(self) -> bool:
        """Check if document processing is complete."""
        return self.status == DocumentStatus.COMPLETED

    @property
    def has_error(self) -> bool:
        """Check if document processing failed."""
        return self.status in (DocumentStatus.FAILED, DocumentStatus.ERROR)

    def mark_processing(self) -> None:
        """Mark document as currently processing."""
        self.status = DocumentStatus.PROCESSING
        self.error_message = None

    def mark_completed(self, chunk_count: int, word_count: int | None = None) -> None:
        """
        Mark document as successfully processed.

        Args:
            chunk_count: Number of chunks created
            word_count: Word count if available
        """
        self.status = DocumentStatus.COMPLETED
        self.chunk_count = chunk_count
        if word_count is not None:
            self.word_count = word_count
        self.error_message = None

    def mark_failed(self, error_message: str) -> None:
        """
        Mark document processing as failed.

        Args:
            error_message: Description of the error
        """
        self.status = DocumentStatus.FAILED
        self.error_message = error_message
