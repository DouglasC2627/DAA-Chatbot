"""
Chat model for conversation sessions within a project.
"""
from typing import TYPE_CHECKING

from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .project import Project
    from .message import Message


class Chat(Base, TimestampMixin, SoftDeleteMixin):
    """
    Chat model representing a conversation session within a project.

    Each chat contains a sequence of messages (user questions and assistant responses)
    and is associated with a specific project for context retrieval.

    Attributes:
        id: Primary key
        project_id: Foreign key to parent project
        title: Chat title (auto-generated or user-defined)
        message_count: Cached count of messages in this chat
        created_at: Timestamp when chat was created
        updated_at: Timestamp when chat was last updated
        deleted_at: Timestamp when chat was soft-deleted
        project: Relationship to parent project
        messages: Relationship to messages in this chat
    """
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Chat metadata
    title: Mapped[str] = mapped_column(
        String(512),
        nullable=False,
        default="New Chat"
    )
    message_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="chats"
    )
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Message.created_at"
    )

    def __repr__(self) -> str:
        return f"<Chat(id={self.id}, title='{self.title}', messages={self.message_count})>"

    def generate_title(self, first_message: str, max_length: int = 50) -> str:
        """
        Generate a chat title from the first user message.

        Args:
            first_message: The first message in the chat
            max_length: Maximum length of the title

        Returns:
            Generated title
        """
        # Take first line or max_length characters
        title = first_message.split('\n')[0]
        if len(title) > max_length:
            title = title[:max_length - 3] + "..."
        return title

    @property
    def is_empty(self) -> bool:
        """Check if chat has no messages."""
        return self.message_count == 0

    def increment_message_count(self) -> None:
        """Increment the message count."""
        self.message_count += 1

    def decrement_message_count(self) -> None:
        """Decrement the message count (when deleting messages)."""
        if self.message_count > 0:
            self.message_count -= 1
