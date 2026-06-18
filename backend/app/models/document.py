"""
Document database model.

This defines the 'documents' table in SQLite.
Each row represents one uploaded document with its metadata.

WHAT IS AN ORM MODEL?
- Instead of writing: CREATE TABLE documents (id INTEGER PRIMARY KEY, ...)
- You write a Python class, and SQLAlchemy creates the table for you
- Each instance of the class = one row in the table
- Each class attribute = one column in the table
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, Text, Float
from sqlalchemy.orm import Mapped, mapped_column

# Import Base from our database module
from app.database import Base


class Document(Base):
    """
    Represents an uploaded document in the database.
    
    Table name: 'documents'
    
    Columns:
    - id: Unique identifier (UUID string)
    - filename: Original name of the uploaded file
    - file_type: Extension (pdf, docx, txt, md)
    - file_size: Size in bytes
    - content: Full extracted text from the document
    - chunk_count: Number of chunks created from this document
    - status: Processing state (uploaded, processing, completed, failed)
    - error_message: Error details if processing failed
    - created_at: When the document was uploaded
    - updated_at: When the document was last modified
    """

    # This sets the actual table name in SQLite
    __tablename__ = "documents"

    # ── Columns ──────────────────────────────────────
    # Mapped[type] tells SQLAlchemy the Python type
    # mapped_column() defines the SQL column properties

    # Primary key — unique ID for each document
    # We use UUID strings instead of auto-increment integers
    # Why? UUIDs are globally unique and don't reveal how many documents exist
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())  # Auto-generate UUID
    )

    # Original filename (e.g., "annual_report.pdf")
    filename: Mapped[str] = mapped_column(String(255), nullable=False)

    # File extension without dot (e.g., "pdf", "docx", "txt", "md")
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)

    # File size in bytes (e.g., 1048576 for 1MB)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)

    # Full extracted text content from the document
    # Text type = unlimited length (unlike String which has a max)
    content: Mapped[str] = mapped_column(Text, default="")

    # How many chunks this document was split into
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)

    # Processing status: uploaded → processing → completed/failed
    status: Mapped[str] = mapped_column(String(20), default="uploaded")

    # Associated chat session ID (documents are scoped per chat thread)
    session_id: Mapped[str] = mapped_column(String(36), nullable=True, default=None)

    # If processing failed, store the error message
    error_message: Mapped[str] = mapped_column(Text, nullable=True, default=None)

    # Timestamps — when was this document created and last updated
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)  # Auto-update on changes
    )

    def to_dict(self) -> dict:
        """
        Convert this document to a dictionary for API responses.
        
        Why a method instead of returning the object directly?
        - FastAPI can't serialize SQLAlchemy objects automatically
        - We control exactly what fields are in the response
        - We can format values (e.g., datetime → ISO string)
        """
        return {
            "id": self.id,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "chunk_count": self.chunk_count,
            "status": self.status,
            "session_id": self.session_id,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        """String representation for debugging (shows in print/logs)."""
        return f"<Document(id={self.id[:8]}..., filename={self.filename}, status={self.status})>"