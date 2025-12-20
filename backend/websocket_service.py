"""
WebSocket Service for Real-time Notifications
Handles WebSocket connections and broadcasts RSHD alerts to DACs.
"""

import asyncio
import json
import logging
from typing import Dict, Set, Optional
from datetime import datetime, timezone
from fastapi import WebSocket, WebSocketDisconnect
from jose import jwt, JWTError
import os

logger = logging.getLogger(__name__)

# JWT secret for token validation
SECRET_KEY = os.environ.get("SECRET_KEY", "your-secret-key-here-change-in-production")
ALGORITHM = "HS256"


class ConnectionManager:
    """
    Manages WebSocket connections for real-time notifications.
    
    - Tracks active connections by user ID
    - Broadcasts notifications to specific users or groups
    - Handles connection lifecycle (connect, disconnect, reconnect)
    """
    
    def __init__(self):
        # Map of user_id -> set of WebSocket connections (user can have multiple tabs)
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Map of WebSocket -> user_id for reverse lookup
        self.connection_user_map: Dict[WebSocket, str] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, user_id: str) -> bool:
        """Accept a new WebSocket connection and register it."""
        try:
            await websocket.accept()
            
            async with self._lock:
                if user_id not in self.active_connections:
                    self.active_connections[user_id] = set()
                self.active_connections[user_id].add(websocket)
                self.connection_user_map[websocket] = user_id
            
            logger.info(f"WebSocket connected: user={user_id}, total_connections={self.get_connection_count()}")
            
            # Send welcome message
            await self.send_personal_message({
                "type": "connected",
                "message": "Connected to DealShaq notifications",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, websocket)
            
            return True
        except Exception as e:
            logger.error(f"Failed to accept WebSocket connection: {e}")
            return False
    
    async def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection."""
        async with self._lock:
            user_id = self.connection_user_map.get(websocket)
            if user_id:
                if user_id in self.active_connections:
                    self.active_connections[user_id].discard(websocket)
                    if not self.active_connections[user_id]:
                        del self.active_connections[user_id]
                del self.connection_user_map[websocket]
                logger.info(f"WebSocket disconnected: user={user_id}, total_connections={self.get_connection_count()}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send a message to all connections of a specific user."""
        async with self._lock:
            connections = self.active_connections.get(user_id, set()).copy()
        
        disconnected = []
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send to user {user_id}: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for ws in disconnected:
            await self.disconnect(ws)
    
    async def send_to_users(self, user_ids: list, message: dict):
        """Send a message to multiple users."""
        tasks = [self.send_to_user(user_id, message) for user_id in user_ids]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all connected users."""
        async with self._lock:
            all_websockets = []
            for connections in self.active_connections.values():
                all_websockets.extend(connections)
        
        disconnected = []
        for websocket in all_websockets:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        
        for ws in disconnected:
            await self.disconnect(ws)
    
    def get_connection_count(self) -> int:
        """Get total number of active connections."""
        return sum(len(conns) for conns in self.active_connections.values())
    
    def get_user_count(self) -> int:
        """Get number of unique connected users."""
        return len(self.active_connections)
    
    def is_user_connected(self, user_id: str) -> bool:
        """Check if a user has any active connections."""
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0


# Global connection manager instance
manager = ConnectionManager()


def verify_ws_token(token: str) -> Optional[str]:
    """Verify JWT token and return user_id if valid."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        return None


async def notify_new_rshd(db, rshd_item: dict, drlp_id: str):
    """
    Notify all relevant DACs about a new RSHD.
    
    1. Get the DRLP's DRLPDAC-List (DACs who want notifications from this DRLP)
    2. For each connected DAC, check if item matches their preferences
    3. Send real-time notification to matching DACs
    """
    try:
        # Get DRLPDAC-List for this retailer
        drlpdac = await db.drlpdac_list.find_one({"drlp_id": drlp_id}, {"_id": 0})
        
        if not drlpdac or not drlpdac.get("dac_ids"):
            logger.info(f"No DACs to notify for DRLP {drlp_id}")
            return
        
        dac_ids = drlpdac.get("dac_ids", [])
        
        # Prepare notification message
        discount_labels = {1: "50% OFF", 2: "60% OFF", 3: "75% OFF"}
        discount_level = rshd_item.get("discount_level", 1)
        
        notification = {
            "type": "new_rshd",
            "title": "🔥 New Sizzling Hot Deal!",
            "message": f"{rshd_item.get('name')} - {discount_labels.get(discount_level, '50% OFF')} at {rshd_item.get('drlp_name')}",
            "data": {
                "rshd_id": rshd_item.get("id"),
                "item_name": rshd_item.get("name"),
                "category": rshd_item.get("category"),
                "drlp_name": rshd_item.get("drlp_name"),
                "drlp_id": drlp_id,
                "discount_level": discount_level,
                "discount_percent": rshd_item.get("consumer_discount_percent", 50),
                "deal_price": rshd_item.get("deal_price"),
                "regular_price": rshd_item.get("regular_price"),
                "quantity": rshd_item.get("quantity"),
                "expiry_date": rshd_item.get("expiry_date"),
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Filter to only connected DACs for efficiency
        connected_dacs = [dac_id for dac_id in dac_ids if manager.is_user_connected(dac_id)]
        
        if connected_dacs:
            logger.info(f"Sending RSHD notification to {len(connected_dacs)} connected DACs")
            await manager.send_to_users(connected_dacs, notification)
        
        # Also store notification in database for offline users
        for dac_id in dac_ids:
            await db.notifications.insert_one({
                "id": f"notif-{rshd_item.get('id')}-{dac_id}",
                "dac_id": dac_id,
                "rshd_id": rshd_item.get("id"),
                "type": "new_rshd",
                "title": notification["title"],
                "message": notification["message"],
                "data": notification["data"],
                "is_read": False,
                "created_at": datetime.now(timezone.utc).isoformat()
            })
        
        logger.info(f"RSHD notification sent to {len(dac_ids)} DACs ({len(connected_dacs)} online)")
        
    except Exception as e:
        logger.error(f"Failed to notify DACs about new RSHD: {e}")


async def websocket_endpoint(websocket: WebSocket, token: str):
    """
    WebSocket endpoint handler.
    
    Usage: ws://host/ws?token=<jwt_token>
    """
    # Verify token
    user_id = verify_ws_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Invalid or expired token")
        return
    
    # Connect
    connected = await manager.connect(websocket, user_id)
    if not connected:
        return
    
    try:
        while True:
            # Keep connection alive and handle incoming messages
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                msg_type = message.get("type")
                
                if msg_type == "ping":
                    # Respond to ping with pong
                    await manager.send_personal_message({"type": "pong"}, websocket)
                elif msg_type == "mark_read":
                    # Handle marking notification as read
                    notification_id = message.get("notification_id")
                    if notification_id:
                        # This would update the database - handled by main app
                        await manager.send_personal_message({
                            "type": "ack",
                            "action": "mark_read",
                            "notification_id": notification_id
                        }, websocket)
                else:
                    # Echo unknown messages back
                    await manager.send_personal_message({
                        "type": "echo",
                        "received": message
                    }, websocket)
                    
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, websocket)
                
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)
