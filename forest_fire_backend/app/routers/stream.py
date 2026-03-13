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
import re
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
MEDIA_DIR = BASE_DIR / "media"
MODEL_PATH = str(BASE_DIR / "app" / "models" / "best.pt")
UPLOADS_DIR = str(BASE_DIR / "uploads")


def resolve_demo_video_path() -> str:
    for candidate in (MEDIA_DIR / "demo.mp4", BASE_DIR / "demo.mp4"):
        if candidate.exists():
            return str(candidate)
    return str(MEDIA_DIR / "demo.mp4")


DEMO_VIDEO = resolve_demo_video_path()

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


def create_video_capture(video_source: object) -> cv2.VideoCapture:
    cap = cv2.VideoCapture()
    # Reduce blocking time on RTSP/network sources to avoid freezing the API event loop.
    if hasattr(cv2, "CAP_PROP_OPEN_TIMEOUT_MSEC"):
        cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 2500)
    if hasattr(cv2, "CAP_PROP_READ_TIMEOUT_MSEC"):
        cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 2000)
    cap.open(video_source)
    return cap


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


def parse_llm_verdict(text: str) -> str:
    content = text or ""
    normalized = content.lower()
    # 优先识别误报，避免“非火灾”中的“火灾”造成误判。
    if any(token in content for token in ["误报", "非火灾", "非火情"]) or "false_alarm" in normalized:
        return "false_alarm"
    if any(token in content for token in ["真实火灾", "真火", "存在火情"]) or "true_fire" in normalized:
        return "true_fire"
    # 兼容旧版风险分级输出。
    if "低风险" in content:
        return "false_alarm"
    if "高风险" in content or "中风险" in content:
        return "true_fire"
    return "unknown"


def verdict_to_status(verdict: str) -> str:
    return "pending_verify" if verdict == "true_fire" else "archived_low"


def verdict_label_zh(verdict: str) -> str:
    return {"true_fire": "真实火灾", "false_alarm": "误报"}.get(verdict, "待复核")


def verdict_risk_label_zh(verdict: str) -> str:
    return {"true_fire": "高风险", "false_alarm": "低风险"}.get(verdict, "待复核")


def extract_llm_suggestion(text: str) -> str:
    content = (text or "").strip()
    if not content:
        return ""
    match = re.search(r"处置建议\s*[:：]\s*(.+)", content)
    if match:
        return match.group(1).strip().splitlines()[0][:80]
    return content.splitlines()[0][:80]


async def call_llm_review(alert_id: int, image_url: str, confidence: float, camera_name: str, config: dict):
    llm_url = config.get("llm_api_url", "")
    llm_key = config.get("llm_api_key", "")
    llm_model = config.get("llm_model", "qwen-vl-max")

    llm_text = ""
    verdict = "unknown"
    suggestion = ""

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
                                    "你是森林火灾复核专家。"
                                    "请仅输出两行，不要输出其他内容。\n"
                                    "复核结论: 真实火灾 或 误报\n"
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
                raw_llm_text = data["choices"][0]["message"]["content"]

            verdict = parse_llm_verdict(raw_llm_text)
            suggestion = extract_llm_suggestion(raw_llm_text)
            if verdict == "unknown":
                # 模型输出不合规时按火灾兜底，避免漏报。
                verdict = "true_fire"
                if not suggestion:
                    suggestion = "模型输出不规范，已转人工复核。"

        except Exception as e:
            verdict = "true_fire"
            suggestion = f"LLM调用失败，按火灾兜底并转人工复核：{e}"

    else:
        # 未配置LLM：按置信度做本地二分类模拟。
        if confidence >= 0.75:
            verdict = "true_fire"
            suggestion = "未配置LLM，按高疑似火情转人工复核。"
        else:
            verdict = "false_alarm"
            suggestion = "未配置LLM，判定疑似误报并归档。"

    final_status = verdict_to_status(verdict)
    llm_text = (
        f"复核结论: {verdict_label_zh(verdict)}\n"
        f"风险级别: {verdict_risk_label_zh(verdict)}\n"
        f"处置建议: {suggestion or '请人工复核。'}"
    )

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

    # 仅真实火灾通知前端；误报静默归档。
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


