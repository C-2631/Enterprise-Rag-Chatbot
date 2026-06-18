"""
Indexing Service — Connects document processing to vector storage.

THE INDEXING PIPELINE:
1. Take text chunks (from chunking_service)
2. Embed each chunk (using embedding_service)
3. Store embeddings in ChromaDB (using vectorstore_service)

This is the bridge between Phase 2 (documents) and Phase 3 (vectors).

WHY A SEPARATE SERVICE?
- document_service handles file management
- embedding_service handles the Gemini API
- vectorstore_service handles ChromaDB
- indexing_service ORCHESTRATES them all
"""

import logging
from app.services.embedding_service import embed_batch
from app.services.vectorstore_service import add_chunks, delete_document_chunks, delete_session_chunks
from app.services.chunking_service import chunk_text

logger = logging.getLogger(__name__)


def index_document(document_id: str, text_content: str, filename: str, session_id: str = None) -> int:
    """
    Full indexing pipeline for a document with optional session scoping.
    """
    logger.info(f"Starting indexing for: {filename} (ID: {document_id[:8]}...) for Session: {session_id}")
    
    # ── Step 1: Chunk the text ───────────────────────
    chunks = chunk_text(text_content, filename)
    
    if not chunks:
        logger.warning(f"No chunks produced for {filename}")
        return 0
    
    logger.info(f"Step 1/3: Created {len(chunks)} chunks")
    
    # ── Step 2: Embed all chunks ─────────────────────
    # Extract just the text from each chunk dict
    chunk_texts = [chunk["text"] for chunk in chunks]
    
    embeddings = embed_batch(chunk_texts)
    
    logger.info(f"Step 2/3: Generated {len(embeddings)} embeddings")
    
    # ── Step 3: Store in ChromaDB ────────────────────
    # Generate unique IDs for each chunk
    chunk_ids = [
        f"{document_id}_chunk_{i}" 
        for i in range(len(chunks))
    ]
    
    # Prepare metadata for each chunk
    metadatas = [
        {
            "source": filename,
            "document_id": document_id,
            "session_id": session_id or "",
            "chunk_index": chunk["metadata"]["chunk_index"],
            "total_chunks": chunk["metadata"]["total_chunks"],
            "char_count": chunk["metadata"]["char_count"],
        }
        for chunk in chunks
    ]
    
    # Add to vector store
    num_stored = add_chunks(
        chunk_ids=chunk_ids,
        embeddings=embeddings,
        texts=chunk_texts,
        metadatas=metadatas
    )
    
    logger.info(f"Step 3/3: Stored {num_stored} chunks in vector store")
    logger.info(f"Indexing complete for: {filename}")
    
    return num_stored


def remove_document_from_index(filename: str) -> int:
    """
    Remove all indexed chunks for a document.
    
    Called when a user deletes a document — we need to
    remove its chunks from the vector store too.
    """
    logger.info(f"Removing from index: {filename}")
    deleted = delete_document_chunks(filename)
    logger.info(f"Removed {deleted} chunks for: {filename}")
    return deleted


def remove_session_from_index(session_id: str) -> int:
    """
    Remove all indexed chunks for a session.
    """
    logger.info(f"Removing session from index: {session_id}")
    deleted = delete_session_chunks(session_id)
    logger.info(f"Removed {deleted} chunks for session: {session_id}")
    return deleted