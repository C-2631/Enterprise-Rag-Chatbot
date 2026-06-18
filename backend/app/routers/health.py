"""
Health Checker router.
Every production API needs a health endpoint. It's used by:
-> Load balance, to know if this server can handle requests
-> Monitoring tools, to alert when the service is down
-> Docker, HEALTHCHECK instruction pings this endpoint
-> Developers, to quickly verify the server is running
"""

from fastapi import APIRouter

# Import our settings to show app info in the response
from app.config import get_settings
from app.services.vectorstore_service import get_collection_stats

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    """
    Detailed health check showing component status.

    In later pahse, this will check:
    -> Databse connection
    -> Vectore store connection
    -> LLM API availability
    """
    settings = get_settings()

    return {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "components": {
            "database": "connected",
            "vector_store": get_collection_stats(),
            "llm_api": "not configured",
            "embedding": "configured"
        }
    }