def resolve_video_source(configured_source: str) -> tuple[object, bool]:
    source = (configured_source or "").strip()
    if not source:
        return resolve_demo_video_path(), True

    aliases = {
        "demo": "demo.mp4",
        "demo.mp4": "demo.mp4",
        "firework": "firework.mp4",
        "firework.mp4": "firework.mp4",
        "fire": "\u706b\u707e.mp4",
        "fire.mp4": "\u706b\u707e.mp4",
        "\u706b\u707e.mp4": "\u706b\u707e.mp4",
        "sunset": "sunset.mp4",
        "sunset.mp4": "sunset.mp4",
    }
    source = aliases.get(source.lower(), source)

    lower_source = source.lower()
    if lower_source.startswith(("rtsp://", "rtsps://", "http://", "https://")):
        return source, False
    if source.isdigit():
        return int(source), False

    source_path = Path(source)
    if source_path.is_absolute():
        if source_path.exists():
            return str(source_path), True
        return resolve_demo_video_path(), True

    # Prefer media/ for local sample files, then fallback to backend root.
    candidates = [MEDIA_DIR / source_path, BASE_DIR / source_path]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate), True

    return resolve_demo_video_path(), True


def build_status_frame(text: str, size: tuple[int, int] = (640, 480)) -> bytes:
    width, height = size
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.putText(frame, text, (30, int(height * 0.5)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 220, 255), 2)
    _, buf = cv2.imencode(".jpg", frame)
    return b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + buf.tobytes() + b"\r\n"


async def generate_frames(camera_id: int):
    camera_name = f"Camera-{camera_id}"
    camera_enable_ai = True
    camera_source_config = ""

    with Session(engine) as session:
        cam = session.get(Camera, camera_id)
        if cam:
            camera_name = cam.name
            camera_enable_ai = cam.enable_ai
            camera_source_config = cam.rtsp_url or ""
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

    video_source, is_file_source = resolve_video_source(camera_source_config)
    cap = await asyncio.to_thread(create_video_capture, video_source)
    if not cap.isOpened():
        # Don't block forever on an unavailable source; keep pushing status frames.
        while True:
            yield build_status_frame(f"camera-{camera_id}: source unavailable")
            await asyncio.sleep(1)
            with Session(engine) as session:
                cam_refresh = session.get(Camera, camera_id)
                if cam_refresh:
                    camera_enable_ai = cam_refresh.enable_ai
                    new_source_config = (cam_refresh.rtsp_url or "").strip()
                    if new_source_config != (camera_source_config or "").strip():
                        camera_source_config = new_source_config
                        video_source, is_file_source = resolve_video_source(camera_source_config)
            cap = await asyncio.to_thread(create_video_capture, video_source)
            if cap.isOpened():
                break

    last_detect_time = 0.0
    detect_task = None
    detect_context = None

    try:
        while True:
            success, frame = await asyncio.to_thread(cap.read)
            if not success:
                if is_file_source:
                    await asyncio.to_thread(cap.set, cv2.CAP_PROP_POS_FRAMES, 0)
                else:
                    await asyncio.to_thread(cap.release)
                    # RTSP/device read failure: reconnect and return a placeholder frame
                    # to avoid browser hanging on an endless black panel.
                    yield build_status_frame(f"camera-{camera_id}: reconnecting stream")
                    await asyncio.sleep(0.8)
                    cap = await asyncio.to_thread(create_video_capture, video_source)
                continue

            now = time.time()

            if now - last_config_load >= config["yolo_interval"]:
                config = load_detection_config()
                last_config_load = now
                with Session(engine) as session:
                    cam_refresh = session.get(Camera, camera_id)
                    if cam_refresh:
                        camera_enable_ai = cam_refresh.enable_ai
                        new_source_config = (cam_refresh.rtsp_url or "").strip()
                        if new_source_config != (camera_source_config or "").strip():
                            camera_source_config = new_source_config
                            next_source, next_is_file_source = resolve_video_source(camera_source_config)
                            if next_source != video_source:
                                await asyncio.to_thread(cap.release)
                                cap = await asyncio.to_thread(create_video_capture, next_source)
                                video_source = next_source
                                is_file_source = next_is_file_source

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
                                "复核结论: 真实火灾\n"
                                "风险级别: 高风险\n"
                                f"处置建议: YOLO置信度 {highest_conf:.1%} 超过阈值 {high_th:.0%}，请立刻按 SOP1 处置。"
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
                                "复核结论: 误报\n"
                                "风险级别: 低风险\n"
                                f"处置建议: YOLO置信度 {highest_conf:.1%} 低于阈值 {low_th:.0%}，系统已自动归档。"
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
                                llm_result=f"复核结论: 待复核\n风险级别: 待复核\n处置建议: YOLO置信度 {highest_conf:.1%}，正在等待大模型复核。",
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
    finally:
        if detect_task is not None and not detect_task.done():
            detect_task.cancel()
        try:
            await asyncio.to_thread(cap.release)
        except Exception:
            pass


@router.get("/video/{camera_id}")
async def video_feed(camera_id: int):
    return StreamingResponse(
        generate_frames(camera_id),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )


