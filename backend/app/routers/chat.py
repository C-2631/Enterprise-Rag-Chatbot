"""
Chat Router — Endpoints for the chat interface.

Endpoints:
- POST /api/v1/chat          → Non-streaming chat (returns full response)
- POST /api/v1/chat/stream   → Streaming chat (returns SSE stream)
- GET  /api/v1/chat/sessions → List chat sessions
"""

import json
import logging

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database import get_db, async_session
from app.models.chat import ChatSession, ChatMessage
from app.models.document import Document
from app.services.chat_service import generate_response, generate_stream_response
from app.services import document_service
from app.services.indexing_service import remove_session_from_index

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Chat"])


# ── Request Models ───────────────────────────────────

class ChatRequest(BaseModel):
    """What the client sends to chat."""
    question: str = Field(
        ..., min_length=1, max_length=5000,
        description="The user's question"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Chat session ID (optional — creates new session if not provided)"
    )


# ── Non-Streaming Chat ──────────────────────────────

@router.post("/chat")
async def chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message and get a complete response.
    
    Good for: API clients, testing, simple integrations
    Bad for: User-facing chat (no typing effect)
    """
    try:
        # Get or create session
        session = None
        chat_history = []
        
        if request.session_id:
            result = await db.execute(
                select(ChatSession).where(ChatSession.id == request.session_id)
            )
            session = result.scalar_one_or_none()
        
        if not session:
            session = ChatSession(
                title=request.question[:50] + ("..." if len(request.question) > 50 else "")
            )
            db.add(session)
            await db.flush()
        
        # Load chat history for this session
        if session:
            result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == session.id)
                .order_by(ChatMessage.created_at)
            )
            messages = result.scalars().all()
            chat_history = [{"role": m.role, "content": m.content} for m in messages]
        
        # Check if this session has any documents uploaded
        doc_check = await db.execute(
            select(Document).where(Document.session_id == session.id)
        )
        session_docs = doc_check.scalars().all()
        
        if not session_docs:
            response_data = {
                "answer": "No documents have been uploaded for this chat session. Please upload a document (PDF, DOCX, TXT, or MD) using the clip button below to begin.",
                "sources": [],
                "chunks_used": 0
            }
        else:
            # Generate response
            response_data = generate_response(
                question=request.question,
                chat_history=chat_history,
                session_id=session.id
            )
        
        # Save user message
        user_msg = ChatMessage(
            session_id=session.id,
            role="user",
            content=request.question
        )
        db.add(user_msg)
        
        # Save assistant message
        bot_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=response_data["answer"],
            sources=json.dumps(response_data["sources"])
        )
        db.add(bot_msg)
        
        # Update session
        session.message_count = len(chat_history) + 2
        
        return {
            "answer": response_data["answer"],
            "sources": response_data["sources"],
            "session_id": session.id,
            "chunks_used": response_data["chunks_used"]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Streaming Chat ───────────────────────────────────

@router.post("/chat/stream")
async def chat_stream(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message and get a streaming response via SSE.
    
    The response is a stream of events:
    1. {type: "sources", data: [...]}   → Retrieved document chunks
    2. {type: "token", data: "word"}    → Each token as it's generated
    3. {type: "done", data: "full text"} → Complete response
    """
    try:
        # Log the raw request body
        body = await request.body()
        logger.info(f"Received stream request body: {body.decode()}")

        # Manually parse and validate
        try:
            data = json.loads(body)
            chat_request = ChatRequest(**data)
        except (json.JSONDecodeError, ValidationError) as e:
            logger.error(f"Invalid request data: {e}")
            raise HTTPException(status_code=422, detail=f"Invalid request data: {e}")

        # Load chat history
        chat_history = []
        session = None
        
        if chat_request.session_id:
            result = await db.execute(
                select(ChatSession).where(ChatSession.id == chat_request.session_id)
            )
            session = result.scalar_one_or_none()
        
        if not session:
            session = ChatSession(
                title=chat_request.question[:50] + ("..." if len(chat_request.question) > 50 else "")
            )
            db.add(session)
            await db.flush()
        
        if session:
            result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == session.id)
                .order_by(ChatMessage.created_at)
            )
            messages = result.scalars().all()
            chat_history = [{"role": m.role, "content": m.content} for m in messages]
        
        # Save user message immediately
        user_msg = ChatMessage(
            session_id=session.id,
            role="user",
            content=chat_request.question
        )
        db.add(user_msg)
        await db.flush()
        
        # Store session_id to send with stream
        session_id = session.id
        
        # Create the streaming generator
        async def event_generator():
            # First, send the session ID
            yield f"data: {json.dumps({'type': 'session', 'data': session_id})}\n\n"
            
            full_answer = ""
            sources = []
            
            # Check if this session has any documents uploaded
            async with async_session() as check_db:
                doc_check = await check_db.execute(
                    select(Document).where(Document.session_id == session_id)
                )
                session_docs = doc_check.scalars().all()
            
            try:
                if not session_docs:
                    warning_text = "No documents have been uploaded for this chat session. Please upload a document (PDF, DOCX, TXT, or MD) using the clip button below to begin."
                    full_answer = warning_text
                    yield f"data: {json.dumps({'type': 'sources', 'data': []})}\n\n"
                    yield f"data: {json.dumps({'type': 'token', 'data': warning_text})}\n\n"
                    yield f"data: {json.dumps({'type': 'done', 'data': warning_text})}\n\n"
                else:
                    # Then stream the LLM response
                    async for event in generate_stream_response(
                        question=chat_request.question,
                        chat_history=chat_history,
                        session_id=session_id
                    ):
                        if event.startswith("data: "):
                            try:
                                event_data = json.loads(event[6:].strip())
                                if event_data["type"] == "token":
                                    full_answer += event_data["data"]
                                elif event_data["type"] == "sources":
                                    sources = event_data["data"]
                            except Exception:
                                pass
                        yield event
            finally:
                # Save assistant message to database when stream finishes or is interrupted
                if full_answer:
                    try:
                        async with async_session() as local_db:
                            async with local_db.begin():
                                bot_msg = ChatMessage(
                                    session_id=session_id,
                                    role="assistant",
                                    content=full_answer,
                                    sources=json.dumps(sources) if sources else None
                                )
                                local_db.add(bot_msg)
                                
                                # Update session message count
                                result = await local_db.execute(
                                    select(ChatSession).where(ChatSession.id == session_id)
                                )
                                local_session = result.scalar_one_or_none()
                                if local_session:
                                    local_session.message_count += 2
                    except Exception as save_err:
                        logger.error(f"Failed to save streamed chat message: {save_err}")
        
        # Return a streaming response with SSE content type
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable proxy buffering
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stream chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ── Chat Sessions ────────────────────────────────────

@router.get("/chat/sessions/{session_id}/messages")
async def get_session_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all messages for a specific session, oldest first."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at)
    )
    messages = result.scalars().all()
    
    formatted_messages = []
    for m in messages:
        msg_dict = m.to_dict()
        if msg_dict["sources"]:
            try:
                msg_dict["sources"] = json.loads(msg_dict["sources"])
            except Exception:
                pass
        formatted_messages.append(msg_dict)
        
    return {
        "messages": formatted_messages,
        "total": len(messages)
    }


@router.get("/chat/sessions")
async def list_sessions(db: AsyncSession = Depends(get_db)):
    """List all chat sessions, newest first."""
    result = await db.execute(
        select(ChatSession).order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    return {
        "sessions": [s.to_dict() for s in sessions],
        "total": len(sessions)
    }


@router.delete("/chat/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a chat session, its messages, associated documents (and files),
    and all vector embeddings from ChromaDB.
    """
    # 1. Check if session exists
    result = await db.execute(
        select(ChatSession).where(ChatSession.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # 2. Find and delete all documents for this session
    doc_result = await db.execute(
        select(Document).where(Document.session_id == session_id)
    )
    docs = doc_result.scalars().all()
    for doc in docs:
        await document_service.delete_document(db, doc.id)
        
    # 3. Clean up any remaining chunks in ChromaDB for this session
    remove_session_from_index(session_id)
    
    # 4. Delete messages
    await db.execute(
        delete(ChatMessage).where(ChatMessage.session_id == session_id)
    )
    
    # 5. Delete session
    await db.execute(
        delete(ChatSession).where(ChatSession.id == session_id)
    )
    
    await db.commit()
    
    return {"message": "Session and all associated data deleted successfully"}

