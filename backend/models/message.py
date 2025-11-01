"""
Message model for individual messages within a chat conversation.
"""
from typing import TYPE_CHECKING
from enum import Enum

from sqlalchemy import String, Text, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin

if TYPE_CHECKING:
    from .chat import Chat


class MessageRole(str, Enum):
    """Role of the message sender."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(Base, TimestampMixin):
    """
    Message model for individual messages in a chat conversation.

    Messages are not soft-deletable to preserve conversation history integrity.

    Attributes:
        id: Primary key
        chat_id: Foreign key to parent chat
        role: Role of message sender (user, assistant, system)
        content: Message content/text
        sources: JSON array of source references used for this message
        model_name: Name of the LLM model used (for assistant messages)
        token_count: Approximate token count
        metadata: Additional metadata (retrieval scores, etc.)
        created_at: Timestamp when message was created
        updated_at: Timestamp when message was last updated
        chat: Relationship to parent chat
    """
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Message content
    role: Mapped[MessageRole] = mapped_column(
        SQLEnum(MessageRole),
        nullable=False,
        index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Source attribution (stored as JSON)
    sources: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Model information (for assistant messages)
    model_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    token_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Additional metadata (stored as JSON)
    # Note: "metadata" is reserved by SQLAlchemy, so we use "msg_metadata"
    msg_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    chat: Mapped["Chat"] = relationship(
        "Chat",
        back_populates="messages"
    )

    def __repr__(self) -> str:
        content_preview = self.content[:50] + "..." if len(self.content) > 50 else self.content
        return f"<Message(id={self.id}, role={self.role.value}, content='{content_preview}')>"

    @property
    def is_user_message(self) -> bool:
        """Check if this is a user message."""
        return self.role == MessageRole.USER

    @property
    def is_assistant_message(self) -> bool:
        """Check if this is an assistant message."""
        return self.role == MessageRole.ASSISTANT

    @property
    def is_system_message(self) -> bool:
        """Check if this is a system message."""
        return self.role == MessageRole.SYSTEM

    @property
    def has_sources(self) -> bool:
        """Check if this message has source references."""
        return self.sources is not None and len(self.sources) > 0

    def set_sources(self, sources: list[dict]) -> None:
        """
        Set source references for this message.

        Args:
            sources: List of source reference dictionaries
        """
        import json
        self.sources = json.dumps(sources) if sources else None

    def get_sources(self) -> list[dict]:
        """
        Get parsed source references.

        Returns:
            List of source reference dictionaries
        """
        import json
        if not self.sources:
            return []
        try:
            return json.loads(self.sources)
        except (json.JSONDecodeError, TypeError):
            return []
