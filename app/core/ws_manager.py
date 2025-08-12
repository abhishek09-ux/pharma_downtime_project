# app/core/ws_manager.py
from typing import List
from fastapi import WebSocket
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        # Lock to protect connection list in concurrency
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """
        Broadcast a dictionary message to all connected clients as JSON.
        """
        if not self.active_connections:
            return
        text = json.dumps(message, default=str)
        async with self._lock:
            to_remove = []
            for ws in self.active_connections:
                try:
                    await ws.send_text(text)
                except Exception:
                    # If send fails, schedule removal
                    to_remove.append(ws)
            for ws in to_remove:
                try:
                    self.active_connections.remove(ws)
                except ValueError:
                    pass

# create global manager instance to import
ws_manager = ConnectionManager()
