import asyncio
import websockets
import json
from datetime import datetime

async def test_alert():
    uri = "ws://localhost:8000/ws/alerts"
    async with websockets.connect(uri) as websocket:
        
        # 模拟一条完整的告警消息
        fake_alert = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "image_path": "https://img.zcool.cn/community/019b885be29d10a801209252033c4a.jpg@1280w_1l_2o_100sh.jpg",  # 找了一张网上的火灾示意图
            "yolo_confidence": 0.95,
            "llm_result": "⚠️ 经视觉大模型二次确认：画面中存在明显的明火和浓烟，确认为真实火灾！",
            "status": "pending"
        }
        
        # 注意：目前的后端 WS 还没有实现把接收到的消息 broadcast 给其他所有人。
        # 为了方便演示，这里可以直接在后端 `ws.py` 中写个测试 HTTP 接口，或者直接发。
        # 这里仅作脚本示例，真实情况下是后端 YOLO 进程直接调用 ws_manager.broadcast()

        print("This script is just a placeholder. Real WS broadcast happens inside FastAPI.")

if __name__ == "__main__":
    asyncio.run(test_alert())
