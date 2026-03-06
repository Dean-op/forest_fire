from sqlmodel import Session, select
from app.database import engine
from app.models.user import User
from app.models.alert import Alert
from app.utils.security import get_password_hash
from datetime import datetime, timedelta
import random


def create_seed_data():
    with Session(engine) as session:
        # 1. 预置账号
        admins = session.exec(select(User).where(User.username == "admin")).all()
        if not admins:
            seed_users = [
                User(username="admin", hashed_password=get_password_hash("123456"), role="admin"),
                User(username="manager", hashed_password=get_password_hash("123456"), role="supervisor"),
                User(username="operator", hashed_password=get_password_hash("123456"), role="operator"),
            ]
            session.add_all(seed_users)
            session.commit()
            print("用户种子数据生成成功！默认密码皆为 123456。")
        
        # 2. 模拟告警记录
        existing_alerts = session.exec(select(Alert)).all()
        if not existing_alerts:
            statuses = ["pending", "confirmed", "false_alarm"]
            llm_results = [
                "⚠️ 经视觉大模型确认：画面中存在明显的明火和浓烟，确认为真实火灾！",
                "✅ 经视觉大模型分析：画面中的红色光源为夕阳反光，非火灾。",
                "⚠️ 检测到浓烟，但未见明火，建议现场核实。",
                "✅ 画面正常，检测到的亮点为工业设备指示灯。",
                "⚠️ 存在大面积烟雾扩散迹象，疑似林火初期阶段。",
            ]
            for i in range(15):
                alert = Alert(
                    timestamp=datetime.utcnow() - timedelta(hours=random.randint(1, 168)),
                    image_path=f"/static/fire_sample_{i+1}.jpg",
                    yolo_confidence=round(random.uniform(0.60, 0.99), 2),
                    llm_result=random.choice(llm_results),
                    status=random.choice(statuses),
                    remark="自动生成的测试数据" if random.random() > 0.5 else None,
                )
                session.add(alert)
            session.commit()
            print("告警种子数据 (15条) 生成成功！")
        
        # 3. 模拟摄像头设备
        from app.models.supervisor import Camera, CameraLog, CaptureConfig, ShiftLog
        existing_cameras = session.exec(select(Camera)).all()
        if not existing_cameras:
            cam_data = [
                ("东区瞭望塔", "rtsp://192.168.1.101:554/stream", "东区山顶", "online"),
                ("西区林道入口", "rtsp://192.168.1.102:554/stream", "西区入口处", "online"),
                ("北区防火带", "rtsp://192.168.1.103:554/stream", "北区防火隔离带", "online"),
                ("南区管理站", "rtsp://192.168.1.104:554/stream", "南区管理站楼顶", "offline"),
            ]
            for name, url, loc, st in cam_data:
                cam = Camera(name=name, rtsp_url=url, location=loc, status=st)
                session.add(cam)
            session.commit()

            # 设备日志
            cams = session.exec(select(Camera)).all()
            events = ["设备上线", "设备掉线", "设备恢复", "信号弱", "设备上线"]
            for cam in cams:
                for j in range(3):
                    log = CameraLog(
                        camera_id=cam.id,
                        event=random.choice(events),
                        timestamp=datetime.utcnow() - timedelta(hours=random.randint(1, 72))
                    )
                    session.add(log)

            # 抓拍配置
            for cam in cams:
                cfg = CaptureConfig(camera_id=cam.id, enable_capture=True, capture_interval=random.choice([3, 5, 10]))
                session.add(cfg)

            # 交接班日志
            shifts = [
                ("张三", "2026-03-05 08:00 - 16:00", "白班正常巡检，无异常。"),
                ("李四", "2026-03-05 16:00 - 00:00", "晚班接班，东区有疑似烟雾，已排查为村民烧秸秆。"),
                ("王五", "2026-03-04 00:00 - 08:00", "夜班正常，所有设备运行稳定。"),
            ]
            for op, st, ct in shifts:
                session.add(ShiftLog(operator=op, shift_time=st, content=ct))

            session.commit()
            print("设备/配置/交接班种子数据生成成功！")

        # 4. 系统参数配置
        from app.models.admin import SystemConfig, Announcement, SystemLog
        existing_configs = session.exec(select(SystemConfig)).all()
        if not existing_configs:
            configs = [
                ("yolo_confidence", "0.6", "YOLO 检测置信度阈值", "ai"),
                ("yolo_model_path", "best.pt", "YOLO 模型文件路径", "ai"),
                ("capture_interval", "5", "默认抓拍间隔 (秒)", "ai"),
                ("llm_api_url", "https://dashscope.aliyuncs.com", "大模型 API 地址", "llm"),
                ("llm_api_key", "sk-xxxxx", "大模型 API Key", "llm"),
                ("llm_model", "qwen-vl-max", "大模型名称", "llm"),
                ("system_name", "森林火灾预警系统", "系统名称", "general"),
                ("alert_sound", "true", "告警声音提醒", "general"),
            ]
            for key, val, label, group in configs:
                session.add(SystemConfig(key=key, value=val, label=label, group=group))
            session.commit()
            print("系统参数配置种子数据生成成功！")

        # 5. 公告 / SOP
        existing_ann = session.exec(select(Announcement)).all()
        if not existing_ann:
            anns = [
                ("系统上线通知", "本系统已于 2026 年 3 月正式上线，请各岗位人员及时熟悉操作流程。", "notice"),
                ("值班人员注意事项", "1. 每小时至少检查一次监控大屏\n2. 发现告警后立即核实\n3. 确认火灾需 5 分钟内上报\n4. 交接班必须填写交接日志", "sop"),
                ("误报处理流程", "1. 点击\"标记为误报\"\n2. 在备注栏填写误报原因（如夕阳反光、工业排烟等）\n3. 主管定期审核误报率", "sop"),
            ]
            for title, content, cat in anns:
                session.add(Announcement(title=title, content=content, category=cat))
            session.commit()
            print("公告/SOP 种子数据生成成功！")

        # 6. 系统日志
        existing_logs = session.exec(select(SystemLog)).all()
        if not existing_logs:
            log_data = [
                ("admin", "登录系统", "管理员登录", "127.0.0.1"),
                ("admin", "创建用户", "新增用户 operator", "127.0.0.1"),
                ("operator", "处理告警", "告警ID #3 标记为误报", "192.168.1.50"),
                ("manager", "查看统计", "访问统计看板", "192.168.1.60"),
                ("admin", "修改配置", "YOLO 置信度阈值调整为 0.7", "127.0.0.1"),
                ("operator", "登录系统", "操作员登录", "192.168.1.50"),
            ]
            for user, action, detail, ip in log_data:
                session.add(SystemLog(user=user, action=action, detail=detail, ip=ip, timestamp=datetime.utcnow() - timedelta(hours=random.randint(1, 48))))
            session.commit()
            print("系统日志种子数据生成成功！")

if __name__ == "__main__":
    create_seed_data()
