from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import inspect, text
from sqlmodel import Session, select

from app.database import engine, get_session
from app.models.admin import Announcement, SystemConfig, SystemLog
from app.models.user import User
from app.routers.auth import get_current_user, require_roles
from app.utils.security import get_password_hash

router = APIRouter(prefix="/api/admin", tags=["admin"])

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKUP_DIR = PROJECT_ROOT / "backups"
MEDIA_DIR = PROJECT_ROOT / "media"


def resolve_alarm_audio_path() -> Optional[Path]:
    for folder in (MEDIA_DIR, PROJECT_ROOT):
        if not folder.exists():
            continue
        files = sorted([p for p in folder.glob("*.m4a") if p.is_file()])
        if files:
            return files[0]
    return None

REQUIRED_CONFIGS = {
    "system_name": ("防火预警系统", "系统名称", "general"),
    "yolo_interval": ("2.0", "YOLO 检测间隔（秒）", "ai"),
    "yolo_infer_scale": ("0.6", "推理前缩放比例（0.2-1.0）", "ai"),
    "yolo_high_threshold": ("0.9", "高风险阈值（> 直接高风险）", "ai"),
    "yolo_low_threshold": ("0.4", "低风险阈值（< 直接低风险）", "ai"),
    "alert_cooldown": ("10", "同一路告警冷却（秒）", "ai"),
    "fire_dispatch_phone": ("119", "联动消防电话", "general"),
    "alert_sound": ("true", "告警声音提醒", "general"),
}


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "operator"


class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


class ConfigUpdate(BaseModel):
    value: str


class AnnouncementCreate(BaseModel):
    title: str
    content: str
    category: str = "notice"


class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    is_published: Optional[bool] = None


def ensure_required_configs(session: Session) -> None:
    existing = {row.key for row in session.exec(select(SystemConfig)).all()}
    missing = []
    for key, (value, label, group) in REQUIRED_CONFIGS.items():
        if key not in existing:
            missing.append(SystemConfig(key=key, value=value, label=label, group=group))
    if missing:
        session.add_all(missing)
        session.commit()


def get_float_config(session: Session, key: str, fallback: float) -> float:
    row = session.exec(select(SystemConfig).where(SystemConfig.key == key)).first()
    if not row:
        return fallback
    try:
        return float(row.value)
    except (TypeError, ValueError):
        return fallback


def get_bool_config(session: Session, key: str, fallback: bool) -> bool:
    row = session.exec(select(SystemConfig).where(SystemConfig.key == key)).first()
    if not row:
        return fallback
    value = (row.value or "").strip().lower()
    if value in {"true", "1", "yes", "on"}:
        return True
    if value in {"false", "0", "no", "off"}:
        return False
    return fallback


def validate_config_value(session: Session, key: str, raw_value: str) -> None:
    numeric_rules = {
        "yolo_interval": (0.5, 10.0),
        "yolo_infer_scale": (0.2, 1.0),
        "yolo_low_threshold": (0.1, 0.8),
        "yolo_high_threshold": (0.5, 0.99),
        "alert_cooldown": (3.0, 120.0),
    }

    if key in numeric_rules:
        lo, hi = numeric_rules[key]
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail=f"{key} must be numeric")
        if not (lo <= value <= hi):
            raise HTTPException(status_code=400, detail=f"{key} out of range [{lo}, {hi}]")

    if key == "alert_sound":
        value = (raw_value or "").strip().lower()
        if value not in {"true", "false", "1", "0", "yes", "no", "on", "off"}:
            raise HTTPException(status_code=400, detail="alert_sound must be boolean")

    if key == "yolo_low_threshold":
        high = get_float_config(session, "yolo_high_threshold", 0.9)
        if float(raw_value) >= high:
            raise HTTPException(status_code=400, detail="yolo_low_threshold must be lower than yolo_high_threshold")

    if key == "yolo_high_threshold":
        low = get_float_config(session, "yolo_low_threshold", 0.4)
        if float(raw_value) <= low:
            raise HTTPException(status_code=400, detail="yolo_high_threshold must be greater than yolo_low_threshold")


def format_size(num_bytes: int) -> str:
    value = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if value < 1024.0 or unit == "GB":
            return f"{value:.2f} {unit}"
        value /= 1024.0
    return f"{num_bytes} B"


def quote_identifier(name: str) -> str:
    safe = (name or "").replace("`", "``")
    return f"`{safe}`"


def sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, datetime):
        return "'" + value.strftime("%Y-%m-%d %H:%M:%S") + "'"
    if isinstance(value, bytes):
        return "X'" + value.hex() + "'"
    text_value = str(value).replace("\\", "\\\\").replace("'", "''")
    return f"'{text_value}'"


def dump_database_to_sql(session: Session) -> str:
    inspector = inspect(engine)
    dialect = engine.url.get_backend_name()
    table_names = inspector.get_table_names()

    lines: list[str] = []
    lines.append("-- Forest Fire database backup")
    lines.append(f"-- Created at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"-- Dialect: {dialect}")
    lines.append("")

    for table in table_names:
        q_table = quote_identifier(table)
        lines.append(f"-- Table: {table}")

        create_stmt = None
        if dialect == "mysql":
            row = session.exec(text(f"SHOW CREATE TABLE {q_table}")).first()
            if row and len(row) >= 2:
                create_stmt = row[1]
        elif dialect == "sqlite":
            row = session.exec(
                text("SELECT sql FROM sqlite_master WHERE type='table' AND name=:name"),
                {"name": table},
            ).first()
            if row and row[0]:
                create_stmt = row[0]

        if create_stmt:
            lines.append(f"DROP TABLE IF EXISTS {q_table};")
            lines.append(str(create_stmt).rstrip(";") + ";")

        columns = inspector.get_columns(table)
        column_names = [c["name"] for c in columns]
        if not column_names:
            lines.append("")
            continue

        rows = session.exec(text(f"SELECT * FROM {q_table}")).mappings().all()
        if rows:
            col_sql = ", ".join(quote_identifier(c) for c in column_names)
            for row in rows:
                vals = ", ".join(sql_literal(row.get(c)) for c in column_names)
                lines.append(f"INSERT INTO {q_table} ({col_sql}) VALUES ({vals});")

        lines.append("")

    return "\n".join(lines)


@router.get("/users")
def list_users(session: Session = Depends(get_session), current_user: User = Depends(require_roles("admin"))):
    users = session.exec(select(User).order_by(User.id)).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at,
        }
        for u in users
    ]


