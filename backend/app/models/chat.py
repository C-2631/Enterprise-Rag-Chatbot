"""
Chat database models — Chat sessions and messages.

A ChatSession groups messages together (like a conversation thread).
Each ChatMessage belongs to one session.

STRUCTURE:
  ChatSession (1) ──── (many) ChatMessage
  "Monday Q&A"    ←→   User: "What is revenue?"
                        Bot:  "Based on the document..."
                        User: "Tell me more"
                        Bot:  "The revenue breakdown..."
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ChatSession(Base):
    """
    A conversation session (thread).
    
    Each session has a title and contains multiple messages.
    """
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Display title (auto-generated from first question)
    title: Mapped[str] = mapped_column(String(255), default="New Chat")
    
    # How many messages in this session
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "message_count": self.message_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ChatMessage(Base):
    """
    A single message in a chat session.
    
    role: "user" or "assistant"
    content: The message text
    sources: JSON string of cited sources (for assistant messages)
    """
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    
    # Which session this message belongs to
    session_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # "user" or "assistant"
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # The actual message text
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # JSON string of sources/citations (for bot messages)
    sources: Mapped[str] = mapped_column(Text, nullable=True, default=None)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "sources": self.sources,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
