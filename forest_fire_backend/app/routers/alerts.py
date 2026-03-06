from fastapi import APIRouter, Depends, Query
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


# ---- Schemas ----
class AlertProcess(BaseModel):
    status: str  # confirmed / false_alarm
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
        query = query.where(Alert.status == status)
    
    total_query = select(Alert)
    if status:
        total_query = total_query.where(Alert.status == status)
    total = len(session.exec(total_query).all())
    
    alerts = session.exec(query.offset((page - 1) * size).limit(size)).all()
    return {"total": total, "items": alerts}


# ---- 告警详情 ----
@router.get("/{alert_id}")
def get_alert(alert_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    alert = session.get(Alert, alert_id)
    if not alert:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert


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
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alert.status = data.status
    alert.remark = data.remark
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
        query = query.where(Alert.status == status)
    alerts = session.exec(query).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "时间", "YOLO置信度", "大模型判定", "状态", "备注", "截图路径"])
    for a in alerts:
        writer.writerow([a.id, a.timestamp, a.yolo_confidence, a.llm_result, a.status, a.remark, a.image_path])
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=alerts_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"}
    )


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
