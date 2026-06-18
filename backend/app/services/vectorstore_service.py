"""
Vector Store Service — ChromaDB operations.

WHAT IS A VECTOR DATABASE?
- A specialized database for storing and searching vectors (embeddings)
- Traditional DB: "Find rows WHERE name = 'John'"
- Vector DB: "Find vectors CLOSEST to this query vector"

WHAT IS ChromaDB?
- Open-source, lightweight vector database
- Stores vectors + metadata + original text
- Uses HNSW algorithm for fast nearest-neighbor search
- Persists data to disk (survives server restarts)

WHAT IS COSINE SIMILARITY?
- Measures the angle between two vectors
- 1.0 = identical direction (same meaning)
- 0.0 = perpendicular (unrelated)
- -1.0 = opposite direction (opposite meaning)

HOW SEARCH WORKS:
1. User query: "What is the revenue?"
2. Embed query → query_vector = [0.12, 0.45, ...]
3. ChromaDB finds the K vectors closest to query_vector
4. Returns the corresponding text chunks + similarity scores
"""

import os
import logging

import chromadb
from chromadb.config import Settings as ChromaSettings

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────
# Where ChromaDB stores its data on disk
VECTORSTORE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "vectorstore"
)

# Collection name — like a "table" in ChromaDB
COLLECTION_NAME = "document_chunks"

# Default number of results to return
DEFAULT_TOP_K = 5


def _get_client() -> chromadb.PersistentClient:
    """
    Get a ChromaDB client with persistent storage.
    
    PersistentClient vs Client:
    - Client: in-memory only, data lost on restart
    - PersistentClient: saves to disk, survives restarts
    
    The data is stored in the vectorstore/ directory.
    """
    os.makedirs(VECTORSTORE_DIR, exist_ok=True)
    
    client = chromadb.PersistentClient(
        path=VECTORSTORE_DIR,
        settings=ChromaSettings(
            anonymized_telemetry=False  # Don't send usage data to ChromaDB
        )
    )
    return client


def _get_collection(client: chromadb.PersistentClient):
    """
    Get or create the document chunks collection.
    
    get_or_create_collection:
    - If collection exists → returns it
    - If not → creates it
    
    cosine = use cosine similarity for distance measurement
    """
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}  # Use cosine distance
    )
    return collection


def add_chunks(
    chunk_ids: list[str],
    embeddings: list[list[float]],
    texts: list[str],
    metadatas: list[dict]
) -> int:
    """
    Add embedded chunks to the vector store.
    
    Args:
        chunk_ids:  Unique ID for each chunk (e.g., "doc123_chunk_0")
        embeddings: The vector for each chunk (from embedding service)
        texts:      The original text of each chunk (stored for retrieval)
        metadatas:  Metadata for each chunk (source, chunk_index, etc.)
    
    Returns:
        Number of chunks added
    
    IMPORTANT: All four lists must be the same length!
    chunk_ids[0] corresponds to embeddings[0], texts[0], metadatas[0]
    """
    if not chunk_ids:
        return 0
    
    client = _get_client()
    collection = _get_collection(client)
    
    # ChromaDB's add() method stores everything together
    # Each chunk gets: an ID, a vector, the original text, and metadata
    try:
        collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metadatas
        )
        
        logger.info(f"Added {len(chunk_ids)} chunks to vector store. "
                    f"Total in collection: {collection.count()}")
        
        return len(chunk_ids)
    
    except Exception as e:
        logger.error(f"Failed to add chunks to vector store: {e}")
        raise


def query_similar(
    query_embedding: list[float],
    top_k: int = DEFAULT_TOP_K,
    filter_metadata: dict = None
) -> list[dict]:
    """
    Find the most similar chunks to a query embedding.
    
    Args:
        query_embedding: The vector of the user's query
        top_k: How many results to return (default: 5)
        filter_metadata: Optional filter (e.g., {"source": "report.pdf"})
    
    Returns:
        List of result dicts, each containing:
        - 'text': The chunk's original text
        - 'metadata': Source info (filename, chunk_index, etc.)
        - 'score': Similarity score (0 to 1, higher = more similar)
        - 'id': The chunk's unique ID
    
    HOW SCORING WORKS:
    ChromaDB returns 'distances' (lower = more similar for cosine).
    We convert to 'similarity scores' (higher = more similar) with:
        score = 1 - distance
    So: distance=0.1 → score=0.9 (very similar)
        distance=0.9 → score=0.1 (not similar)
    """
    client = _get_client()
    collection = _get_collection(client)
    
    # Check if the collection has any data
    if collection.count() == 0:
        logger.warning("Vector store is empty — no documents indexed yet")
        return []
    
    # Build query parameters
    query_params = {
        "query_embeddings": [query_embedding],
        "n_results": min(top_k, collection.count()),  # Can't request more than exists
        "include": ["documents", "metadatas", "distances"]
    }
    
    # Add metadata filter if provided
    if filter_metadata:
        query_params["where"] = filter_metadata
    
    try:
        results = collection.query(**query_params)
        
        # Parse ChromaDB results into a cleaner format
        parsed_results = []
        
        if results and results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                # Convert distance to similarity score
                distance = results['distances'][0][i]
                similarity_score = 1 - distance  # Cosine: 1 - distance = similarity
                
                parsed_results.append({
                    "id": results['ids'][0][i],
                    "text": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "score": round(similarity_score, 4)
                })
        
        logger.info(f"Query returned {len(parsed_results)} results "
                    f"(top score: {parsed_results[0]['score'] if parsed_results else 'N/A'})")
        
        return parsed_results
    
    except Exception as e:
        logger.error(f"Vector store query failed: {e}")
        return []


def delete_document_chunks(document_source: str) -> int:
    """
    Delete all chunks belonging to a specific document.
    
    Args:
        document_source: The filename/source to delete (matches metadata.source)
    
    Returns:
        Number of chunks that were in the store (approximate)
    
    Used when: User deletes a document → remove its chunks from vector store too
    """
    client = _get_client()
    collection = _get_collection(client)
    
    # Count before deletion (for logging)
    count_before = collection.count()
    
    try:
        # Delete all chunks where metadata.source matches the filename
        collection.delete(
            where={"source": document_source}
        )
        
        count_after = collection.count()
        deleted_count = count_before - count_after
        
        logger.info(f"Deleted {deleted_count} chunks for document: {document_source}")
        return deleted_count
    
    except Exception as e:
        logger.error(f"Failed to delete chunks for {document_source}: {e}")
        return 0


def delete_session_chunks(session_id: str) -> int:
    """
    Delete all chunks belonging to a specific session.
    """
    client = _get_client()
    collection = _get_collection(client)
    
    count_before = collection.count()
    
    try:
        collection.delete(
            where={"session_id": session_id}
        )
        
        count_after = collection.count()
        deleted_count = count_before - count_after
        
        logger.info(f"Deleted {deleted_count} chunks for session: {session_id}")
        return deleted_count
    
    except Exception as e:
        logger.error(f"Failed to delete chunks for session {session_id}: {e}")
        return 0


def get_collection_stats() -> dict:
    """
    Get statistics about the vector store.
    
    Returns info for the health check endpoint.
    """
    try:
        client = _get_client()
        collection = _get_collection(client)
        
        return {
            "status": "connected",
            "total_chunks": collection.count(),
            "collection_name": COLLECTION_NAME,
            "storage_path": VECTORSTORE_DIR
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }