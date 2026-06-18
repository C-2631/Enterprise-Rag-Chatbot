"""
Text Chunking Service.

WHY CHUNKING?
LLMs have a context window limit, and embeddings work best on focused passages.
A 50-page PDF can't be fed to the model as-is. We split it into smaller,
overlapping chunks that each contain a coherent piece of information.

CHUNK SIZE & OVERLAP:
- chunk_size=800: Each chunk is ~800 characters (~200 words)
  → Small enough for focused embedding
  → Large enough to contain a complete thought
  
- chunk_overlap=200: Adjacent chunks share 200 characters
  → Prevents cutting information in the middle of a sentence
  → If a fact spans two chunks, the overlap preserves it in at least one chunk

Example: Text = "AAABBBCCDDDEEE" with size=6, overlap=2
  Chunk 1: "AAABBB"
  Chunk 2: "BBCCDD"   (overlaps "BB" with chunk 1)
  Chunk 3: "DDDEEE"   (overlaps "DD" with chunk 2)
"""

import logging

from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

# ── Chunking Configuration ───────────────────────────
CHUNK_SIZE = 800        # Characters per chunk
CHUNK_OVERLAP = 200     # Overlap between adjacent chunks

# The separators define WHERE the splitter prefers to cut.
# It tries the first separator, then falls back to the next:
SEPARATORS = [
    "\n\n",    # 1st priority: Split at paragraph breaks (best — preserves paragraphs)
    "\n",      # 2nd priority: Split at line breaks
    ". ",      # 3rd priority: Split at sentence endings
    "? ",      # 4th priority: Split at questions
    "! ",      # 5th priority: Split at exclamations
    ", ",      # 6th priority: Split at commas (less ideal)
    " ",       # Last resort: Split at any space
]


def chunk_text(text: str, filename: str = "") -> list[dict]:
    """
    Split text into overlapping chunks with metadata.
    
    Args:
        text: The full text content to split
        filename: Source filename (stored as metadata on each chunk)
    
    Returns:
        List of dictionaries, each containing:
        - 'text': The chunk content
        - 'metadata': Source info (filename, chunk index, char positions)
    
    Example return:
        [
            {
                "text": "Chapter 1: Introduction...",
                "metadata": {
                    "source": "report.pdf",
                    "chunk_index": 0,
                    "start_char": 0,
                    "end_char": 800
                }
            },
            ...
        ]
    """
    
    if not text or not text.strip():
        logger.warning(f"Empty text provided for chunking: {filename}")
        return []
    
    # Create the text splitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,           # Use character count for length
        separators=SEPARATORS,
        is_separator_regex=False,      # Separators are literal strings, not regex
    )
    
    # Split the text into chunks
    # create_documents() returns LangChain Document objects
    chunks = splitter.create_documents(
        texts=[text],
        metadatas=[{"source": filename}]  # Metadata applied to all chunks
    )
    
    # Convert LangChain Documents to our own format (plain dicts)
    result = []
    for i, chunk in enumerate(chunks):
        result.append({
            "text": chunk.page_content,
            "metadata": {
                "source": filename,
                "chunk_index": i,
                "total_chunks": len(chunks),
                "char_count": len(chunk.page_content),
            }
        })
    
    logger.info(f"Split '{filename}' into {len(result)} chunks "
                f"(avg {sum(len(c['text']) for c in result) // max(len(result), 1)} chars/chunk)")
    
    return result