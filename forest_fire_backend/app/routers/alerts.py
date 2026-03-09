from datetime import datetime
from typing import Literal, Optional
import csv
import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlmodel import Session, desc, select

from app.database import get_session
from app.models.admin import SystemConfig
from app.models.alert import Alert
from app.models.user import User
from app.routers.auth import get_current_user, require_roles

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


WORKFLOW_STATUS_LABELS = {
    "pending": "待核实",
    "pending_verify": "待核实",
    "reviewing_llm": "LLM复核中",
    "confirmed": "已核实真实火灾",
    "verified_true": "已核实真实火灾",
    "false_alarm": "已核实误报",
    "verified_false": "已核实误报",
    "dispatched": "已联动消防",
    "resolved": "已处理",
    "archived_low": "低风险静默归档",
    "cancelled_pending": "已撤销待处置",
}

HIDDEN_FOR_OPERATOR = {"archived_low", "reviewing_llm"}
DELETABLE_STATUSES = {"verified_false", "false_alarm", "resolved", "archived_low", "cancelled_pending"}
CANCELLABLE_STATUSES = {"pending", "pending_verify"}


def expand_status_filter(status: str) -> set[str]:
    aliases = {
        "pending": {"pending", "pending_verify", "reviewing_llm"},
        "pending_verify": {"pending", "pending_verify"},
        "confirmed": {"confirmed", "verified_true", "dispatched", "resolved"},
        "false_alarm": {"false_alarm", "verified_false"},
        "operator_queue": {"pending", "pending_verify", "confirmed", "verified_true", "dispatched"},
        "done": {"resolved", "verified_false", "false_alarm", "archived_low", "cancelled_pending"},
        "low_archived": {"archived_low"},
        "cancelled_pending": {"cancelled_pending"},
    }
    return aliases.get(status, {status})


def append_remark(original: Optional[str], extra: Optional[str]) -> Optional[str]:
    if not extra:
        return original
    text = extra.strip()
    if not text:
        return original
    if not original:
        return text
    return f"{original}\n{text}"


def can_delete_alert(status: str) -> bool:
    return status in DELETABLE_STATUSES


def can_cancel_alert(status: str) -> bool:
    return status in CANCELLABLE_STATUSES


def get_float_config(session: Session, key: str, default: float) -> float:
    row = session.exec(select(SystemConfig).where(SystemConfig.key == key)).first()
    if not row:
        return default
    try:
        return float(row.value)
    except (TypeError, ValueError):
        return default


def get_text_config(session: Session, key: str, default: str) -> str:
    row = session.exec(select(SystemConfig).where(SystemConfig.key == key)).first()
    if not row:
        return default
    value = (row.value or "").strip()
    return value or default


class AlertProcess(BaseModel):
    status: str
    remark: Optional[str] = None


class AlertDispatch(BaseModel):
    contact: Optional[str] = None
    note: Optional[str] = None


class AlertResolve(BaseModel):
    remark: Optional[str] = None


class AlertCancel(BaseModel):
    reason: str


class AlertSOPExecute(BaseModel):
    sop_type: Literal["SOP1", "SOP2"]
    outcome: Optional[Literal["true_fire", "false_alarm"]] = None
    contact: Optional[str] = None
    note: Optional[str] = None


class BatchDeleteRequest(BaseModel):
    ids: list[int]


@router.get("")
def list_alerts(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    query = select(Alert).order_by(desc(Alert.timestamp))
    total_query = select(Alert)

    if status:
        values = expand_status_filter(status)
        query = query.where(Alert.status.in_(values))
        total_query = total_query.where(Alert.status.in_(values))

    if current_user.role == "operator":
        query = query.where(~Alert.status.in_(HIDDEN_FOR_OPERATOR))
        total_query = total_query.where(~Alert.status.in_(HIDDEN_FOR_OPERATOR))

    total = len(session.exec(total_query).all())
    alerts = session.exec(query.offset((page - 1) * size).limit(size)).all()
    return {"total": total, "items": alerts}


@router.put("/{alert_id}/process")
def process_alert(
    alert_id: int,
    data: AlertProcess,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("operator", "admin")),
):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if data.status == "confirmed":
        alert.status = "verified_true"
        result_note = f"【现场核实】真实火灾（{now_str}）"
    elif data.status == "false_alarm":
        alert.status = "verified_false"
        result_note = f"【现场核实】误报（{now_str}）"
    else:
        raise HTTPException(status_code=400, detail="status must be confirmed or false_alarm")

    alert.remark = append_remark(alert.remark, result_note)
    alert.remark = append_remark(alert.remark, data.remark)
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert


