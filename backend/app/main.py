"""
Main application entry point for the Enterprise RAG Chatbot API.

This is the file that uvicorn runs:
    uvicorn app.main:app --reload

'app.main' = this file (app/main.py)
':app'     = the 'app' variable defined below (the FastAPI instance)
'--reload' = restart server when code changes (dev only!)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import our settings and routers
from app.config import get_settings
from app.database import init_db
from app.routers import health, documents, search, chat

def create_app() -> FastAPI:
    """
    Application factory pattern.
    
    Why a function instead of just creating 'app' directly?
    - Cleaner: all setup logic is in one place
    - Testable: tests can create their own app instance
    - Configurable: can pass different settings for dev/test/prod
    """
    
    # Load settings from .env
    settings = get_settings()

    # Create the FastAPI application instance
    # This is the core object — everything attaches to it
    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "A production-grade chatbot that answers questions from "
            "uploaded documents using Retrieval-Augmented Generation (RAG). "
            "Powered by Google Gemini, LangChain, and ChromaDB."
        ),
        docs_url="/docs",       # Swagger UI URL (interactive API testing)
        redoc_url="/redoc"      # ReDoc URL (beautiful API documentation)
    )

    # ── CORS Middleware ──────────────────────────────────────────
    # CORS = Cross-Origin Resource Sharing
    # 
    # Without this, the browser BLOCKS the frontend (localhost:5173)
    # from calling the backend (localhost:8000) because they're
    # different "origins" (different ports = different origin).
    #
    # This middleware tells the browser: "Yes, I trust requests
    # from these origins, let them through."
    
    # Split "http://localhost:5173" into a list: ["http://localhost:5173"]
    # This supports multiple origins like "http://localhost:5173,http://localhost:3000"
    origins = [
        origin.strip() 
        for origin in settings.cors_origins.split(",")
    ]

    application.add_middleware(
        CORSMiddleware,
        allow_origins=origins,          # Which frontend URLs can call us
        allow_credentials=True,         # Allow cookies/auth headers
        allow_methods=["*"],            # Allow ALL HTTP methods (GET, POST, etc.)
        allow_headers=["*"],            # Allow ALL headers
    )

    # ── Register Routers ─────────────────────────────────────────
    # Routers group related endpoints under a common prefix.
    # health.router has /health → becomes /api/v1/health
    application.include_router(
        health.router,
        prefix="/api/v1"
    )
    application.include_router(
        documents.router,
        prefix="/api/v1"
    )
    application.include_router(
        search.router, 
        prefix="/api/v1"
    )
    application.include_router(
        chat.router,
        prefix="/api/v1"
    )

    # ── Root Endpoint ────────────────────────────────────────────
    @application.get("/")
    async def root():
        """Root endpoint — shows welcome message."""
        return {
            "message": f"Welcome to {settings.app_name}",
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/api/v1/health"
        }
    
    @application.on_event("startup")
    async def startup():
        """Initialize database tables on app startup."""
        await init_db()

    return application


# Create the app instance
# This is what uvicorn looks for: 'app' in 'app.main'
app = create_app()