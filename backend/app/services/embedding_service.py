"""
Embedding Service — Convert text to vector embeddings using Google Gemini.

WHAT ARE EMBEDDINGS?
- An embedding is a list of numbers (a vector) that represents the MEANING of text
- Similar meanings → similar vectors → close in vector space
- Example:
    "king"  → [0.12, 0.85, -0.33, ...]
    "queen" → [0.15, 0.82, -0.30, ...]   ← very close! (similar meaning)
    "car"   → [0.90, -0.10, 0.55, ...]   ← very different (different meaning)

WHY GEMINI EMBEDDINGS?
- Model: "models/embedding-001"
- Output: 768-dimensional vector
- Free tier: 1,500 requests/day (plenty for development)
- Quality: Very good for English text, decent for multilingual

BATCH PROCESSING:
- We embed multiple chunks at once (up to 100 per request)
- This is 10-100x faster than embedding one at a time
- We also add delays between batches to respect rate limits
"""

import time
import logging
from typing import Optional

import google.generativeai as genai

from app.config import get_settings

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────
EMBEDDING_MODEL = "models/gemini-embedding-001"
BATCH_SIZE = 100          # Max texts per API call
RATE_LIMIT_DELAY = 0.5    # Seconds between batches (avoid 429 errors)


def _configure_genai():
    """
    Configure the Google Generative AI SDK with our API key.
    
    Called before every operation to ensure the key is set.
    This is idempotent — calling it multiple times is safe.
    """
    settings = get_settings()
    if not settings.google_api_key:
        raise ValueError(
            "GOOGLE_API_KEY is not set! "
            "Add it to your backend/.env file. "
            "Get a key from: https://aistudio.google.com/apikey"
        )
    genai.configure(api_key=settings.google_api_key)


def embed_single(text: str) -> list[float]:
    """
    Embed a single text string into a vector.
    
    Args:
        text: The text to embed (e.g., a user's query)
    
    Returns:
        A list of 768 floats representing the text's meaning
    
    Used for: Embedding user queries at search time
    """
    _configure_genai()
    
    try:
        result = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=text,
            task_type="retrieval_query",  # Optimized for search queries
            output_dimensionality=768
        )
        
        # result['embedding'] is the vector
        return result['embedding']
    
    except Exception as e:
        logger.error(f"Embedding failed for text: {text[:50]}... Error: {e}")
        raise


def embed_batch(texts: list[str]) -> list[list[float]]:
    """
    Embed multiple texts in batches.
    
    Args:
        texts: List of text strings to embed
    
    Returns:
        List of vectors (one per input text), same order as input
    
    Used for: Embedding document chunks during indexing
    
    TASK TYPE MATTERS:
    - "retrieval_document" → for chunks being stored (what we search THROUGH)
    - "retrieval_query"    → for queries (what we search WITH)
    
    Google optimizes the embeddings differently for each role.
    Documents and queries end up in the same vector space,
    but with slightly different emphasis.
    """
    _configure_genai()
    
    if not texts:
        return []
    
    all_embeddings = []
    total_batches = (len(texts) + BATCH_SIZE - 1) // BATCH_SIZE  # Ceiling division
    
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        
        logger.info(f"Embedding batch {batch_num}/{total_batches} ({len(batch)} texts)")
        
        try:
            result = genai.embed_content(
                model=EMBEDDING_MODEL,
                content=batch,
                task_type="retrieval_document",  # These are documents, not queries
                output_dimensionality=768
            )
            
            # result['embedding'] is a list of vectors when input is a list
            all_embeddings.extend(result['embedding'])
            
        except Exception as e:
            logger.error(f"Batch {batch_num} embedding failed: {e}")
            # For failed batches, add zero vectors as placeholders
            # This prevents the whole pipeline from crashing
            all_embeddings.extend([[0.0] * 768] * len(batch))
        
        # Rate limiting: pause between batches to avoid API throttling
        if i + BATCH_SIZE < len(texts):
            time.sleep(RATE_LIMIT_DELAY)
    
    logger.info(f"Embedded {len(all_embeddings)} texts total")
    return all_embeddings


def get_embedding_dimension() -> int:
    """Return the dimension of embeddings produced by our model."""
    return 768