from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime


class Camera(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    rtsp_url: str = Field(default="")
    location: str = Field(default="")
    status: str = Field(default="online")  # online / offline
    enable_ai: bool = Field(default=True)  # 是否开启 YOLO 检测
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CameraLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    camera_id: int = Field(foreign_key="camera.id")
    event: str = Field(default="")  # 如 "掉线" / "恢复"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CaptureConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    camera_id: Optional[int] = Field(default=None)
    enable_capture: bool = Field(default=True)
    capture_interval: int = Field(default=5, description="抓拍间隔(秒)")
    save_original: bool = Field(default=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ShiftLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    operator: str = Field(default="")
    shift_time: str = Field(default="")
    content: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)
