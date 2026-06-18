"""
Retrieval Service — Find relevant document chunks for a query.

This is the "R" in RAG (Retrieval-Augmented Generation).

WHAT IT DOES:
1. Takes the user's question
2. Converts it to an embedding vector
3. Searches ChromaDB for the most similar chunks
4. Returns the chunks with their source metadata
"""

import logging

from app.services.embedding_service import embed_single
from app.services.vectorstore_service import query_similar

logger = logging.getLogger(__name__)

# Default number of chunks to retrieve
DEFAULT_TOP_K = 5

# Minimum similarity score to consider a chunk relevant
MIN_RELEVANCE_SCORE = 0.20


def retrieve_relevant_chunks(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    session_id: str = None
) -> list[dict]:
    """
    Retrieve document chunks relevant to a user query, scoped by session.
    """
    logger.info(f"Retrieving chunks for: '{query[:80]}...' (Session: {session_id})")
    
    # Step 1: Embed the query
    try:
        query_embedding = embed_single(query)
    except Exception as e:
        logger.error(f"Failed to embed query: {e}")
        return []
    
    # Step 2: Search vector store (scope by session_id if provided)
    results = query_similar(
        query_embedding=query_embedding,
        top_k=top_k,
        filter_metadata={"session_id": session_id} if session_id else None
    )
    
    # Step 3: Filter by minimum relevance
    relevant = [r for r in results if r["score"] >= MIN_RELEVANCE_SCORE]
    
    filtered_count = len(results) - len(relevant)
    if filtered_count > 0:
        logger.info(f"Filtered out {filtered_count} low-relevance chunks (< {MIN_RELEVANCE_SCORE})")
    
    logger.info(f"Retrieved {len(relevant)} relevant chunks "
                f"(scores: {[r['score'] for r in relevant]})")
    
    return relevant
