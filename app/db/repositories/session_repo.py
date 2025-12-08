"""
Session Repository
==================

Data access layer for Session and Message models.
Encapsulates all database operations for cleaner service layer code.

Design Philosophy:
- Each method performs a single, focused operation
- All operations are async for non-blocking I/O
- Returns domain models, not raw query results
- Handles common patterns like "get or 404"
"""

from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Message, Session, SessionStatus


class SessionRepository:
    """
    Repository for Session and Message database operations.
    
    Follows the repository pattern to abstract database access
    from the service layer. All methods are async.
    
    Usage:
        repo = SessionRepository(db_session)
        session = await repo.create_session(title="My Task", model="claude-...")
        await repo.add_message(session.id, "user", {"text": "Hello"})
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize repository with database session.
        
        Args:
            db: Async SQLAlchemy session from dependency injection
        """
        self.db = db
    
    # =========================================================================
    # Session CRUD Operations
    # =========================================================================
    
    async def create_session(
        self,
        model: str,
        provider: str = "anthropic",
        title: str | None = None,
        system_prompt_suffix: str | None = None,
    ) -> Session:
        """
        Create a new chat session.
        
        Args:
            model: Claude model identifier
            provider: API provider (anthropic, bedrock, vertex)
            title: Optional human-readable title
            system_prompt_suffix: Optional custom system prompt addition
        
        Returns:
            Newly created Session instance with generated ID
        """
        session = Session(
            model=model,
            provider=provider,
            title=title or f"Session {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}",
            system_prompt_suffix=system_prompt_suffix,
            status=SessionStatus.ACTIVE,
        )
        
        self.db.add(session)
        await self.db.flush()  # Populate ID without committing
        await self.db.refresh(session)
        
        return session
    
    async def get_session(
        self,
        session_id: str,
        include_messages: bool = True,
    ) -> Session | None:
        """
        Get a session by ID.
        
        Args:
            session_id: Session identifier
            include_messages: Whether to eager-load messages
        
        Returns:
            Session instance or None if not found
        """
        query = select(Session).where(Session.id == session_id)
        
        if include_messages:
            query = query.options(selectinload(Session.messages))
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def list_sessions(
        self,
        include_archived: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Session]:
        """
        List all sessions, optionally including archived ones.
        
        Args:
            include_archived: Include archived sessions in results
            limit: Maximum number of results
            offset: Number of results to skip (for pagination)
        
        Returns:
            List of Session instances ordered by created_at DESC
        """
        query = select(Session).order_by(Session.created_at.desc())
        
        if not include_archived:
            query = query.where(Session.status != SessionStatus.ARCHIVED)
        
        query = query.limit(limit).offset(offset)
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_session_status(
        self,
        session_id: str,
        status: SessionStatus,
    ) -> bool:
        """
        Update a session's status.
        
        Args:
            session_id: Session to update
            status: New status value
        
        Returns:
            True if session was found and updated, False otherwise
        """
        result = await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(status=status, updated_at=datetime.utcnow())
        )
        return result.rowcount > 0
    
    async def delete_session(self, session_id: str) -> bool:
        """
        Soft-delete a session by archiving it.
        
        Args:
            session_id: Session to archive
        
        Returns:
            True if session was found and archived
        """
        return await self.update_session_status(session_id, SessionStatus.ARCHIVED)
    
    # =========================================================================
    # Message Operations
    # =========================================================================
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: dict[str, Any] | list[Any],
        tool_use_id: str | None = None,
    ) -> Message:
        """
        Add a message to a session.
        
        Args:
            session_id: Parent session ID
            role: Message role (user, assistant, tool)
            content: Message content (JSON-serializable)
            tool_use_id: For tool results, the associated tool_use ID
        
        Returns:
            Newly created Message instance
        """
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            tool_use_id=tool_use_id,
        )
        
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        
        # Update session's updated_at timestamp
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(updated_at=datetime.utcnow())
        )
        
        return message
    
    async def get_session_messages(
        self,
        session_id: str,
        limit: int | None = None,
    ) -> Sequence[Message]:
        """
        Get all messages for a session.
        
        Args:
            session_id: Session to get messages for
            limit: Optional limit on number of messages (most recent)
        
        Returns:
            List of Message instances ordered by created_at ASC
        """
        query = (
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.created_at.asc())
        )
        
        if limit:
            # Get most recent N messages
            query = (
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
            )
            result = await self.db.execute(query)
            messages = list(result.scalars().all())
            return list(reversed(messages))  # Restore chronological order
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_messages_as_anthropic_format(
        self,
        session_id: str,
    ) -> list[dict[str, Any]]:
        """
        Get session messages formatted for Anthropic API.
        
        Returns messages in the format expected by sampling_loop.
        
        Args:
            session_id: Session to get messages for
        
        Returns:
            List of message dicts compatible with BetaMessageParam
        """
        messages = await self.get_session_messages(session_id)
        return [msg.to_anthropic_format() for msg in messages]
    
    async def bulk_add_messages(
        self,
        session_id: str,
        messages: list[dict[str, Any]],
    ) -> list[Message]:
        """
        Add multiple messages to a session in a single transaction.
        
        Useful for restoring session history or bulk imports.
        
        Args:
            session_id: Parent session ID
            messages: List of message dicts with role, content, optional tool_use_id
        
        Returns:
            List of created Message instances
        """
        created = []
        for msg_data in messages:
            message = Message(
                session_id=session_id,
                role=msg_data["role"],
                content=msg_data["content"],
                tool_use_id=msg_data.get("tool_use_id"),
            )
            self.db.add(message)
            created.append(message)
        
        await self.db.flush()
        
        # Update session timestamp once
        await self.db.execute(
            update(Session)
            .where(Session.id == session_id)
            .values(updated_at=datetime.utcnow())
        )
        
        return created

