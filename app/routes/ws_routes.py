# app/routes/ws_routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.core.ws_manager import ws_manager

router = APIRouter()

@router.websocket("/ws/monitor")
async def websocket_monitor(websocket: WebSocket):
    """
    Clients connect here to get live sensor readings and predictions.
    """
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; we don't expect client messages but
            # allow ping/pong. Wait for any incoming message (optional).
            await websocket.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(websocket)
