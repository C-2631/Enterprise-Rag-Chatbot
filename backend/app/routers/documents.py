"""
Document Router — API endpoints for document management.

Endpoints:
- POST   /api/v1/documents/upload  → Upload a new document
- GET    /api/v1/documents         → List all documents
- GET    /api/v1/documents/{id}    → Get one document
- DELETE /api/v1/documents/{id}    → Delete a document

This router is THIN — it only handles HTTP concerns:
- Extract data from requests
- Call the service layer
- Return HTTP responses

All business logic lives in document_service.py.
"""

import logging

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services import document_service

logger = logging.getLogger(__name__)

# Create router with tag for API docs grouping
router = APIRouter(tags=["Documents"])


@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    session_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a document for processing.
    
    Accepts: PDF, DOCX, TXT, MD files (max 50MB)
    """
    try:
        # Read the file content into memory
        file_content = await file.read()
        file_size = len(file_content)
        
        # If session_id is not provided, create a new session automatically
        created_session = False
        if not session_id or session_id == "null" or session_id == "undefined":
            from app.models.chat import ChatSession
            session = ChatSession(
                title=f"Chat on {file.filename[:40]}"
            )
            db.add(session)
            await db.flush()
            session_id = session.id
            created_session = True
            
        logger.info(f"Upload request: {file.filename} ({file_size} bytes), Session: {session_id}")
        
        # Process the document (validate → save → parse → chunk)
        doc = await document_service.process_document(
            db=db,
            filename=file.filename,
            file_content=file_content,
            file_size=file_size,
            session_id=session_id
        )
        
        return {
            "message": f"Document '{file.filename}' uploaded successfully",
            "document": doc.to_dict(),
            "session_id": session_id,
            "created_session": created_session
        }
    
    except ValueError as e:
        # Validation errors → 400 Bad Request
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/documents")
async def list_documents(
    session_id: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List uploaded documents, optionally filtered by session_id.
    """
    documents = await document_service.get_all_documents(db, session_id=session_id)
    return {
        "documents": documents,
        "total": len(documents)
    }


@router.get("/documents/{document_id}")
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single document by ID.
    
    Path parameter: document_id is extracted from the URL
    Example: GET /api/v1/documents/abc-123-def
    """
    doc = await document_service.get_document_by_id(db, document_id)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"document": doc.to_dict()}


@router.delete("/documents/{document_id}")
async def delete_document_endpoint(
    document_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document and its associated file.
    
    Returns 404 if document doesn't exist.
    """
    deleted = await document_service.delete_document(db, document_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully"}