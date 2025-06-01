
"""
AI Service API Routes
RESTful endpoints for AI service communication
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, List
import asyncio
import logging
from datetime import datetime

from .ai_service import (
    AIRequest, 
    AIResponse, 
    ProcessingStatus,
    ai_service_manager
)

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
ai_router = APIRouter(prefix="/api/ai", tags=["AI Service"])

# Rate limiting (simple in-memory implementation)
class RateLimiter:
    def __init__(self, max_requests: int = 100, window_seconds: int = 3600):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = {}
    
    def is_allowed(self, client_id: str) -> bool:
        now = datetime.now().timestamp()
        
        # Clean old requests
        if client_id in self.requests:
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if now - req_time < self.window_seconds
            ]
        else:
            self.requests[client_id] = []
        
        # Check rate limit
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[client_id].append(now)
        return True

rate_limiter = RateLimiter()

def get_client_id(request) -> str:
    """Extract client ID for rate limiting"""
    return request.client.host if hasattr(request, 'client') else "unknown"

@ai_router.post("/process", response_model=dict)
async def process_ai_request(
    ai_request: AIRequest,
    background_tasks: BackgroundTasks,
    request = None
):
    """
    Process an AI request asynchronously
    Returns request ID for status tracking
    """
    try:
        # Rate limiting check
        client_id = get_client_id(request) if request else "api"
        if not rate_limiter.is_allowed(client_id):
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Too many requests."
            )
        
        # Validate request
        if not ai_request.prompt or len(ai_request.prompt.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Prompt cannot be empty"
            )
        
        # Process request
        request_id = await ai_service_manager.process_request(ai_request)
        
        logger.info(f"AI request {request_id} submitted for processing")
        
        return {
            "success": True,
            "request_id": request_id,
            "status": "submitted",
            "message": "Request submitted for processing",
            "estimated_completion": "2-5 seconds"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing AI request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

@ai_router.get("/status", response_model=dict)
async def get_service_status():
    """
    Get overall AI service status and statistics
    """
    try:
        status = ai_service_manager.get_service_status()
        
        return {
            "success": True,
            "service": status,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting service status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get service status: {str(e)}"
        )

@ai_router.get("/status/{request_id}", response_model=dict)
async def get_request_status(request_id: str):
    """
    Get status of a specific AI request
    """
    try:
        response = ai_service_manager.get_request_status(request_id)
        
        if not response:
            raise HTTPException(
                status_code=404,
                detail=f"Request {request_id} not found"
            )
        
        return {
            "success": True,
            "request": response.dict(),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting request status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get request status: {str(e)}"
        )

@ai_router.get("/history", response_model=dict)
async def get_processing_history(
    limit: int = 50,
    status: Optional[ProcessingStatus] = None
):
    """
    Get AI processing history with optional filtering
    """
    try:
        if limit > 200:
            raise HTTPException(
                status_code=400,
                detail="Limit cannot exceed 200"
            )
        
        history = ai_service_manager.get_processing_history(
            limit=limit,
            status_filter=status
        )
        
        return {
            "success": True,
            "history": [item.dict() for item in history],
            "count": len(history),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting processing history: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get processing history: {str(e)}"
        )

@ai_router.delete("/cancel/{request_id}", response_model=dict)
async def cancel_request(request_id: str):
    """
    Cancel an active AI request
    """
    try:
        success = await ai_service_manager.cancel_request(request_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Request {request_id} not found or not active"
            )
        
        return {
            "success": True,
            "message": f"Request {request_id} cancelled successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling request: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel request: {str(e)}"
        )

# Health check endpoint
@ai_router.get("/health", response_model=dict)
async def health_check():
    """
    Health check endpoint for the AI service
    """
    return {
        "status": "healthy",
        "service": "AI Service API",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }
