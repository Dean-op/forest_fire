"""
视频流路由 — 级联推理系统 (Cascaded Inference)
视频正常播放，YOLO 按配置间隔抽帧检测，根据置信度三级分流：
  ≥ high_threshold  → 高危建议，进入人工核实队列 (pending_verify)
  low ~ high        → 异步调用大模型复核，仍进入人工核实队列 (pending_verify)
  < low_threshold   → 忽略

性能优化：
  - 推理前按 yolo_infer_scale 缩放分辨率（降低算力开销）
  - 仅检测帧显示检测框，非检测帧保持原始画面（降低渲染负担）
"""
import os
import time
import asyncio
import base64
import httpx
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
BASE_DIR = Path(__file__).resolve().parent.parent.parent   # => forest_fire_backend/
DEMO_VIDEO = str(BASE_DIR / "demo.mp4")
MODEL_PATH = str(BASE_DIR / "app" / "models" / "best.pt")
UPLOADS_DIR = str(BASE_DIR / "uploads")

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

# 每路摄像头独立的冷却时间戳 {camera_id: timestamp}
camera_cooldowns: dict[int, float] = {}


# ==================== 辅助：从 DB 批量加载系统配置 ====================

def load_detection_config() -> dict:
    """从 SystemConfig 表批量加载级联推理参数，返回 dict"""
    defaults = {
        "yolo_interval": 3.0,
        "yolo_infer_scale": 0.6,
        "yolo_high_threshold": 0.8,
        "yolo_low_threshold": 0.5,
        "alert_cooldown": 10.0,
        "llm_api_url": "",
        "llm_api_key": "",
        "llm_model": "qwen-vl-max",
    }
    keys_needed = list(defaults.keys())
    with Session(engine) as session:
        rows = session.exec(
            select(SystemConfig).where(SystemConfig.key.in_(keys_needed))
        ).all()
        for row in rows:
            try:
                if row.key in ("yolo_interval", "yolo_infer_scale", "yolo_high_threshold",
                               "yolo_low_threshold", "alert_cooldown"):
                    defaults[row.key] = float(row.value)
                else:
                    defaults[row.key] = row.value
            except (ValueError, TypeError):
                pass
    defaults["yolo_infer_scale"] = max(0.2, min(1.0, defaults["yolo_infer_scale"]))
    return defaults


# ==================== 辅助：截图保存 ====================

def save_snapshot(frame, camera_id: int) -> str:
    """保存截图到 uploads/ 目录，返回 /static/xxx.jpg URL"""
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_name = f"fire_{camera_id}_{ts}.jpg"
    cv2.imwrite(os.path.join(UPLOADS_DIR, img_name), frame)
    return f"/static/{img_name}"


# ==================== 辅助：创建告警记录 ====================

def create_alert(image_url: str, confidence: float, camera_name: str,
                 status: str = "pending", llm_result: str = None) -> int:
    """在数据库中创建一条告警记录，返回 alert_id"""
    with Session(engine) as session:
        alert = Alert(
            image_path=image_url,
            yolo_confidence=confidence,
            camera_name=camera_name,
            status=status,
            llm_result=llm_result,
        )
        session.add(alert)
        session.commit()
        session.refresh(alert)
        return alert.id


# ==================== 辅助：YOLO 单次推理（在线程中执行） ====================

def run_yolo_inference(frame, infer_scale: float = 1.0):
    """
    执行一次 YOLO 推理并返回：
    - annotated_frame: 带框图像
    - highest_conf: 最高置信度（无目标时为 None）
    """
    h, w = frame.shape[:2]
    infer_scale = max(0.2, min(1.0, float(infer_scale)))

    infer_frame = frame
    if infer_scale < 0.999:
        infer_w = max(64, int(w * infer_scale))
        infer_h = max(64, int(h * infer_scale))
        infer_frame = cv2.resize(frame, (infer_w, infer_h), interpolation=cv2.INTER_AREA)

    results = model(infer_frame, verbose=False)
    result = results[0]
    annotated_frame = result.plot()
    if infer_scale < 0.999:
        # 推理分辨率与展示分辨率不同时，将带框图还原到原画面大小
        annotated_frame = cv2.resize(annotated_frame, (w, h), interpolation=cv2.INTER_LINEAR)
    highest_conf = float(result.boxes.conf.max()) if len(result.boxes) > 0 else None
    return annotated_frame, highest_conf


# ==================== 异步：大模型二次复核 ====================

async def call_llm_review(alert_id: int, image_url: str, confidence: float,
                          camera_name: str, config: dict):
    """
    异步调用大模型 API 对截图进行火灾复核。
    完成后更新 DB 中的 alert 状态，并通过 WebSocket 推送结果。
    此函数通过 asyncio.create_task 调度，不会阻塞视频流。
    """
    llm_url = config.get("llm_api_url", "")
    llm_key = config.get("llm_api_key", "")
    llm_model = config.get("llm_model", "qwen-vl-max")

    final_status = "pending_verify"
    llm_text = ""

    if llm_url and llm_key and llm_key != "sk-xxxxx":
        # ---------- 真实调用大模型 API ----------
        try:
            # 读取截图并转为 base64
            img_full_path = os.path.join(UPLOADS_DIR, os.path.basename(image_url))
            with open(img_full_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode("utf-8")

            payload = {
                "model": llm_model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
                            },
                            {
                                "type": "text",
                                "text": (
                                    "你是一个森林火灾检测专家。请分析这张图片，"
                                    "判断是否有真实的森林火灾（明火、浓烟）。"
                                    "请极简短回答，格式如下：\n"
                                    "判定结果：真实火灾 / 误报\n"
                                    "分析说明：<20个字以内说明原因>"
                                )
                            }
                        ]
                    }
                ],
                "max_tokens": 300,
            }

            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    llm_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {llm_key}",
                        "Content-Type": "application/json",
                    },
                )
                if resp.status_code != 200:
                    print(f"❌ LLM API ERROR {resp.status_code}: {resp.text}")
                resp.raise_for_status()
                data = resp.json()
                llm_text = data["choices"][0]["message"]["content"]

            # 解析判定结果（仅作为建议，不直接替代人工结论）
            if "真实火灾" in llm_text:
                llm_text = f"【AI建议】疑似真实火灾，需现场核实。\n{llm_text}"
            else:
                llm_text = f"【AI建议】疑似误报，仍需人工复核。\n{llm_text}"

            print(f"🤖 LLM review for Alert #{alert_id}: pending_verify")

        except httpx.HTTPStatusError as e:
            error_body = e.response.text if hasattr(e, 'response') else str(e)
            llm_text = f"API 状体码 {e.response.status_code} 报错详情: {error_body}"
            final_status = "pending_verify"
            print(f"❌ LLM API Http Error for Alert #{alert_id}: {error_body}")
        except Exception as e:
            llm_text = f"大模型调用内部错误: {e}"
            final_status = "pending_verify"  # 调用失败保持人工核实
            print(f"❌ LLM call failed for Alert #{alert_id}: {e}")
    else:
        # ---------- 未配置 LLM → 模拟返回 ----------
        llm_text = (
            f"[模拟] 大模型 {llm_model} 分析：YOLO 置信度 {confidence:.1%}，"
            "图像中存在疑似火焰/烟雾特征，建议人工复核。"
        )
        final_status = "pending_verify"  # 无真实 LLM 时保持人工核实
        print(f"🤖 LLM simulated for Alert #{alert_id} (API key not configured)")

    # ---------- 更新数据库 ----------
    broadcast_status = final_status
    with Session(engine) as session:
        alert = session.get(Alert, alert_id)
        if alert:
            alert.llm_result = llm_text
            # 若人工已处理，不覆盖人工状态；仅更新 AI 文本
            if alert.status in {"pending", "pending_verify"}:
                alert.status = final_status
            broadcast_status = alert.status
            session.add(alert)
            session.commit()

    # ---------- WebSocket 广播更新 ----------
    await ws_manager.broadcast({
        "id": alert_id,
        "camera_name": camera_name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "image_path": image_url,
        "yolo_confidence": confidence,
        "status": broadcast_status,
        "llm_result": llm_text,
    })


# ==================== 核心：逐帧生成器 ====================

async def generate_frames(camera_id: int):
    """
    为指定摄像头生成 MJPEG 帧流，带级联推理检测。
    视频始终以 ~30fps 输出；YOLO 仅按 yolo_interval 间隔抽帧运行。
    """
    # ---------- 1. 读取摄像头基本信息 ----------
    camera_name = f"Camera-{camera_id}"
    camera_enable_ai = True

    with Session(engine) as session:
        cam = session.get(Camera, camera_id)
        if cam:
            camera_name = cam.name
            camera_enable_ai = cam.enable_ai
        else:
            while True:
                err = np.zeros((480, 640, 3), dtype=np.uint8)
                cv2.putText(err, f"Camera {camera_id} Not Found",
                            (60, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                _, buf = cv2.imencode('.jpg', err)
                yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n'
                await asyncio.sleep(1)
            return

    # ---------- 2. 加载系统配置 ----------
    config = load_detection_config()
    last_config_load = time.time()

    # ---------- 3. 打开视频源 ----------
    video_path = DEMO_VIDEO
    print(f"📹 Camera [{camera_id}] {camera_name} → opening {video_path}")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Cannot open video: {video_path}")
        while True:
            err = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(err, "Video Source Unavailable",
                        (50, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
            _, buf = cv2.imencode('.jpg', err)
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buf.tobytes() + b'\r\n'
            await asyncio.sleep(1)
        return

    # ---------- 4. 逐帧推理主循环 ----------
    last_detect_time = 0.0  # 上次 YOLO 推理启动时间
    detect_task = None       # 后台 YOLO 推理任务
    detect_context = None    # 当前推理任务上下文（阈值、设备名等快照）

    while True:
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        now = time.time()

        # 每个检测周期同时刷新系统配置 + enable_ai 状态
        if now - last_config_load >= config["yolo_interval"]:
            config = load_detection_config()
            last_config_load = now
            with Session(engine) as session:
                cam_refresh = session.get(Camera, camera_id)
                if cam_refresh:
                    camera_enable_ai = cam_refresh.enable_ai

        # ---- 判断是否在冷却期 ----
        cooldown_until = camera_cooldowns.get(camera_id, 0)
        in_cooldown = now < cooldown_until

        # ---- 判断是否该执行 YOLO ----
        should_detect = (
            model is not None
            and camera_enable_ai
            and not in_cooldown
            and (now - last_detect_time) >= config["yolo_interval"]
        )

        # 有空闲任务且到达检测间隔时，启动后台 YOLO 推理（避免阻塞视频输出）
        if should_detect and (detect_task is None):
            last_detect_time = now
            detect_context = {
                "camera_name": camera_name,
                "config": config.copy(),
                "frame": frame.copy(),
                "started_at": now,
            }
            detect_task = asyncio.create_task(
                asyncio.to_thread(
                    run_yolo_inference,
                    frame.copy(),
                    detect_context["config"]["yolo_infer_scale"]
                )
            )

        output_frame = frame

        # 推理任务完成后再处理告警逻辑
        if detect_task is not None and detect_task.done():
            try:
                annotated_frame, highest_conf = detect_task.result()
                output_frame = annotated_frame

                if highest_conf is not None and detect_context is not None:
                    high_th = detect_context["config"]["yolo_high_threshold"]
                    low_th = detect_context["config"]["yolo_low_threshold"]
                    cooldown_sec = detect_context["config"]["alert_cooldown"]
                    detect_camera_name = detect_context["camera_name"]
                    detect_started_at = detect_context["started_at"]
                    detect_frame = detect_context["frame"]

                    if highest_conf >= high_th:
                        # ========== 高置信度：高危建议，进入人工核实 ==========
                        camera_cooldowns[camera_id] = detect_started_at + cooldown_sec
                        img_url = save_snapshot(detect_frame, camera_id)
                        alert_id = create_alert(
                            img_url, highest_conf, detect_camera_name,
                            status="pending_verify",
                            llm_result=f"【AI高危建议】YOLO 置信度 {highest_conf:.1%} ≥ {high_th:.0%}，建议优先现场核实。"
                        )
                        # 即时广播
                        asyncio.create_task(ws_manager.broadcast({
                            "id": alert_id,
                            "camera_name": detect_camera_name,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "image_path": img_url,
                            "yolo_confidence": highest_conf,
                            "status": "pending_verify",
                            "llm_result": f"【AI高危建议】YOLO 高置信度 ({highest_conf:.1%})，请立即现场核实。",
                        }))
                        print(f"🔥 HIGH-RISK Alert #{alert_id} [{detect_camera_name}] conf={highest_conf:.2f}")

                    elif highest_conf >= low_th:
                        # ========== 中置信度：存 pending_verify + 异步 LLM 复核 ==========
                        camera_cooldowns[camera_id] = detect_started_at + cooldown_sec
                        img_url = save_snapshot(detect_frame, camera_id)
                        alert_id = create_alert(
                            img_url, highest_conf, detect_camera_name,
                            status="pending_verify",
                            llm_result="正在调用大模型进行二次复核..."
                        )
                        # 先广播 pending 状态
                        asyncio.create_task(ws_manager.broadcast({
                            "id": alert_id,
                            "camera_name": detect_camera_name,
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "image_path": img_url,
                            "yolo_confidence": highest_conf,
                            "status": "pending_verify",
                            "llm_result": "正在调用大模型进行二次复核...",
                        }))
                        # 异步启动 LLM 复核（不阻塞视频流）
                        asyncio.create_task(
                            call_llm_review(alert_id, img_url, highest_conf, detect_camera_name, detect_context["config"])
                        )
                        print(f"🔍 LLM Review Alert #{alert_id} [{detect_camera_name}] conf={highest_conf:.2f}")
                    # else: < low_threshold → 忽略，不做任何操作
            except Exception as e:
                print(f"❌ YOLO async inference failed for camera {camera_id}: {e}")
            finally:
                detect_task = None
                detect_context = None

        # ---- 编码并输出 MJPEG 帧 ----
        _, buffer = cv2.imencode('.jpg', output_frame)
        yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n'
        await asyncio.sleep(0.033)  # ≈ 30 fps


# ==================== 路由 ====================

@router.get("/video/{camera_id}")
async def video_feed(camera_id: int):
    """动态获取指定摄像头的 YOLO 级联推理视频流（MJPEG）"""
    return StreamingResponse(
        generate_frames(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
