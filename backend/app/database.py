"""
Database connection and session management.

We use SQLAlchemy with async SQLite:
- SQLAlchemy = ORM (Object-Relational Mapper)
  → Lets you interact with the database using Python classes
  → Instead of: "INSERT INTO documents (name, ...) VALUES (...)"
  → You write:  db.add(Document(name="...", ...))

- Async = Non-blocking
  → While one request waits for the database, FastAPI can handle other requests
  → Essential for a responsive API

- SQLite = File-based database
  → No separate server needed — the database IS a file (rag_chatbot.db)
  → Perfect for development and small-to-medium projects
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

import os
# Get the absolute path to the backend/rag_chatbot.db file
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "rag_chatbot.db")
DATABASE_URL = f"sqlite+aiosqlite:///{db_path}"

# ── Engine ───────────────────────────────────────────
# The engine manages the actual database connection
# echo=False → don't print SQL queries to console (set True for debugging)
engine = create_async_engine(
    DATABASE_URL,
    echo=False
)

# ── Session Factory ──────────────────────────────────
# A session is a "conversation" with the database
# Each API request gets its own session (isolated transactions)
# expire_on_commit=False → objects stay usable after commit
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# ── Base Class ───────────────────────────────────────
# All our database models inherit from this
# It provides the table creation machinery
class Base(DeclarativeBase):
    pass


# ── Dependency: Get Database Session ─────────────────
async def get_db() -> AsyncSession:
    """
    FastAPI dependency that provides a database session.
    
    Usage in endpoints:
        @router.get("/something")
        async def my_endpoint(db: AsyncSession = Depends(get_db)):
            # use db here
    
    The 'async with' ensures the session is properly closed
    even if an error occurs (like a try/finally).
    """
    async with async_session() as session:
        try:
            yield session       # Give the session to the endpoint
            await session.commit()   # If no errors, save changes
        except Exception:
            await session.rollback()  # If error, undo all changes
            raise                     # Re-raise the error


# ── Initialize Database ─────────────────────────────
async def init_db():
    """
    Create all tables defined by our models.
    
    This runs once at app startup.
    'create_all' only creates tables that don't exist yet,
    so it's safe to call repeatedly.
    """
    import logging
    db_logger = logging.getLogger("app.database")
    
    async with engine.begin() as conn:
        # Import models here so SQLAlchemy knows about them
        from app.models.document import Document  # noqa: F401
        from app.models.chat import ChatSession, ChatMessage  # noqa: F401
        
        # Create tables (if they don't exist)
        await conn.run_sync(Base.metadata.create_all)
        
        # Self-healing migration check to add session_id if missing
        try:
            from sqlalchemy import text
            cursor = await conn.execute(text("PRAGMA table_info(documents)"))
            columns = cursor.fetchall()
            if columns:
                has_session_id = any(col[1] == "session_id" for col in columns)
                if not has_session_id:
                    await conn.execute(text("ALTER TABLE documents ADD COLUMN session_id VARCHAR(36)"))
                    db_logger.info("Migrated SQLite: added session_id to documents table.")
        except Exception as ex:
            db_logger.warning(f"Database migration check skipped: {ex}")