
"""
NeonSpark AI Backend - Main Application
Enhanced with Gemini 1.5 Flash integration
"""

import os
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import google.generativeai as genai
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()

# Import our AI service modules
from ai_service import ai_service_manager, AIRequest
from api_routes import ai_router
from websocket_handler import websocket_endpoint, websocket_manager, periodic_status_broadcast

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Verify Gemini API key
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables")
    logger.error("Please set GEMINI_API_KEY in your .env file")

# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("Starting NeonSpark AI Backend with Gemini 1.5 Flash...")
    
    # Start background tasks
    status_task = asyncio.create_task(periodic_status_broadcast())
    
    try:
        yield
    finally:
        logger.info("Shutting down NeonSpark AI Backend...")
        status_task.cancel()
        try:
            await status_task
        except asyncio.CancelledError:
            pass

# Create FastAPI application
app = FastAPI(
    title="NeonSpark AI Backend",
    description="AI-powered backend with Gemini 1.5 Flash integration",
    version="2.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS middleware - updated for better security
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080", 
        "http://127.0.0.1:8080",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include AI service routes
app.include_router(ai_router)

# Legacy models for compatibility
class ChatRequest(BaseModel):
    message: str
    thinking_mode: bool = False
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    thinking_steps: Optional[list] = None
    session_id: Optional[str] = None
    processing_time: Optional[float] = None
    model: str = "gemini-1.5-flash"

# WebSocket endpoint for real-time updates
@app.websocket("/ws/{client_id}")
async def websocket_ai_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for AI service real-time updates"""
    await websocket_endpoint(websocket, client_id)

# Enhanced health check endpoint
@app.get("/api/health")
async def health_check():
    """Comprehensive health check with AI service status"""
    try:
        service_status = ai_service_manager.get_service_status()
        
        # Test Gemini API connectivity
        gemini_status = "unknown"
        if GEMINI_API_KEY:
            try:
                # Quick test to verify API key works
                test_model = genai.GenerativeModel('gemini-1.5-flash')
                gemini_status = "configured"
            except Exception as e:
                gemini_status = f"error: {str(e)}"
        else:
            gemini_status = "not_configured"
        
        return {
            "status": "healthy" if service_status["status"] == "healthy" else "degraded",
            "timestamp": datetime.now().isoformat(),
            "backend": "NeonSpark AI Backend v2.1.0",
            "ai_service": {
                "status": service_status["status"],
                "model": service_status["model"],
                "total_requests": service_status["total_requests"],
                "active_requests": service_status["active_requests"],
                "success_rate": service_status["success_rate"],
                "uptime": service_status["uptime"]
            },
            "gemini": {
                "status": gemini_status,
                "api_key_configured": bool(GEMINI_API_KEY),
                "model": "gemini-1.5-flash"
            },
            "websocket": {
                "active_connections": len(websocket_manager.active_connections),
                "status": "active"
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "backend": "NeonSpark AI Backend v2.1.0"
            }
        )

# Legacy chat endpoint (maintained for compatibility)
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Legacy chat endpoint using Gemini 1.5 Flash"""
    try:
        if not GEMINI_API_KEY:
            raise HTTPException(
                status_code=503, 
                detail="AI service not configured. Please set GEMINI_API_KEY."
            )
        
        # Convert to new AI service format
        ai_request = AIRequest(
            prompt=request.message,
            parameters={
                "thinking_mode": request.thinking_mode,
                "session_id": request.session_id,
                "temperature": 0.7
            }
        )
        
        # Process through AI service
        request_id = await ai_service_manager.process_request(ai_request)
        
        # Wait for completion with timeout
        max_wait = 30  # seconds
        wait_time = 0
        response = None
        
        while wait_time < max_wait:
            response = ai_service_manager.get_request_status(request_id)
            if response and response.status in ["completed", "failed", "cancelled"]:
                break
            await asyncio.sleep(0.5)
            wait_time += 0.5
        
        if not response:
            raise HTTPException(status_code=408, detail="Request timeout")
        
        if response.status == "failed":
            raise HTTPException(
                status_code=500, 
                detail=response.error or "AI processing failed"
            )
        
        if response.status == "cancelled":
            raise HTTPException(status_code=499, detail="Request was cancelled")
        
        return ChatResponse(
            response=response.result or "No response generated",
            thinking_steps=response.metadata.get("thinking_steps", []) if response.metadata else [],
            session_id=request.session_id,
            processing_time=response.processing_time,
            model="gemini-1.5-flash"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# Image analysis endpoint
@app.post("/api/analyze-image")
async def analyze_image_endpoint(file: UploadFile = File(...)):
    """Image analysis using Gemini 1.5 Flash vision capabilities"""
    try:
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        if not GEMINI_API_KEY:
            raise HTTPException(
                status_code=503, 
                detail="AI service not configured. Please set GEMINI_API_KEY."
            )
        
        # Read file content
        content = await file.read()
        
        # Create AI request for image analysis
        ai_request = AIRequest(
            prompt=f"Analyze this image in detail. Describe what you see, identify objects, text, colors, and any other notable features. Image filename: {file.filename}",
            parameters={
                "type": "image_analysis",
                "filename": file.filename,
                "content_type": file.content_type,
                "size": len(content),
                "model": "gemini-1.5-flash"
            }
        )
        
        # Process through AI service
        request_id = await ai_service_manager.process_request(ai_request)
        
        # Wait for completion
        max_wait = 30
        wait_time = 0
        response = None
        
        while wait_time < max_wait:
            response = ai_service_manager.get_request_status(request_id)
            if response and response.status in ["completed", "failed", "cancelled"]:
                break
            await asyncio.sleep(0.5)
            wait_time += 0.5
        
        if not response or response.status != "completed":
            raise HTTPException(
                status_code=500, 
                detail=response.error if response else "Analysis failed"
            )
        
        return {
            "analysis": response.result,
            "filename": file.filename,
            "processing_time": response.processing_time,
            "request_id": request_id,
            "model": "gemini-1.5-flash",
            "metadata": response.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Image analysis failed: {str(e)}")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with detailed logging"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url),
            "backend_version": "2.1.0"
        }
    )

if __name__ == "__main__":
    logger.info("Starting NeonSpark AI Backend v2.1.0 with Gemini 1.5 Flash...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3000,
        reload=False,
        log_level="info",
        access_log=True
    )
