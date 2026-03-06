from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime


class SystemConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    key: str = Field(index=True, unique=True)
    value: str = Field(default="")
    label: str = Field(default="")
    group: str = Field(default="general")  # general / ai / llm
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Announcement(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str = Field(default="")
    category: str = Field(default="notice")  # notice / sop
    is_published: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SystemLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user: str = Field(default="")
    action: str = Field(default="")
    detail: str = Field(default="")
    ip: str = Field(default="")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