@router.put("/{alert_id}/execute-sop")
def execute_sop(
    alert_id: int,
    data: AlertSOPExecute,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("operator", "admin")),
):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.status in {"archived_low", "reviewing_llm", "verified_false", "false_alarm", "resolved", "cancelled_pending"}:
        raise HTTPException(status_code=400, detail="This alert is not executable for SOP")

    default_phone = get_text_config(session, "fire_dispatch_phone", "119")
    contact = (data.contact or "").strip() or default_phone
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if data.sop_type == "SOP1":
        alert.status = "resolved"
        remark = (
            f"【SOP1 已执行】{now_str} 完成人工视检，已联动消防（电话:{contact}），"
            "并完成内部调度。状态变更为已处理。"
        )
    else:
        outcome = data.outcome or "false_alarm"
        if outcome == "true_fire":
            alert.status = "resolved"
            remark = (
                f"【SOP2 已执行-真实火灾】{now_str} 完成现场复核为真实火灾，"
                f"已升级执行SOP1并联动消防（电话:{contact}）。状态变更为已处理。"
            )
        else:
            alert.status = "verified_false"
            remark = f"【SOP2 已执行-确认为误报】{now_str} 完成现场复核，确认误报并归档处理。"

    alert.remark = append_remark(alert.remark, remark)
    alert.remark = append_remark(alert.remark, data.note)

    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert


@router.put("/{alert_id}/dispatch")
def dispatch_fire_alert(
    alert_id: int,
    data: AlertDispatch,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("operator", "admin")),
):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    high_threshold = get_float_config(session, "yolo_high_threshold", 0.9)
    allow_direct_dispatch = (
        alert.status in {"pending", "pending_verify"}
        and float(alert.yolo_confidence or 0.0) > high_threshold
    )

    if alert.status not in {"verified_true", "confirmed", "dispatched"} and not allow_direct_dispatch:
        raise HTTPException(status_code=400, detail="Only verified or high-risk alerts can be dispatched")

    default_phone = get_text_config(session, "fire_dispatch_phone", "119")
    contact = (data.contact or "").strip() or default_phone

    alert.status = "dispatched"
    dispatch_msg = f"【联动消防】已通知林区消防队（{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}），电话：{contact}"
    if allow_direct_dispatch:
        dispatch_msg = (
            f"【高风险直联】YOLO置信度 {float(alert.yolo_confidence or 0.0):.1%} > {high_threshold:.0%}，允许直接联动。\n"
            f"{dispatch_msg}"
        )

    alert.remark = append_remark(alert.remark, dispatch_msg)
    alert.remark = append_remark(alert.remark, data.note)

    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert


@router.put("/{alert_id}/resolve")
def resolve_fire_alert(
    alert_id: int,
    data: AlertResolve,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("operator", "admin")),
):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.status not in {"dispatched", "verified_true", "confirmed", "resolved"}:
        raise HTTPException(status_code=400, detail="Only true-fire alerts can be marked resolved")

    alert.status = "resolved"
    alert.remark = append_remark(alert.remark, f"【处置上报】任务闭环（{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}）")
    alert.remark = append_remark(alert.remark, data.remark)

    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert


@router.put("/{alert_id}/cancel")
def cancel_alert(
    alert_id: int,
    data: AlertCancel,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if not can_cancel_alert(alert.status):
        raise HTTPException(status_code=400, detail="Only pending alerts can be cancelled")

    reason = (data.reason or "").strip()
    if not reason:
        raise HTTPException(status_code=400, detail="Cancel reason is required")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alert.status = "cancelled_pending"
    alert.remark = append_remark(alert.remark, f"【任务撤销】{now_str} {current_user.username}：{reason}")

    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert


@router.get("/export/csv")
def export_alerts_csv(
    status: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    query = select(Alert).order_by(desc(Alert.timestamp))
    if status:
        values = expand_status_filter(status)
        query = query.where(Alert.status.in_(values))

    if current_user.role == "operator":
        query = query.where(~Alert.status.in_(HIDDEN_FOR_OPERATOR))

    alerts = session.exec(query).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "时间", "YOLO置信度", "AI建议", "工作流状态", "备注", "截图路径"])
    for alert in alerts:
        writer.writerow([
            alert.id,
            alert.timestamp,
            alert.yolo_confidence,
            alert.llm_result,
            WORKFLOW_STATUS_LABELS.get(alert.status, alert.status),
            alert.remark,
            alert.image_path,
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=alerts_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"},
    )


@router.get("/{alert_id}")
def get_alert(
    alert_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if current_user.role == "operator" and alert.status in HIDDEN_FOR_OPERATOR:
        raise HTTPException(status_code=404, detail="Alert not found")

    return alert


@router.delete("/{alert_id}")
def delete_alert(
    alert_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if not can_delete_alert(alert.status):
        raise HTTPException(status_code=400, detail="Only closed/archived alerts can be deleted")

    session.delete(alert)
    session.commit()
    return {"msg": "Deleted", "id": alert_id}


@router.post("/batch-delete")
def batch_delete_alerts(
    data: BatchDeleteRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_roles("admin")),
):
    deleted = 0
    blocked: list[dict] = []
    not_found: list[int] = []

    for alert_id in data.ids:
        alert = session.get(Alert, alert_id)
        if not alert:
            not_found.append(alert_id)
            continue

        if not can_delete_alert(alert.status):
            blocked.append({"id": alert_id, "status": alert.status})
            continue

        session.delete(alert)
        deleted += 1

    session.commit()
    return {
        "msg": f"Deleted {deleted} alerts",
        "deleted": deleted,
        "blocked": blocked,
        "not_found": not_found,
    }