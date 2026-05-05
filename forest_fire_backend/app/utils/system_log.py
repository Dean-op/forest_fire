from typing import Optional

from fastapi import Request
from sqlmodel import Session

from app.models.admin import SystemLog
from app.models.user import User


def get_request_ip(request: Optional[Request]) -> str:
    if request is None:
        return ""

    forwarded_for = (request.headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if forwarded_for:
        return forwarded_for

    if request.client and request.client.host:
        return request.client.host

    return ""


def write_system_log(
    session: Session,
    *,
    user: str,
    action: str,
    detail: str = "",
    ip: str = "",
) -> SystemLog:
    log = SystemLog(
        user=(user or "").strip()[:64],
        action=(action or "").strip()[:128],
        detail=(detail or "").strip(),
        ip=(ip or "").strip()[:64],
    )
    session.add(log)
    return log


def log_user_action(
    session: Session,
    *,
    current_user: Optional[User],
    action: str,
    detail: str = "",
    request: Optional[Request] = None,
) -> SystemLog:
    return write_system_log(
        session,
        user=current_user.username if current_user else "anonymous",
        action=action,
        detail=detail,
        ip=get_request_ip(request),
    )
