import json
from typing import Dict, List
import asyncio
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # Maps a channel/topic name to a list of active websocket connections
        # e.g., "feed" -> [ws1, ws2], "match_123" -> [ws3]
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, channel: str):
        await websocket.accept()
        if channel not in self.active_connections:
            self.active_connections[channel] = []
        self.active_connections[channel].append(websocket)

    def disconnect(self, websocket: WebSocket, channel: str):
        if channel in self.active_connections:
             if websocket in self.active_connections[channel]:
                 self.active_connections[channel].remove(websocket)
             if len(self.active_connections[channel]) == 0:
                 del self.active_connections[channel]

    async def broadcast(self, channel: str, message: dict):
        if channel in self.active_connections:
            message_str = json.dumps(message)
            # Need to create instances because a disconnect could mutate the list while iterating
            for connection in list(self.active_connections[channel]):
                try:
                    await connection.send_text(message_str)
                except Exception as e:
                    self.disconnect(connection, channel)
                    print(f"WS broadcast error: {e}")

manager = ConnectionManager()
