
from collections import defaultdict

from fastapi import WebSocket, WebSocketDisconnect


class NotificationConnectionManager:
    def __init__(self):
        # One user can have multiple active connections.
        self.active_connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id].add(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        connections = self.active_connections.get(user_id)

        if connections is not None:
            connections.discard(websocket)

            if not connections:
                self.active_connections.pop(user_id, None)

    async def send_to_user(self, user_id: int, message: dict):
        connections = list(self.active_connections.get(user_id, set()))

        for websocket in connections:
            try:
                await websocket.send_json(message)
            except (WebSocketDisconnect, RuntimeError):
                self.disconnect(user_id, websocket)


notification_manager = NotificationConnectionManager()
