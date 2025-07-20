"""Health check router."""

from fastapi import APIRouter, HTTPException
from app.services.supabase_service import supabase_service
from pydantic import BaseModel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: datetime
    database: str
    version: str = "1.0.0"


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify service status.
    
    Returns:
        HealthResponse: Service health status
    """
    try:
        # Check database connection
        db_healthy = await supabase_service.health_check()
        
        if not db_healthy:
            raise HTTPException(
                status_code=503,
                detail="Database connection failed"
            )
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            database="connected"
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}"
        )