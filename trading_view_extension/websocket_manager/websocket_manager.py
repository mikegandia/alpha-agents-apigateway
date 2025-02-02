from config import logger

class WebSocketManager:
    def __init__(self):
        self.connections = {}  # Dictionary to store {websocket_id: websocket}

    def add_connection(self,websocket_id, websocket):
        """
        Add a WebSocket connection to the manager.
        
        Args:
            websocket: The WebSocket connection object.
        Returns:
            websocket_id: The unique identifier for the WebSocket.
        """
        self.connections[str(websocket_id)] = websocket
        return websocket_id

    def get_connection(self, websocket_id):
        """
        Retrieve a WebSocket connection from the manager.
        
        Args:
            websocket_id: The unique identifier for the WebSocket.
        Returns:
            The WebSocket connection object, or None if not found.
        """
        logger.info(f"Connections: {self.connections}")
        return self.connections[f"{websocket_id}"]

    def remove_connection(self, websocket_id):
        """
        Remove a WebSocket connection from the manager.
        
        Args:
            websocket_id: The unique identifier for the WebSocket.
        """
        if websocket_id in self.connections:
            del self.connections[websocket_id]
