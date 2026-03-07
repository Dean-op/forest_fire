from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime


class Alert(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.now)
    image_path: str = Field(description="截图保存的相对路径，如 /static/fire_123.jpg")
    yolo_confidence: float = Field(default=0.0, description="YOLO 检测置信度")
    camera_name: Optional[str] = Field(default=None, description="产生告警的摄像头名称")
    llm_result: Optional[str] = Field(default=None, description="大语言模型复核结果")
    status: str = Field(default="pending", description="状态: pending待处理, confirmed真实火灾, false_alarm误报")
    remark: Optional[str] = Field(default=None, description="操作员处理备注")
