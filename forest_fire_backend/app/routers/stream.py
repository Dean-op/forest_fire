"""
视频流路由：YOLO + LLM 两阶段风险分级

规则（全部可在系统参数配置）：
1) YOLO置信度 > yolo_high_threshold: 直接高风险，进入 operator 任务队列。
2) YOLO置信度 < yolo_low_threshold: 直接低风险，静默归档（不推送 operator）。
3) 其余区间: 进入 LLM 二次复核，LLM 给出高/中/低风险。
   - 高/中: 进入 operator 任务队列
   - 低: 静默归档
"""

import asyncio
import base64
import os
import time
from datetime import datetime
from pathlib import Path

import cv2
import httpx
import numpy as np
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from ultralytics import YOLO

from app.database import engine
from app.models.admin import SystemConfig
from app.models.alert import Alert
from app.models.supervisor import Camera
from app.routers.ws import ws_manager

router = APIRouter(prefix="/api/stream", tags=["stream"])

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEMO_VIDEO = str(BASE_DIR / "demo.mp4")
MODEL_PATH = str(BASE_DIR / "app" / "models" / "best.pt")
UPLOADS_DIR = str(BASE_DIR / "uploads")

model = None
try:
    if os.path.exists(MODEL_PATH):
        model = YOLO(MODEL_PATH)
        print(f"YOLO model loaded from {MODEL_PATH}")
    else:
        print(f"YOLO model not found at {MODEL_PATH}")
except Exception as e:
    print(f"Error loading YOLO model: {e}")

# {camera_id: unix_ts}
camera_cooldowns: dict[int, float] = {}


def load_detection_config() -> dict:
    defaults = {
        "yolo_interval": 2.0,
        "yolo_infer_scale": 0.6,
        "yolo_high_threshold": 0.9,
        "yolo_low_threshold": 0.4,
        "alert_cooldown": 10.0,
        "llm_api_url": "",
        "llm_api_key": "",
        "llm_model": "qwen-vl-max",
    }

    keys = list(defaults.keys())
    with Session(engine) as session:
        rows = session.exec(select(SystemConfig).where(SystemConfig.key.in_(keys))).all()
        for row in rows:
            try:
                if row.key in {"yolo_interval", "yolo_infer_scale", "yolo_high_threshold", "yolo_low_threshold", "alert_cooldown"}:
                    defaults[row.key] = float(row.value)
                else:
                    defaults[row.key] = row.value
            except (TypeError, ValueError):
                pass

    defaults["yolo_infer_scale"] = max(0.2, min(1.0, float(defaults["yolo_infer_scale"])))
    defaults["yolo_high_threshold"] = max(0.5, min(0.99, float(defaults["yolo_high_threshold"])))
    defaults["yolo_low_threshold"] = max(0.1, min(0.8, float(defaults["yolo_low_threshold"])))
    if defaults["yolo_low_threshold"] >= defaults["yolo_high_threshold"]:
        defaults["yolo_low_threshold"] = max(0.1, defaults["yolo_high_threshold"] - 0.05)

    return defaults


def save_snapshot(frame, camera_id: int) -> str:
    os.makedirs(UPLOADS_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_name = f"fire_{camera_id}_{ts}.jpg"
    cv2.imwrite(os.path.join(UPLOADS_DIR, img_name), frame)
    return f"/static/{img_name}"


def create_alert(
    image_url: str,
    confidence: float,
    camera_name: str,
    status: str,
    llm_result: str,
) -> int:
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


def run_yolo_inference(frame, infer_scale: float = 1.0):
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
        annotated_frame = cv2.resize(annotated_frame, (w, h), interpolation=cv2.INTER_LINEAR)

    highest_conf = float(result.boxes.conf.max()) if len(result.boxes) > 0 else None
    return annotated_frame, highest_conf


def parse_llm_risk(text: str) -> str:
    content = text or ""
    if "高风险" in content:
        return "high"
    if "中风险" in content:
        return "medium"
    if "低风险" in content:
        return "low"
    return "medium"


def risk_to_status(risk: str) -> str:
    return "pending_verify" if risk in {"high", "medium"} else "archived_low"


def risk_label_zh(risk: str) -> str:
    return {"high": "高风险", "medium": "中风险", "low": "低风险"}.get(risk, "中风险")


async def call_llm_review(alert_id: int, image_url: str, confidence: float, camera_name: str, config: dict):
    llm_url = config.get("llm_api_url", "")
    llm_key = config.get("llm_api_key", "")
    llm_model = config.get("llm_model", "qwen-vl-max")

    llm_text = ""
    risk = "medium"

    if llm_url and llm_key and llm_key != "sk-xxxxx":
        try:
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
                                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"},
                            },
                            {
                                "type": "text",
                                "text": (
                                    "你是森林火灾风险分级专家。"
                                    "请仅按下述格式输出，不要输出额外内容。\n"
                                    "风险级别: 高风险 或 中风险 或 低风险\n"
                                    "处置建议: 20字以内"
                                ),
                            },
                        ],
                    }
                ],
                "max_tokens": 200,
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
                resp.raise_for_status()
                data = resp.json()
                llm_text = data["choices"][0]["message"]["content"]

            risk = parse_llm_risk(llm_text)

        except Exception as e:
            # LLM失败时，保守处理为中风险，避免漏报
            risk = "medium"
            llm_text = f"LLM调用失败，按中风险兜底处理：{e}"

    else:
        # 未配置LLM：按置信度做本地保守分级模拟
        if confidence >= 0.75:
            risk = "medium"
        else:
            risk = "low"
        llm_text = f"[模拟LLM] 风险级别: {risk_label_zh(risk)}；建议人工复核。"

    final_status = risk_to_status(risk)
    llm_text = f"[风险级别:{risk_label_zh(risk)}] {llm_text}"

    broadcast = False
    with Session(engine) as session:
        alert = session.get(Alert, alert_id)
        if alert:
            alert.llm_result = llm_text
            # 只在未被人工处理时更新状态
            if alert.status in {"reviewing_llm", "pending", "pending_verify"}:
                alert.status = final_status
            session.add(alert)
            session.commit()
            broadcast = alert.status == "pending_verify"
            final_status = alert.status

    # 仅高/中风险通知前端；低风险静默归档
    if broadcast:
        await ws_manager.broadcast(
            {
                "id": alert_id,
                "camera_name": camera_name,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "image_path": image_url,
                "yolo_confidence": confidence,
                "status": final_status,
                "llm_result": llm_text,
            }
        )


async def generate_frames(camera_id: int):
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
                cv2.putText(err, f"Camera {camera_id} Not Found", (60, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
                _, buf = cv2.imencode(".jpg", err)
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"
                await asyncio.sleep(1)
            return

    config = load_detection_config()
    last_config_load = time.time()

    cap = cv2.VideoCapture(DEMO_VIDEO)
    if not cap.isOpened():
        while True:
            err = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(err, "Video Source Unavailable", (50, 220), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 255), 2)
            _, buf = cv2.imencode(".jpg", err)
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"
            await asyncio.sleep(1)
        return

    last_detect_time = 0.0
    detect_task = None
    detect_context = None

    while True:
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            continue

        now = time.time()

        if now - last_config_load >= config["yolo_interval"]:
            config = load_detection_config()
            last_config_load = now
            with Session(engine) as session:
                cam_refresh = session.get(Camera, camera_id)
                if cam_refresh:
                    camera_enable_ai = cam_refresh.enable_ai

        in_cooldown = now < camera_cooldowns.get(camera_id, 0)
        should_detect = (
            model is not None
            and camera_enable_ai
            and not in_cooldown
            and (now - last_detect_time) >= config["yolo_interval"]
        )

        if should_detect and detect_task is None:
            last_detect_time = now
            detect_context = {
                "camera_name": camera_name,
                "config": config.copy(),
                "frame": frame.copy(),
                "started_at": now,
            }
            detect_task = asyncio.create_task(
                asyncio.to_thread(run_yolo_inference, frame.copy(), detect_context["config"]["yolo_infer_scale"])
            )

        output_frame = frame

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

                    camera_cooldowns[camera_id] = detect_started_at + cooldown_sec
                    img_url = save_snapshot(detect_frame, camera_id)

                    if highest_conf > high_th:
                        # 直接高风险
                        llm_text = (
                            f"[风险级别:高风险] YOLO置信度 {highest_conf:.1%} > {high_th:.0%}，"
                            "直接判定高风险并进入人工处置。"
                        )
                        alert_id = create_alert(
                            img_url,
                            highest_conf,
                            detect_camera_name,
                            status="pending_verify",
                            llm_result=llm_text,
                        )
                        asyncio.create_task(
                            ws_manager.broadcast(
                                {
                                    "id": alert_id,
                                    "camera_name": detect_camera_name,
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    "image_path": img_url,
                                    "yolo_confidence": highest_conf,
                                    "status": "pending_verify",
                                    "llm_result": llm_text,
                                }
                            )
                        )

                    elif highest_conf < low_th:
                        # 直接低风险：静默归档，不通知operator
                        llm_text = (
                            f"[风险级别:低风险] YOLO置信度 {highest_conf:.1%} < {low_th:.0%}，"
                            "自动静默归档。"
                        )
                        create_alert(
                            img_url,
                            highest_conf,
                            detect_camera_name,
                            status="archived_low",
                            llm_result=llm_text,
                        )

                    else:
                        # 中间区间：先入LLM复核队列，复核后再决定是否推送operator
                        alert_id = create_alert(
                            img_url,
                            highest_conf,
                            detect_camera_name,
                            status="reviewing_llm",
                            llm_result=f"[风险级别:待复核] YOLO置信度 {highest_conf:.1%} 进入大模型二次复核。",
                        )
                        asyncio.create_task(
                            call_llm_review(
                                alert_id,
                                img_url,
                                highest_conf,
                                detect_camera_name,
                                detect_context["config"],
                            )
                        )

            except Exception as e:
                print(f"YOLO async inference failed for camera {camera_id}: {e}")
            finally:
                detect_task = None
                detect_context = None

        _, buffer = cv2.imencode(".jpg", output_frame)
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buffer.tobytes() + b"\r\n"
        await asyncio.sleep(0.033)


@router.get("/video/{camera_id}")
async def video_feed(camera_id: int):
    return StreamingResponse(
        generate_frames(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
