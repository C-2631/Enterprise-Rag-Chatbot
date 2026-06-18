"""
Search Router — Test endpoint for semantic search.

This lets you verify that:
1. Embeddings are being created correctly
2. ChromaDB is storing and retrieving properly
3. Semantic search actually finds relevant chunks

This endpoint will evolve into the full RAG query in Phase 4.
For now, it's a simple "search and return chunks" test.
"""

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.embedding_service import embed_single
from app.services.vectorstore_service import query_similar, get_collection_stats

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Search"])


# ── Request/Response Models ──────────────────────────
# Pydantic models define the shape of request bodies
# FastAPI uses these for validation AND auto-generated docs

class SearchRequest(BaseModel):
    """What the client sends to search."""
    query: str = Field(
        ...,                    # ... means required
        min_length=1,           # Can't be empty
        max_length=1000,        # Reasonable limit
        description="The search query in natural language"
    )
    top_k: int = Field(
        default=5,
        ge=1,                   # ge = greater than or equal to
        le=20,                  # le = less than or equal to
        description="Number of results to return (1-20)"
    )


@router.post("/search")
async def search_documents(request: SearchRequest):
    """
    Search for relevant document chunks using semantic similarity.
    
    How it works:
    1. Embed the query using Gemini (task_type="retrieval_query")
    2. Find the closest chunks in ChromaDB
    3. Return chunks with similarity scores
    
    The scores indicate relevance:
    - > 0.7: High relevance (very likely contains the answer)
    - 0.4 - 0.7: Medium relevance (might be helpful)
    - < 0.4: Low relevance (probably not useful)
    """
    try:
        # Step 1: Embed the query
        logger.info(f"Search query: '{request.query[:50]}...'")
        query_embedding = embed_single(request.query)
        
        # Step 2: Find similar chunks
        results = query_similar(
            query_embedding=query_embedding,
            top_k=request.top_k
        )
        
        # Step 3: Format and return
        return {
            "query": request.query,
            "results": results,
            "total_results": len(results)
        }
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/search/stats")
async def vector_store_stats():
    """
    Get vector store statistics.
    
    Useful for checking:
    - Is ChromaDB connected?
    - How many chunks are indexed?
    """
    stats = get_collection_stats()
    return {"vector_store": stats}