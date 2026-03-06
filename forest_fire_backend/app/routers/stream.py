"""
视频流路由 — 每路摄像头独立的 YOLO 实时检测流
"""
import os
import time
import asyncio
from pathlib import Path
from datetime import datetime

import cv2
import numpy as np
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from ultralytics import YOLO
from sqlmodel import Session, select

from app.database import engine
from app.models.alert import Alert
from app.models.supervisor import Camera
from app.models.admin import SystemConfig
from app.routers.ws import ws_manager

router = APIRouter(prefix="/api/stream", tags=["stream"])

# ==================== 全局常量 ====================

# demo.mp4 的绝对路径（放在 forest_fire_backend/ 根目录下）
BASE_DIR = Path(__file__).resolve().parent.parent.parent   # => forest_fire_backend/
DEMO_VIDEO = str(BASE_DIR / "demo.mp4")

# YOLO 模型文件的绝对路径
MODEL_PATH = str(BASE_DIR / "app" / "models" / "best.pt")

# ==================== 加载 YOLO 模型（全局单例）====================

model = None
try:
    if os.path.exists(MODEL_PATH):
        model = YOLO(MODEL_PATH)
        print(f"✅ YOLO model loaded from {MODEL_PATH}")
    else:
        print(f"⚠️  YOLO model not found at {MODEL_PATH}")
except Exception as e:
    print(f"❌ Error loading YOLO model: {e}")

# 全局冷却时间（防止同一秒内重复生成大量告警）
last_alert_time = 0
ALERT_COOLDOWN = 10.0  # 秒


# ==================== 核心：逐帧生成器 ====================

async def generate_frames(camera_id: int):
    """为指定摄像头生成 MJPEG 帧流，带 YOLO 实时检测"""
    global last_alert_time

    # ---------- 1. 从数据库读取摄像头信息和系统配置 ----------
    camera_name = f"Camera-{camera_id}"
    camera_enable_ai = True
    yolo_threshold = 0.6

    with Session(engine) as session:
        cam = session.get(Camera, camera_id)
        if cam:
            camera_name = cam.name
            camera_enable_ai = cam.enable_ai
        else:
            # 摄像头不存在 → 持续输出红色错误帧
            while True:
                err = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(err, f"Camera {camera_id} Not Found",
                            (60, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                _, buf = cv2.imencode('.jpg', err)
                yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n'
                await asyncio.sleep(1)
            return  # 不会执行到这里，但让代码意图清晰

        # 读取系统配置的 YOLO 阈值
        conf_row = session.exec(
            select(SystemConfig).where(SystemConfig.key == "yolo_confidence")
        ).first()
        if conf_row:
            try:
                yolo_threshold = float(conf_row.value)
            except (ValueError, TypeError):
                pass

    # ---------- 2. 打开视频源 ----------
    # 当前统一使用 demo.mp4 作为所有摄像头的模拟源
    video_path = DEMO_VIDEO
    print(f"📹 Camera [{camera_id}] {camera_name} → opening {video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Cannot open video: {video_path}")
        # 持续输出黄色提示帧
        while True:
            err = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(err, "Video Source Unavailable",
                        (50, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
            cv2.putText(err, f"Path: {video_path}",
                        (30, 270), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            _, buf = cv2.imencode('.jpg', err)
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n'
            await asyncio.sleep(1)
        return

    # ---------- 3. 逐帧推理循环 ----------
    frame_count = 0
    while True:
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # 循环播放
            continue

        # 每 ~100 帧（约 3 秒）重新从数据库读取 enable_ai 状态，使开关实时生效
        frame_count += 1
        if frame_count % 100 == 0:
            with Session(engine) as session:
                cam_refresh = session.get(Camera, camera_id)
                if cam_refresh:
                    camera_enable_ai = cam_refresh.enable_ai

        # 如果模型已加载，且该摄像头开启了 AI 检测，则执行 YOLO 推理
        if model is not None and camera_enable_ai:
            results = model(frame, verbose=False)
            result = results[0]
            annotated_frame = result.plot()  # 画出检测框

            # 当检测到目标时判断是否触发告警
            if len(result.boxes) > 0:
                highest_conf = float(result.boxes.conf.max())
                now = time.time()

                if highest_conf >= yolo_threshold and (now - last_alert_time) > ALERT_COOLDOWN:
                    last_alert_time = now

                    # 保存截图
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    img_name = f"fire_{camera_id}_{ts}.jpg"
                    uploads_dir = str(BASE_DIR / "uploads")
                    os.makedirs(uploads_dir, exist_ok=True)
                    save_path = os.path.join(uploads_dir, img_name)
                    cv2.imwrite(save_path, frame)
                    img_url = f"/static/{img_name}"

                    # 写入数据库
                    alert_id = None
                    with Session(engine) as session:
                        new_alert = Alert(
                            image_path=img_url,
                            yolo_confidence=highest_conf,
                            status="pending",
                        )
                        session.add(new_alert)
                        session.commit()
                        session.refresh(new_alert)
                        alert_id = new_alert.id

                    # WebSocket 广播
                    alert_payload = {
                        "id": alert_id,
                        "camera_name": camera_name,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "image_path": img_url,
                        "yolo_confidence": highest_conf,
                        "status": "pending",
                        "llm_result": "YOLO 检出疑似火情，等待大模型二次确认...",
                    }
                    asyncio.create_task(ws_manager.broadcast(alert_payload))
                    print(f"🔥 Alert #{alert_id} from [{camera_name}] conf={highest_conf:.2f}")
        else:
            # 模型未加载 或 AI 检测已关闭时直接输出原始帧
            annotated_frame = frame

        # 编码并输出 MJPEG 帧
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n'
        await asyncio.sleep(0.033)  # ≈ 30 fps


# ==================== 路由 ====================

@router.get("/video/{camera_id}")
async def video_feed(camera_id: int):
    """动态获取指定摄像头的 YOLO 实时检测视频流（MJPEG）"""
    return StreamingResponse(
        generate_frames(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
