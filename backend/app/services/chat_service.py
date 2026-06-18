"""
Chat Service — Generate answers using Gemini LLM.

This service:
1. Takes a user question + retrieved context
2. Builds a prompt with system instructions
3. Calls Gemini to generate an answer
4. Streams the response token by token
"""

import json
import logging
from typing import AsyncGenerator

import google.generativeai as genai

from app.config import get_settings
from app.services.retrieval_service import retrieve_relevant_chunks
from app.prompts.system_prompt import build_prompt

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────
CHAT_MODEL = "gemini-2.5-flash"     # Fast and cheap, great for RAG
TEMPERATURE = 0.2                    # Low = factual, high = creative
MAX_OUTPUT_TOKENS = 2048             # Max response length
TOP_K_CHUNKS = 8                     # How many chunks to retrieve

# Simple In-Memory Query Cache to save tokens and speed up repeated queries
# Structure: {(session_id, question): (full_answer, sources)}
QUERY_CACHE = {}


def _configure_genai():
    """Configure Gemini API with our key."""
    settings = get_settings()
    if not settings.google_api_key:
        raise ValueError("GOOGLE_API_KEY is not set in .env!")
    genai.configure(api_key=settings.google_api_key)


def generate_response(
    question: str,
    chat_history: list[dict] = None,
    session_id: str = None
) -> dict:
    """
    Generate a complete (non-streaming) response.
    """
    _configure_genai()
    
    # Step 1: Retrieve relevant chunks
    chunks = retrieve_relevant_chunks(question, top_k=TOP_K_CHUNKS, session_id=session_id)
    
    # Step 2: Build the prompt
    system_prompt = build_prompt(chunks, chat_history)
    
    # Step 3: Create the model
    model = genai.GenerativeModel(
        model_name=CHAT_MODEL,
        generation_config=genai.GenerationConfig(
            temperature=TEMPERATURE,
            max_output_tokens=MAX_OUTPUT_TOKENS,
        )
    )
    
    # Step 4: Generate response
    try:
        chat = model.start_chat(history=[])
        
        # Send system prompt + user question together
        full_prompt = f"{system_prompt}\n\nUser Question: {question}"
        response = chat.send_message(full_prompt)
        
        answer = response.text
        
        # Build sources list from retrieved chunks
        sources = [
            {
                "source": chunk["metadata"].get("source", "Unknown"),
                "chunk_index": chunk["metadata"].get("chunk_index", 0),
                "score": chunk["score"],
                "text": chunk["text"][:200] + "..."  # Preview only
            }
            for chunk in chunks
        ]
        
        return {
            "answer": answer,
            "sources": sources,
            "chunks_used": len(chunks)
        }
    
    except Exception as e:
        logger.error(f"Gemini generation failed: {e}")
        raise


async def generate_stream_response(
    question: str,
    chat_history: list[dict] = None,
    session_id: str = None
) -> AsyncGenerator[str, None]:
    """
    Generate a streaming response using Server-Sent Events format.
    """
    _configure_genai()
    
    # Check cache first
    cache_key = (session_id, question.strip().lower())
    if cache_key in QUERY_CACHE:
        logger.info(f"Cache hit for session {session_id}, bypassing LLM API.")
        cached_answer, cached_sources = QUERY_CACHE[cache_key]
        yield f"data: {json.dumps({'type': 'sources', 'data': cached_sources})}\n\n"
        
        # Simulate a quick stream so the UI still looks alive
        words = cached_answer.split(" ")
        for i, word in enumerate(words):
            suffix = " " if i < len(words) - 1 else ""
            yield f"data: {json.dumps({'type': 'token', 'data': word + suffix})}\n\n"
            
        yield f"data: {json.dumps({'type': 'done', 'data': cached_answer})}\n\n"
        return
    
    try:
        # ── Step 1: Retrieve chunks ──────────────────
        chunks = retrieve_relevant_chunks(question, top_k=TOP_K_CHUNKS, session_id=session_id)
        
        # Send sources as the first event
        sources = [
            {
                "source": chunk["metadata"].get("source", "Unknown"),
                "chunk_index": chunk["metadata"].get("chunk_index", 0),
                "score": chunk["score"],
                "text": chunk["text"][:200] + "..."
            }
            for chunk in chunks
        ]
        
        # Yield a "sources" event
        yield f"data: {json.dumps({'type': 'sources', 'data': sources})}\n\n"
        
        # ── Step 2: Build prompt ─────────────────────
        system_prompt = build_prompt(chunks, chat_history)
        
        # ── Step 3: Create model and start chat ──────────
        model = genai.GenerativeModel(
            model_name=CHAT_MODEL,
            generation_config=genai.GenerationConfig(
                temperature=TEMPERATURE,
                max_output_tokens=MAX_OUTPUT_TOKENS,
            ),
            system_instruction=system_prompt,
        )
        
        # Start chat with history formatted for the Gemini SDK
        formatted_history = []
        if chat_history:
            for msg in chat_history:
                formatted_history.append({
                    "role": "model" if msg["role"] == "assistant" else "user",
                    "parts": [msg["content"]]
                })
        
        chat = model.start_chat(history=formatted_history)
        
        # Stream the response for the new question
        response = chat.send_message(question, stream=True)
        
        full_answer = ""
        
        for chunk in response:
            if chunk.text:
                full_answer += chunk.text
                # Send each text chunk as a "token" event
                yield f"data: {json.dumps({'type': 'token', 'data': chunk.text})}\n\n"
        
        # ── Step 4: Send completion event ────────────
        yield f"data: {json.dumps({'type': 'done', 'data': full_answer})}\n\n"
        
        # Cache the result for future identical queries
        QUERY_CACHE[cache_key] = (full_answer, sources)
        
        # Simple cache management (keep it under 1000 items)
        if len(QUERY_CACHE) > 1000:
            # Remove the oldest key (first in dict, since Python 3.7+ preserves insertion order)
            QUERY_CACHE.pop(next(iter(QUERY_CACHE)))
            
    except Exception as e:
        logger.error(f"Stream generation failed: {e}")
        yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"
