from typing import Dict, List
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # room_id -> list of websockets
        self.active_rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, room: str, websocket: WebSocket):
        await websocket.accept()
        if room not in self.active_rooms:
            self.active_rooms[room] = []
        self.active_rooms[room].append(websocket)

    def disconnect(self, room: str, websocket: WebSocket):
        if room in self.active_rooms:
            self.active_rooms[room] = [ws for ws in self.active_rooms[room] if ws != websocket]
            if not self.active_rooms[room]:
                del self.active_rooms[room]

    async def broadcast(self, room: str, message: dict):
        if room not in self.active_rooms:
            return
        for connection in self.active_rooms[room]:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()
