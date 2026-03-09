import json
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from app.models.user import User
from app.routers.auth import require_roles

router = APIRouter(tags=["websocket"])


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_text(json.dumps(message))


ws_manager = ConnectionManager()


@router.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; server primarily pushes messages.
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


class DummyAlert(BaseModel):
    image_url: str = (
        "https://img.alicdn.com/imgextra/i4/"
        "O1CN01fN6G2Z1D2H5Z2Y1Z1_!!6000000000155-2-tps-800-600.png"
    )
    llm_text: str = "测试告警消息"


@router.post("/api/debug/fire_alert")
async def trigger_fire_alert(
    alert: DummyAlert,
    current_user: User = Depends(require_roles("admin")),
):
    """仅供测试：手动触发一次 WebSocket 告警广播（仅管理员）。"""
    _ = current_user
    fake_alert = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "image_path": alert.image_url,
        "yolo_confidence": 0.92,
        "llm_result": alert.llm_text,
        "status": "pending",
    }
    await ws_manager.broadcast(fake_alert)
    return {"msg": "Alert broadcasted"}
