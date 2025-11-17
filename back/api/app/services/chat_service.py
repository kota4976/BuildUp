"""Chat service for WebSocket connections"""
import logging
from typing import Dict, Set
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manage WebSocket connections for chat"""
    
    def __init__(self):
        # Map of conversation_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Map of WebSocket -> (user_id, conversation_id)
        self.connection_info: Dict[WebSocket, tuple] = {}
        # Map of user_id -> set of WebSocket connections
        self.user_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str, conversation_id: str):
        """
        Connect a WebSocket to a conversation
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
            conversation_id: Conversation ID
        """
        await websocket.accept()
        
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = set()
        
        self.active_connections[conversation_id].add(websocket)
        self.connection_info[websocket] = (user_id, conversation_id)
        
        # Add to user connections map
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(websocket)
        
        logger.info(f"User {user_id} connected to conversation {conversation_id}")
    
    def disconnect(self, websocket: WebSocket):
        """
        Disconnect a WebSocket
        
        Args:
            websocket: WebSocket connection
        """
        if websocket in self.connection_info:
            user_id, conversation_id = self.connection_info[websocket]
            
            if conversation_id in self.active_connections:
                self.active_connections[conversation_id].discard(websocket)
                
                # Clean up empty conversation sets
                if not self.active_connections[conversation_id]:
                    del self.active_connections[conversation_id]
            
            # Remove from user connections map
            if user_id in self.user_connections:
                self.user_connections[user_id].discard(websocket)
                
                # Clean up empty user connection sets
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            del self.connection_info[websocket]
            
            logger.info(f"User {user_id} disconnected from conversation {conversation_id}")
    
    async def send_to_conversation(self, conversation_id: str, message: dict):
        """
        Send a message to all connections in a conversation
        
        Args:
            conversation_id: Conversation ID
            message: Message data to send
        """
        if conversation_id in self.active_connections:
            connections = self.active_connections[conversation_id].copy()
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message: {str(e)}")
                    # Remove dead connection
                    self.disconnect(connection)
    
    async def send_to_user(self, user_id: str, message: dict):
        """
        Send a message to all connections for a specific user
        
        Args:
            user_id: User ID
            message: Message data to send
        """
        if user_id in self.user_connections:
            connections = self.user_connections[user_id].copy()
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {str(e)}")
                    # Remove dead connection
                    self.disconnect(connection)
    
    def get_user_id(self, websocket: WebSocket) -> str:
        """
        Get user ID for a WebSocket connection
        
        Args:
            websocket: WebSocket connection
        
        Returns:
            User ID or None
        """
        if websocket in self.connection_info:
            return self.connection_info[websocket][0]
        return None


# Global connection manager instance
manager = ConnectionManager()

