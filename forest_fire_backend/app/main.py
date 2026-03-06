from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.database import create_db_and_tables
from app.config import UPLOAD_DIR
from app.routers import auth, stream, ws, alerts, supervisor, admin

# ... (lifespan and app creation stay)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="森林火灾预警系统", version="1.0.0", lifespan=lifespan)

# 注册路由
app.include_router(auth.router)
app.include_router(stream.router)
app.include_router(ws.router)
app.include_router(alerts.router)
app.include_router(supervisor.router)
app.include_router(admin.router)

# CORS 中间件 — 允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件挂载
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")


@app.get("/")
async def root():
    return {"message": "森林火灾预警系统 API 正在运行"}
