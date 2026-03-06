from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, desc
from typing import Optional
from pydantic import BaseModel
from datetime import datetime

from app.database import get_session
from app.models.user import User
from app.models.admin import SystemConfig, Announcement, SystemLog
from app.routers.auth import get_current_user
from app.utils.security import get_password_hash

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ===================== 用户管理 =====================

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "operator"

class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/users")
def list_users(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    users = session.exec(select(User).order_by(User.id)).all()
    return [{"id": u.id, "username": u.username, "role": u.role, "is_active": u.is_active, "created_at": u.created_at} for u in users]


@router.post("/users")
def create_user(data: UserCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    existing = session.exec(select(User).where(User.username == data.username)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(username=data.username, hashed_password=get_password_hash(data.password), role=data.role)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"id": user.id, "username": user.username, "role": user.role}


@router.put("/users/{user_id}")
def update_user(user_id: int, data: UserUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for k, v in data.dict(exclude_unset=True).items():
        setattr(user, k, v)
    session.add(user)
    session.commit()
    return {"msg": "Updated"}


# ===================== 系统参数配置 =====================

class ConfigUpdate(BaseModel):
    value: str

@router.get("/configs")
def list_configs(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    configs = session.exec(select(SystemConfig).order_by(SystemConfig.group, SystemConfig.id)).all()
    return configs


@router.put("/configs/{key}")
def update_config(key: str, data: ConfigUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    config = session.exec(select(SystemConfig).where(SystemConfig.key == key)).first()
    if not config:
        raise HTTPException(status_code=404, detail="Config not found")
    config.value = data.value
    config.updated_at = datetime.utcnow()
    session.add(config)
    session.commit()
    session.refresh(config)
    return config


# ===================== SOP / 公告管理 =====================

class AnnouncementCreate(BaseModel):
    title: str
    content: str
    category: str = "notice"

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    is_published: Optional[bool] = None


@router.get("/announcements")
def list_announcements(
    category: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    query = select(Announcement).order_by(desc(Announcement.created_at))
    if category:
        query = query.where(Announcement.category == category)
    return session.exec(query).all()


@router.post("/announcements")
def create_announcement(data: AnnouncementCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    ann = Announcement(**data.dict())
    session.add(ann)
    session.commit()
    session.refresh(ann)
    return ann


@router.put("/announcements/{ann_id}")
def update_announcement(ann_id: int, data: AnnouncementUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
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
def delete_announcement(ann_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    ann = session.get(Announcement, ann_id)
    if not ann:
        raise HTTPException(status_code=404, detail="Not found")
    session.delete(ann)
    session.commit()
    return {"msg": "Deleted"}


# ===================== 系统日志 =====================

@router.get("/logs")
def list_system_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    query = select(SystemLog).order_by(desc(SystemLog.timestamp))
    total = len(session.exec(select(SystemLog)).all())
    logs = session.exec(query.offset((page - 1) * size).limit(size)).all()
    return {"total": total, "items": logs}


# ===================== 数据库备份（模拟） =====================

@router.post("/backup")
async def backup_database(current_user: User = Depends(get_current_user)):
    """模拟数据库备份操作"""
    import asyncio
    await asyncio.sleep(2)  # 模拟耗时
    return {
        "msg": "备份成功",
        "filename": f"forest_fire_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
        "size": "12.3 MB"
    }
