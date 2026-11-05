"""fishmo FastAPI 入口。

包根是 ``app/``：所有命令都必须在 app 目录下运行（或把 app 加入 sys.path）。
"""

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api import service_router
from config import CORS_ORIGINS, async_engine
from utils import AppError, info, shutdown_scheduler, start_scheduler

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        start_scheduler()
    except Exception:  # noqa: BLE001
        logger.exception("启动定时任务失败，浏览量将不会定时落库")
    yield
    shutdown_scheduler()
    await async_engine.dispose()


app = FastAPI(
    title="fishmo API",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    """业务异常统一转为 FastAPI 风格的 {"detail": "..."}。"""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.msg})


app.include_router(service_router)


@app.get("/api/health", tags=["health"])
async def health():
    return info("服务正常", data={"status": "ok"})


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_excludes=["logs/*", "*.log", "__pycache__/*"],
    )