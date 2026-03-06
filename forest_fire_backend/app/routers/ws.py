from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json

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
            # 维持连接，后续主要是后端主动 broadcast
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)

from datetime import datetime
from pydantic import BaseModel

class DummyAlert(BaseModel):
    image_url: str = "https://img.alicdn.com/imgextra/i4/O1CN01fN6G2Z1D2H5Z2Y1Z1_!!6000000000155-2-tps-800-600.png"
    llm_text: str = "⚠️ 经视觉大模型二次确认：画面中存在明显的明火和浓烟，确认为真实火灾！"

@router.post("/api/debug/fire_alert")
async def trigger_fire_alert(alert: DummyAlert):
    """【仅供测试】手动触发一次 WebSocket 告警广播"""
    fake_alert = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "image_path": alert.image_url,
        "yolo_confidence": 0.92,
        "llm_result": alert.llm_text,
        "status": "pending"
    }
    await ws_manager.broadcast(fake_alert)
    return {"msg": "Alert broadcasted"}
