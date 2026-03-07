from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, desc
from typing import Optional
from pydantic import BaseModel
from datetime import datetime
import csv
import io

from app.database import get_session
from app.models.alert import Alert
from app.routers.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/alerts", tags=["alerts"])


WORKFLOW_STATUS_LABELS = {
    "pending": "待核实",
    "pending_verify": "待核实",
    "confirmed": "已核实真实火灾",
    "verified_true": "已核实真实火灾",
    "false_alarm": "已核实误报",
    "verified_false": "已核实误报",
    "dispatched": "已联动消防",
    "resolved": "已完成上报",
}


def expand_status_filter(status: str) -> set[str]:
    aliases = {
        "pending": {"pending", "pending_verify"},
        "pending_verify": {"pending", "pending_verify"},
        "confirmed": {"confirmed", "verified_true", "dispatched", "resolved"},
        "false_alarm": {"false_alarm", "verified_false"},
        # operator 当前任务队列
        "operator_queue": {"pending", "pending_verify", "confirmed", "verified_true", "dispatched"},
        # 已闭环（真实火情完成 + 误报核实）
        "done": {"resolved", "verified_false", "false_alarm"},
    }
    return aliases.get(status, {status})


def append_remark(original: Optional[str], extra: Optional[str]) -> Optional[str]:
    if not extra:
        return original
    extra = extra.strip()
    if not extra:
        return original
    if not original:
        return extra
    return f"{original}\n{extra}"


# ---- Schemas ----
class AlertProcess(BaseModel):
    status: str  # confirmed / false_alarm
    remark: Optional[str] = None


class AlertDispatch(BaseModel):
    contact: Optional[str] = None
    note: Optional[str] = None


class AlertResolve(BaseModel):
    remark: Optional[str] = None


# ---- 告警列表（支持状态筛选、分页） ----
@router.get("")
def list_alerts(
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    query = select(Alert).order_by(desc(Alert.timestamp))
    if status:
        values = expand_status_filter(status)
        query = query.where(Alert.status.in_(values))
    
    total_query = select(Alert)
    if status:
        values = expand_status_filter(status)
        total_query = total_query.where(Alert.status.in_(values))
    total = len(session.exec(total_query).all())
    
    alerts = session.exec(query.offset((page - 1) * size).limit(size)).all()
    return {"total": total, "items": alerts}


# ---- 处理告警（确认/误报 + 备注） ----
@router.put("/{alert_id}/process")
def process_alert(
    alert_id: int,
    data: AlertProcess,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if data.status == "confirmed":
        alert.status = "verified_true"
        result_note = f"【现场核实】真实火灾（{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}）"
    elif data.status == "false_alarm":
        alert.status = "verified_false"
        result_note = f"【现场核实】误报（{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}）"
    else:
        raise HTTPException(status_code=400, detail="status must be confirmed or false_alarm")

    alert.remark = append_remark(alert.remark, result_note)
    alert.remark = append_remark(alert.remark, data.remark)
    session.add(alert)
    session.commit()
    session.refresh(alert)
    return alert


@router.put("/{alert_id}/dispatch")
def dispatch_fire_alert(
    alert_id: int,
    data: AlertDispatch,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    if alert.status not in {"verified_true", "confirmed", "dispatched"}:
        raise HTTPException(status_code=400, detail="Only verified true-fire alerts can be dispatched")

    alert.status = "dispatched"
    dispatch_msg = f"【联动消防】已通知林区消防队（{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}）"
    if data.contact and data.contact.strip():
        dispatch_msg = f"{dispatch_msg}；联系人：{data.contact.strip()}"
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
    current_user: User = Depends(get_current_user)
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


# ---- 导出告警数据为 CSV ----
@router.get("/export/csv")
def export_alerts_csv(
    status: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    query = select(Alert).order_by(desc(Alert.timestamp))
    if status:
        values = expand_status_filter(status)
        query = query.where(Alert.status.in_(values))
    alerts = session.exec(query).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "时间", "YOLO置信度", "AI建议", "工作流状态", "备注", "截图路径"])
    for a in alerts:
        writer.writerow([
            a.id,
            a.timestamp,
            a.yolo_confidence,
            a.llm_result,
            WORKFLOW_STATUS_LABELS.get(a.status, a.status),
            a.remark,
            a.image_path
        ])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=alerts_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"}
    )


# ---- 告警详情 ----
@router.get("/{alert_id}")
def get_alert(alert_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    alert = session.get(Alert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


# ---- 批量删除告警 ----
class BatchDeleteRequest(BaseModel):
    ids: list[int]

@router.post("/batch-delete")
def batch_delete_alerts(
    data: BatchDeleteRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    deleted = 0
    for aid in data.ids:
        alert = session.get(Alert, aid)
        if alert:
            session.delete(alert)
            deleted += 1
    session.commit()
    return {"msg": f"已删除 {deleted} 条记录", "deleted": deleted}
