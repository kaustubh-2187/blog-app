from fastapi import APIRouter
from api.models.responses import HealthResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Returns API status and version.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0"
    )


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.
    
    Returns whether the API is ready to accept requests.
    """
    # Add checks for dependencies (DB, external APIs, etc.)
    return {
        "ready": True,
        "services": {
            "groq": "available",
            "tavily": "available",
            "gemini": "available"
        }
    }