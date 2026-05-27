from __future__ import annotations

import os
from pathlib import Path
import sys

from sqlmodel import Session, SQLModel, create_engine, select
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")

from app.models.admin import Announcement, SystemConfig, SystemLog
from app.models.alert import Alert
from app.models.supervisor import Camera, CameraLog, CaptureConfig, ShiftLog
from app.models.user import User


MODELS = [
    User,
    Alert,
    SystemConfig,
    Announcement,
    SystemLog,
    Camera,
    CameraLog,
    CaptureConfig,
    ShiftLog,
]


def main() -> None:
    source_url = os.environ["DATABASE_URL"]
    target_path = BASE_DIR / "storage" / "forest_fire_archive.db"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_url = f"sqlite:///{target_path.as_posix()}"

    source_engine = create_engine(source_url, echo=False)
    target_engine = create_engine(target_url, echo=False)

    SQLModel.metadata.drop_all(target_engine)
    SQLModel.metadata.create_all(target_engine)

    copied_counts: dict[str, int] = {}

    with Session(source_engine) as source_session, Session(target_engine) as target_session:
        for model in MODELS:
            rows = source_session.exec(select(model)).all()
            for row in rows:
                payload = row.model_dump()
                target_session.add(model(**payload))
            copied_counts[model.__name__] = len(rows)
        target_session.commit()

    print(f"Created SQLite archive at: {target_path}")
    for name, count in copied_counts.items():
        print(f"{name}: {count}")


if __name__ == "__main__":
    main()
