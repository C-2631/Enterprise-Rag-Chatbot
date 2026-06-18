"""
Document Service — Business logic for document management.

This service handles:
- Saving uploaded files to disk
- Triggering parsing and chunking
- CRUD operations on the documents table

WHY A SERVICE LAYER?
- Routers handle HTTP (request/response) → thin, focused
- Services handle LOGIC (save, parse, chunk) → reusable, testable
- If you later add a CLI or a different API, the service logic stays the same
"""

import os
import logging
import uuid

import aiofiles
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.services.parser_service import parse_document, validate_file, get_file_extension
from app.services.chunking_service import chunk_text
from app.services.indexing_service import index_document, remove_document_from_index

logger = logging.getLogger(__name__)

# Directory where uploaded files are stored
UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads")


async def save_upload_file(file_content: bytes, filename: str) -> str:
    """
    Save uploaded file bytes to disk.
    
    Args:
        file_content: Raw bytes of the uploaded file
        filename: Original filename
    
    Returns:
        Absolute path to the saved file
    
    Why save to disk?
    - We need a file path for the parsers (PyPDF2, python-docx)
    - Keeps the uploaded original for reference
    - Can re-process later if needed
    """
    # Create uploads directory if it doesn't exist
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Generate a unique filename to avoid collisions
    # "report.pdf" → "a1b2c3d4_report.pdf"
    unique_filename = f"{uuid.uuid4().hex[:8]}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Write file to disk asynchronously (non-blocking)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(file_content)
    
    logger.info(f"Saved file: {file_path} ({len(file_content)} bytes)")
    return file_path


async def process_document(
    db: AsyncSession,
    filename: str,
    file_content: bytes,
    file_size: int,
    session_id: str = None
) -> Document:
    """
    Full document processing pipeline with session scoping.
    """
    
    # ── Step 1: Validate ─────────────────────────────
    is_valid, error_msg = validate_file(filename, file_size)
    if not is_valid:
        raise ValueError(error_msg)
    
    file_type = get_file_extension(filename)
    
    # ── Step 2: Create DB record (status: "processing") ─
    doc = Document(
        filename=filename,
        file_type=file_type,
        file_size=file_size,
        session_id=session_id,
        status="processing"
    )
    db.add(doc)
    await db.flush()  # Get the auto-generated ID without committing
    
    try:
        # ── Step 3: Save file to disk ────────────────
        file_path = await save_upload_file(file_content, filename)
        
        # ── Step 4: Parse text ───────────────────────
        logger.info(f"Parsing document: {filename}")
        text_content = parse_document(file_path, filename)
        
        # ── Step 5: Chunk the text ───────────────────
        logger.info(f"Chunking document: {filename}")
        chunks = chunk_text(text_content, filename)
        
        # ── Step 6: Index chunks (embed + store in ChromaDB with session ID) ──
        logger.info(f"Indexing document: {filename} for Session: {session_id}")
        num_indexed = index_document(doc.id, text_content, filename, session_id=session_id)
        
        # ── Step 7: Update DB with results ───────────
        doc.content = text_content
        doc.chunk_count = num_indexed  # Use actual indexed count
        doc.status = "completed"
        
        logger.info(f"Document processed: {filename} → {len(chunks)} chunks")
        
    except Exception as e:
        # If ANYTHING fails, mark the document as failed
        doc.status = "failed"
        doc.error_message = str(e)
        logger.error(f"Failed to process {filename}: {e}")
    
    return doc


async def get_all_documents(db: AsyncSession, session_id: str = None) -> list[dict]:
    """
    Get documents from the database, optionally filtered by session_id.
    """
    query = select(Document)
    if session_id:
        query = query.where(Document.session_id == session_id)
    query = query.order_by(Document.created_at.desc())
    
    result = await db.execute(query)
    documents = result.scalars().all()
    return [doc.to_dict() for doc in documents]


async def get_document_by_id(db: AsyncSession, document_id: str) -> Document | None:
    """
    Get a single document by its ID.
    
    Returns None if not found.
    """
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    return result.scalar_one_or_none()


async def delete_document(db: AsyncSession, document_id: str) -> bool:
    """
    Delete a document from the database and its uploaded file.
    
    Returns True if deleted, False if not found.
    """
    # Find the document first
    doc = await get_document_by_id(db, document_id)
    if not doc:
        return False
    
    # Try to delete the uploaded file from disk
    # We look for files containing the original filename
    try:
        for f in os.listdir(UPLOAD_DIR):
            if doc.filename in f:
                os.remove(os.path.join(UPLOAD_DIR, f))
                logger.info(f"Deleted file: {f}")
                break
    except (OSError, FileNotFoundError) as e:
        logger.warning(f"Could not delete file for {doc.filename}: {e}")
    
    # Delete from database
    remove_document_from_index(doc.filename)
    await db.execute(
        delete(Document).where(Document.id == document_id)
    )
    
    logger.info(f"Deleted document: {doc.filename} (ID: {document_id})")
    return True