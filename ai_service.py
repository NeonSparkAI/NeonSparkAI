
"""
AI Service Module - Updated for Gemini 1.5 Flash
Handles AI processing, status tracking, and history management
"""

import asyncio
import uuid
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
import google.generativeai as genai
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class AIRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=10000)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=1, ge=1, le=5)
    timeout: int = Field(default=30, ge=5, le=300)

class AIResponse(BaseModel):
    request_id: str
    status: ProcessingStatus
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class AIServiceManager:
    """Manages AI service operations with Gemini 1.5 Flash"""
    
    def __init__(self):
        self.processing_history: Dict[str, AIResponse] = {}
        self.active_requests: Dict[str, asyncio.Task] = {}
        self.request_count = 0
        self.service_status = "initializing"
        self.start_time = datetime.now()
        self.model = None
        self._initialize_gemini()
    
    def _initialize_gemini(self):
        """Initialize Gemini 1.5 Flash model"""
        try:
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                logger.error("GEMINI_API_KEY not found in environment")
                self.service_status = "configuration_error"
                return
            
            genai.configure(api_key=api_key)
            # Use Gemini 1.5 Flash specifically
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.service_status = "healthy"
            logger.info("Gemini 1.5 Flash model initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            self.service_status = "model_error"
    
    async def process_request(self, request: AIRequest) -> str:
        """Process an AI request and return request ID for tracking"""
        if self.service_status != "healthy":
            raise Exception(f"AI service not available: {self.service_status}")
        
        request_id = str(uuid.uuid4())
        self.request_count += 1
        
        # Create initial response record
        ai_response = AIResponse(
            request_id=request_id,
            status=ProcessingStatus.PENDING,
            created_at=datetime.now(),
            metadata={
                "prompt_length": len(request.prompt),
                "parameters": request.parameters,
                "priority": request.priority,
                "timeout": request.timeout,
                "model": "gemini-1.5-flash"
            }
        )
        
        self.processing_history[request_id] = ai_response
        
        # Start async processing
        task = asyncio.create_task(self._process_ai_task(request_id, request))
        self.active_requests[request_id] = task
        
        logger.info(f"Started Gemini 1.5 Flash processing for request {request_id}")
        return request_id
    
    async def _process_ai_task(self, request_id: str, request: AIRequest):
        """Internal method to handle AI processing with Gemini 1.5 Flash"""
        try:
            # Update status to processing
            self.processing_history[request_id].status = ProcessingStatus.PROCESSING
            start_time = time.time()
            
            # Configure generation settings optimized for Gemini 1.5 Flash
            generation_config = {
                'temperature': 0.7,
                'top_p': 0.8,
                'top_k': 40,
                'max_output_tokens': 2048,
                'candidate_count': 1,
            }
            
            # Apply custom parameters if provided
            if 'temperature' in request.parameters:
                generation_config['temperature'] = request.parameters['temperature']
            if 'max_tokens' in request.parameters:
                generation_config['max_output_tokens'] = request.parameters['max_tokens']
            
            # Process with Gemini 1.5 Flash
            try:
                response = await asyncio.wait_for(
                    self.model.generate_content_async(
                        request.prompt,
                        generation_config=generation_config
                    ),
                    timeout=request.timeout
                )
                
                result = response.text
                
            except asyncio.TimeoutError:
                raise Exception(f"Processing timeout after {request.timeout} seconds")
            except Exception as e:
                raise Exception(f"Gemini API error: {str(e)}")
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Update response
            response_obj = self.processing_history[request_id]
            response_obj.status = ProcessingStatus.COMPLETED
            response_obj.result = result
            response_obj.completed_at = datetime.now()
            response_obj.processing_time = processing_time
            response_obj.metadata.update({
                "tokens_processed": len(request.prompt.split()),
                "response_length": len(result) if result else 0
            })
            
            logger.info(f"Completed Gemini 1.5 Flash processing for request {request_id} in {processing_time:.2f}s")
            
        except asyncio.CancelledError:
            self.processing_history[request_id].status = ProcessingStatus.CANCELLED
            self.processing_history[request_id].completed_at = datetime.now()
            logger.info(f"AI processing cancelled for request {request_id}")
            
        except Exception as e:
            self.processing_history[request_id].status = ProcessingStatus.FAILED
            self.processing_history[request_id].error = str(e)
            self.processing_history[request_id].completed_at = datetime.now()
            logger.error(f"AI processing error for request {request_id}: {e}")
            
        finally:
            # Clean up active request
            if request_id in self.active_requests:
                del self.active_requests[request_id]
    
    def get_request_status(self, request_id: str) -> Optional[AIResponse]:
        """Get status of a specific request"""
        return self.processing_history.get(request_id)
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get overall service status"""
        active_count = len(self.active_requests)
        completed_count = len([r for r in self.processing_history.values() if r.status == ProcessingStatus.COMPLETED])
        failed_count = len([r for r in self.processing_history.values() if r.status == ProcessingStatus.FAILED])
        
        return {
            "status": self.service_status,
            "model": "gemini-1.5-flash",
            "uptime": str(datetime.now() - self.start_time),
            "total_requests": self.request_count,
            "active_requests": active_count,
            "completed_requests": completed_count,
            "failed_requests": failed_count,
            "success_rate": round((completed_count / max(self.request_count, 1)) * 100, 2),
            "memory_usage": len(self.processing_history),
            "api_configured": self.model is not None
        }
    
    def get_processing_history(self, limit: int = 50, status_filter: Optional[ProcessingStatus] = None) -> List[AIResponse]:
        """Get processing history with optional filtering"""
        history = list(self.processing_history.values())
        
        if status_filter:
            history = [r for r in history if r.status == status_filter]
        
        # Sort by creation time (newest first)
        history.sort(key=lambda x: x.created_at, reverse=True)
        
        return history[:limit]
    
    async def cancel_request(self, request_id: str) -> bool:
        """Cancel an active request"""
        if request_id in self.active_requests:
            task = self.active_requests[request_id]
            task.cancel()
            
            # Update status will be handled in the task's finally block
            logger.info(f"Cancelled AI processing for request {request_id}")
            return True
        
        return False

# Global service manager instance
ai_service_manager = AIServiceManager()
