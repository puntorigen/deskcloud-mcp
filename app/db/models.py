"""
SQLAlchemy ORM Models
=====================

Defines the database schema for session and message storage.
Uses async-compatible column types for SQLite and PostgreSQL.

Tables:
- sessions: Chat session metadata and configuration
- messages: Individual messages within sessions (user, assistant, tool)
"""

import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.
    
    Provides common configuration and can be extended with
    shared columns or methods if needed.
    """
    pass


class SessionStatus(enum.Enum):
    """
    Possible states for a chat session.
    
    State transitions:
        ACTIVE -> PROCESSING (when message sent)
        PROCESSING -> ACTIVE (when response complete)
        PROCESSING -> ERROR (on failure)
        ACTIVE -> COMPLETED (manually ended)
        * -> ARCHIVED (soft delete)
    """
    ACTIVE = "active"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    ARCHIVED = "archived"


def generate_uuid() -> str:
    """Generate a prefixed UUID for readable identification."""
    return f"sess_{uuid.uuid4().hex[:12]}"


def generate_message_uuid() -> str:
    """Generate a prefixed UUID for messages."""
    return f"msg_{uuid.uuid4().hex[:12]}"


class Session(Base):
    """
    Represents a computer use agent chat session.
    
    Each session maintains its own conversation history,
    configuration, and state. Sessions are isolated from
    each other and persist across container restarts.
    
    Attributes:
        id: Unique session identifier (prefixed UUID)
        title: Human-readable session name (auto-generated if not provided)
        status: Current session state
        model: Claude model identifier (e.g., claude-sonnet-4-5-20250929)
        provider: API provider (anthropic, bedrock, vertex)
        system_prompt_suffix: Custom instructions appended to system prompt
        created_at: Session creation timestamp
        updated_at: Last modification timestamp
        messages: Related message history (ordered by creation time)
    """
    
    __tablename__ = "sessions"
    
    # Primary key with readable prefix
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    
    # Session metadata
    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        doc="Human-readable session title",
    )
    
    status: Mapped[SessionStatus] = mapped_column(
        Enum(SessionStatus),
        default=SessionStatus.ACTIVE,
        nullable=False,
        index=True,
        doc="Current session state",
    )
    
    # Model configuration
    model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Claude model identifier",
    )
    
    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="anthropic",
        doc="API provider (anthropic, bedrock, vertex)",
    )
    
    system_prompt_suffix: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Custom instructions appended to system prompt",
    )
    
    # Display configuration (for multi-session isolation)
    display_num: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="X11 display number (e.g., 1 for DISPLAY=:1)",
    )
    
    vnc_port: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="VNC server port for this session",
    )
    
    novnc_port: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="noVNC web interface port for this session",
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        doc="Session creation timestamp",
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        doc="Last modification timestamp",
    )
    
    # Last activity timestamp for TTL tracking
    last_activity: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        doc="Last user activity timestamp (for session TTL)",
    )
    
    # Relationships
    messages: Mapped[list["Message"]] = relationship(
        "Message",
        back_populates="session",
        order_by="Message.created_at",
        cascade="all, delete-orphan",
        lazy="selectin",  # Eager load for better performance
    )
    
    def __repr__(self) -> str:
        return f"<Session(id={self.id}, title={self.title}, status={self.status.value})>"
    
    def to_anthropic_messages(self) -> list[dict[str, Any]]:
        """
        Convert session messages to Anthropic API format.
        
        Returns a list of message dicts compatible with
        the sampling_loop messages parameter.
        """
        return [msg.to_anthropic_format() for msg in self.messages]


class Message(Base):
    """
    Represents a single message in a chat session.
    
    Messages can be from the user, assistant (Claude), or tool results.
    The content is stored as JSON to preserve the full structure
    of Anthropic API message blocks.
    
    Attributes:
        id: Unique message identifier (prefixed UUID)
        session_id: Parent session reference
        role: Message sender (user, assistant, tool)
        content: Message content (JSON - preserves all block types)
        tool_use_id: For tool results, the associated tool_use block ID
        created_at: Message timestamp
    """
    
    __tablename__ = "messages"
    
    # Primary key
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_message_uuid,
    )
    
    # Foreign key to session
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Message metadata
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Message role: user, assistant, or tool",
    )
    
    # Content stored as JSON to preserve structure
    # Can contain: text blocks, tool_use blocks, tool_result blocks, etc.
    content: Mapped[dict[str, Any] | list[Any]] = mapped_column(
        JSON,
        nullable=False,
        doc="Message content (preserves all Anthropic block types)",
    )
    
    # For tool result messages, reference the tool_use block
    tool_use_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        doc="For tool results, the associated tool_use block ID",
    )
    
    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )
    
    # Relationship
    session: Mapped["Session"] = relationship(
        "Session",
        back_populates="messages",
    )
    
    def __repr__(self) -> str:
        content_preview = str(self.content)[:50] + "..." if len(str(self.content)) > 50 else str(self.content)
        return f"<Message(id={self.id}, role={self.role}, content={content_preview})>"
    
    def to_anthropic_format(self) -> dict[str, Any]:
        """
        Convert to Anthropic API message format.
        
        Returns dict compatible with BetaMessageParam.
        """
        result = {
            "role": self.role if self.role != "tool" else "user",
            "content": self.content,
        }
        return result