@router.post("/users")
def create_user(
    data: UserCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    existing = session.exec(select(User).where(User.username == data.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=data.username,
        hashed_password=get_password_hash(data.password),
        role=data.role,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"id": user.id, "username": user.username, "role": user.role}


@router.put("/users/{user_id}")
def update_user(
    user_id: int,
    data: UserUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for k, v in data.dict(exclude_unset=True).items():
        setattr(user, k, v)

    session.add(user)
    session.commit()
    return {"msg": "Updated"}


@router.get("/configs")
def list_configs(session: Session = Depends(get_session), current_user: User = Depends(require_roles("admin"))):
    ensure_required_configs(session)
    return session.exec(select(SystemConfig).order_by(SystemConfig.group, SystemConfig.id)).all()


@router.put("/configs/{key}")
def update_config(
    key: str,
    data: ConfigUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    ensure_required_configs(session)
    validate_config_value(session, key, data.value)
    config = session.exec(select(SystemConfig).where(SystemConfig.key == key)).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")

    config.value = data.value
    config.updated_at = datetime.utcnow()
    session.add(config)
    session.commit()
    session.refresh(config)
    return config


@router.get("/announcements")
def list_announcements(
    category: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    query = select(Announcement).order_by(Announcement.id)
    if category:
        query = query.where(Announcement.category == category)
    if current_user.role != "admin":
        query = query.where(Announcement.is_published.is_(True))
    return session.exec(query).all()


@router.post("/announcements")
def create_announcement(
    data: AnnouncementCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    ann = Announcement(**data.dict())
    session.add(ann)
    session.commit()
    session.refresh(ann)
    return ann


@router.put("/announcements/{ann_id}")
def update_announcement(
    ann_id: int,
    data: AnnouncementUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    ann = session.get(Announcement, ann_id)
    if not ann:
        raise HTTPException(status_code=404, detail="Not found")

    for k, v in data.dict(exclude_unset=True).items():
        setattr(ann, k, v)

    session.add(ann)
    session.commit()
    session.refresh(ann)
    return ann


@router.delete("/announcements/{ann_id}")
def delete_announcement(
    ann_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    ann = session.get(Announcement, ann_id)
    if not ann:
        raise HTTPException(status_code=404, detail="Not found")

    session.delete(ann)
    session.commit()
    return {"msg": "Deleted"}


@router.get("/logs")
def list_system_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    query = select(SystemLog).order_by(SystemLog.id)
    total = len(session.exec(select(SystemLog)).all())
    logs = session.exec(query.offset((page - 1) * size).limit(size)).all()
    return {"total": total, "items": logs}


@router.post("/backup")
def backup_database(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    sql_text = dump_database_to_sql(session)
    filename = f"forest_fire_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
    target = BACKUP_DIR / filename
    target.write_text(sql_text, encoding="utf-8")

    return {
        "msg": "备份成功",
        "filename": filename,
        "size": format_size(target.stat().st_size),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "download_url": f"/api/admin/backup/download/{filename}",
    }


@router.get("/backup/download/{filename}")
def download_backup(
    filename: str,
    current_user: User = Depends(require_roles("admin")),
):
    safe_name = Path(filename).name
    file_path = BACKUP_DIR / safe_name
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Backup file not found")
    return FileResponse(
        path=file_path,
        media_type="application/sql",
        filename=safe_name,
    )


@router.get("/public/system-name")
def get_public_system_name(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ensure_required_configs(session)
    rows = session.exec(
        select(SystemConfig).where(
            SystemConfig.key.in_(
                [
                    "system_name",
                    "fire_dispatch_phone",
                    "yolo_high_threshold",
                    "yolo_low_threshold",
                    "alert_sound",
                ]
            )
        )
    ).all()
    values = {r.key: (r.value or "").strip() for r in rows}

    try:
        high = float(values.get("yolo_high_threshold") or 0.9)
    except ValueError:
        high = 0.9
    try:
        low = float(values.get("yolo_low_threshold") or 0.4)
    except ValueError:
        low = 0.4

    alarm_audio_path = resolve_alarm_audio_path()

    return {
        "system_name": values.get("system_name") or "防火预警系统",
        "fire_dispatch_phone": values.get("fire_dispatch_phone") or "119",
        "yolo_high_threshold": high,
        "yolo_low_threshold": low,
        "alert_sound": get_bool_config(session, "alert_sound", True),
        "alarm_audio_url": "/api/admin/public/alarm-audio" if alarm_audio_path else None,
    }


@router.get("/public/alarm-audio")
def get_alarm_audio():
    alarm_audio_path = resolve_alarm_audio_path()
    if not alarm_audio_path:
        raise HTTPException(status_code=404, detail="Alarm audio not found")
    return FileResponse(path=alarm_audio_path, media_type="audio/mp4", filename=alarm_audio_path.name)
