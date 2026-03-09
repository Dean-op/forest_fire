from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, desc, select

from app.database import get_session
from app.models.alert import Alert
from app.models.supervisor import Camera, CameraLog, CaptureConfig, ShiftLog
from app.models.user import User
from app.routers.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/supervisor", tags=["supervisor"])


@router.get("/stats")
def get_stats(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    all_alerts = session.exec(select(Alert)).all()

    def is_true_fire(status: str) -> bool:
        return status in {"confirmed", "verified_true", "dispatched", "resolved"}

    def is_false_alarm(status: str) -> bool:
        return status in {"false_alarm", "verified_false", "archived_low"}

    def is_pending(status: str) -> bool:
        return status in {"pending", "pending_verify", "reviewing_llm"}

    total = len(all_alerts)
    confirmed = len([a for a in all_alerts if is_true_fire(a.status)])
    false_alarm = len([a for a in all_alerts if is_false_alarm(a.status)])
    pending = len([a for a in all_alerts if is_pending(a.status)])

    cameras = session.exec(select(Camera)).all()
    total_cameras = len(cameras)
    online_cameras = len([c for c in cameras if c.status == "online"])

    trend = []
    for i in range(6, -1, -1):
        day = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        day_end = day + timedelta(days=1)
        day_alerts = [a for a in all_alerts if day <= a.timestamp < day_end]
        trend.append(
            {
                "date": day.strftime("%m-%d"),
                "total": len(day_alerts),
                "confirmed": len([a for a in day_alerts if is_true_fire(a.status)]),
                "false_alarm": len([a for a in day_alerts if is_false_alarm(a.status)]),
            }
        )

    hourly = [0] * 24
    for a in all_alerts:
        hourly[a.timestamp.hour] += 1

    conf_bins = {"0.6-0.7": 0, "0.7-0.8": 0, "0.8-0.9": 0, "0.9-1.0": 0}
    for a in all_alerts:
        c = float(a.yolo_confidence or 0.0)
        if c < 0.7:
            conf_bins["0.6-0.7"] += 1
        elif c < 0.8:
            conf_bins["0.7-0.8"] += 1
        elif c < 0.9:
            conf_bins["0.8-0.9"] += 1
        else:
            conf_bins["0.9-1.0"] += 1

    camera_list = [{"name": c.name, "location": c.location, "status": c.status} for c in cameras]

    recent = session.exec(select(Alert).order_by(desc(Alert.timestamp)).limit(5)).all()
    recent_alerts = [
        {
            "id": a.id,
            "timestamp": a.timestamp.strftime("%m-%d %H:%M"),
            "confidence": a.yolo_confidence,
            "status": a.status,
        }
        for a in recent
    ]

    avg_conf = round(sum(float(a.yolo_confidence or 0.0) for a in all_alerts) / total, 2) if total else 0
    processed = confirmed + false_alarm
    accuracy = round(confirmed / processed * 100, 1) if processed else 0

    return {
        "total_alerts": total,
        "confirmed": confirmed,
        "false_alarm": false_alarm,
        "pending": pending,
        "total_cameras": total_cameras,
        "online_cameras": online_cameras,
        "online_rate": round(online_cameras / total_cameras * 100, 1) if total_cameras else 0,
        "avg_confidence": avg_conf,
        "accuracy": accuracy,
        "trend": trend,
        "hourly": hourly,
        "confidence_distribution": conf_bins,
        "camera_list": camera_list,
        "recent_alerts": recent_alerts,
    }


class CameraCreate(BaseModel):
    name: str
    rtsp_url: str = ""
    location: str = ""
    status: str = "online"
    enable_ai: bool = True


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    rtsp_url: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    enable_ai: Optional[bool] = None


@router.get("/cameras")
def list_cameras(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return session.exec(select(Camera).order_by(Camera.id)).all()


@router.post("/cameras")
def create_camera(
    data: CameraCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("supervisor", "admin")),
):
    camera = Camera(**data.dict())
    session.add(camera)
    session.commit()
    session.refresh(camera)
    return camera


@router.put("/cameras/{camera_id}")
def update_camera(
    camera_id: int,
    data: CameraUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("supervisor", "admin")),
):
    camera = session.get(Camera, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    for k, v in data.dict(exclude_unset=True).items():
        setattr(camera, k, v)

    session.add(camera)
    session.commit()
    session.refresh(camera)
    return camera


@router.delete("/cameras/{camera_id}")
def delete_camera(
    camera_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("supervisor", "admin")),
):
    camera = session.get(Camera, camera_id)
    if not camera:
        raise HTTPException(status_code=404, detail="Camera not found")

    session.delete(camera)
    session.commit()
    return {"msg": "Deleted"}


@router.get("/cameras/{camera_id}/logs")
def get_camera_logs(
    camera_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("supervisor", "admin")),
):
    return session.exec(select(CameraLog).where(CameraLog.camera_id == camera_id).order_by(desc(CameraLog.timestamp))).all()


class CaptureConfigUpdate(BaseModel):
    enable_capture: Optional[bool] = None
    capture_interval: Optional[int] = None
    save_original: Optional[bool] = None


@router.get("/capture-config")
def get_capture_config(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("supervisor", "admin")),
):
    return session.exec(select(CaptureConfig)).all()


@router.put("/capture-config/{config_id}")
def update_capture_config(
    config_id: int,
    data: CaptureConfigUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("supervisor", "admin")),
):
    config = session.get(CaptureConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    for k, v in data.dict(exclude_unset=True).items():
        setattr(config, k, v)
    config.updated_at = datetime.utcnow()

    session.add(config)
    session.commit()
    session.refresh(config)
    return config


class ShiftLogCreate(BaseModel):
    operator: str
    shift_time: str
    content: str


@router.get("/shift-logs")
def list_shift_logs(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("supervisor", "admin")),
):
    return session.exec(select(ShiftLog).order_by(desc(ShiftLog.created_at))).all()


@router.post("/shift-logs")
def create_shift_log(
    data: ShiftLogCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("supervisor", "admin")),
):
    log = ShiftLog(**data.dict())
    session.add(log)
    session.commit()
    session.refresh(log)
    return log


@router.delete("/shift-logs/{log_id}")
def delete_shift_log(
    log_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("supervisor", "admin")),
):
    log = session.get(ShiftLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="Shift log not found")

    session.delete(log)
    session.commit()
    return {"msg": "Deleted"}
