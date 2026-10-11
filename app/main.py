import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.service import user_router, email_router, gal_router, link_router, comment_router, favorite_router, search_router, article_router
from api.admin import control_router
import uvicorn
import logging
from contextlib import asynccontextmanager
from utils import shutdown_scheduler, start_scheduler
from config import async_engine


logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时：仅启动定时任务（浏览量定时落库）。数据表已人工建好，不做建表。
    try:
        start_scheduler()
    except Exception:
        logger.exception("启动定时任务失败，浏览量将不会定时落库")
    yield
    # 关闭时：停止定时任务，释放连接池
    shutdown_scheduler()
    await async_engine.dispose()

app = FastAPI(lifespan=lifespan)

# 允许前端跨域访问
cors_origins_str = os.getenv("CORS_ORIGINS", "http://localhost:3000")
cors_origins = [o.strip() for o in cors_origins_str.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(email_router)
app.include_router(gal_router)
app.include_router(link_router)
app.include_router(comment_router)
app.include_router(favorite_router)
app.include_router(search_router)
app.include_router(article_router)
app.include_router(control_router)

if __name__ == "__main__":
    uvicorn.run("main:app",reload=True,reload_excludes=["logs/*", "*.log", "__pycache__/*"])