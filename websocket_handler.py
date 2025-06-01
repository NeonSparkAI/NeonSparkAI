
"""
WebSocket Handler for Real-time AI Service Updates
"""

import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

from ai_service import ai_service_manager

logger = logging.getLogger(__name__)

class WebSocketManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_subscriptions: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        self.client_subscriptions[client_id] = set()
        logger.info(f"WebSocket client {client_id} connected")
        
        # Send initial service status
        try:
            service_status = ai_service_manager.get_service_status()
            await self.send_personal_message(client_id, {
                "type": "service_status",
                "data": service_status,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to send initial status to {client_id}: {e}")
    
    def disconnect(self, client_id: str):
        """Disconnect a WebSocket client"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.client_subscriptions:
            del self.client_subscriptions[client_id]
        logger.info(f"WebSocket client {client_id} disconnected")
    
    async def send_personal_message(self, client_id: str, message: dict):
        """Send message to a specific client"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {client_id}: {e}")
                self.disconnect(client_id)
    
    async def broadcast_message(self, message: dict):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
            
        message_text = json.dumps(message)
        disconnected_clients = []
        
        for client_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(message_text)
            except Exception as e:
                logger.error(f"Failed to broadcast to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)
    
    async def handle_client_message(self, client_id: str, message: dict):
        """Handle incoming message from client"""
        try:
            message_type = message.get("type")
            
            if message_type == "subscribe":
                # Subscribe to specific request updates
                request_id = message.get("request_id")
                if request_id:
                    self.client_subscriptions[client_id].add(request_id)
                    logger.info(f"Client {client_id} subscribed to request {request_id}")
            
            elif message_type == "unsubscribe":
                # Unsubscribe from request updates
                request_id = message.get("request_id")
                if request_id and request_id in self.client_subscriptions.get(client_id, set()):
                    self.client_subscriptions[client_id].remove(request_id)
                    logger.info(f"Client {client_id} unsubscribed from request {request_id}")
            
            elif message_type == "get_status":
                # Send current service status
                service_status = ai_service_manager.get_service_status()
                await self.send_personal_message(client_id, {
                    "type": "service_status",
                    "data": service_status,
                    "timestamp": datetime.now().isoformat()
                })
            
            elif message_type == "ping":
                # Respond to ping with pong
                await self.send_personal_message(client_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            
        except Exception as e:
            logger.error(f"Error handling message from {client_id}: {e}")

# Global WebSocket manager instance
websocket_manager = WebSocketManager()

async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint handler"""
    await websocket_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                await websocket_manager.handle_client_message(client_id, message)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from client {client_id}: {data}")
                await websocket_manager.send_personal_message(client_id, {
                    "type": "error",
                    "message": "Invalid JSON format"
                })
            
    except WebSocketDisconnect:
        websocket_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        websocket_manager.disconnect(client_id)

async def periodic_status_broadcast():
    """Periodically broadcast service status to all clients"""
    while True:
        try:
            await asyncio.sleep(30)  # Broadcast every 30 seconds
            
            if websocket_manager.active_connections:
                service_status = ai_service_manager.get_service_status()
                await websocket_manager.broadcast_message({
                    "type": "service_status_update",
                    "data": service_status,
                    "timestamp": datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error in periodic status broadcast: {e}")
            await asyncio.sleep(5)  # Wait before retrying
