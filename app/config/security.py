"""安全与第三方服务配置。

所有敏感值只从 ``app/.env`` 读取，代码中不提供默认密钥。
.env 的加载路径基于本文件位置（而不是当前工作目录），
因此无论从仓库根还是 ``app/`` 启动都能命中同一份配置。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# app/config/security.py -> app/
APP_DIR = Path(__file__).resolve().parents[1]
load_dotenv(APP_DIR / ".env")


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"缺少必需的环境变量：{name}（请检查 app/.env）")
    return value


# JWT
SECRET_KEY = require_env("SECRET_KEY")
ALGORITHM = "HS256"
TOKEN_EXPIRE_DAYS = 7

# MySQL（异步驱动 aiomysql）
ASYNC_DATABASE_URL = require_env("ASYNC_DATABASE_URL")

# Redis：本地默认无密码
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD") or None

# Resend
RESEND_API_KEY = require_env("RESEND_API_KEY")
RESEND_FROM = os.getenv("RESEND_FROM", "fishmo <noboard@fishmo.top>")

# Cloudinary
CLOUDINARY_API_KEY = require_env("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = require_env("CLOUDINARY_API_SECRET")
CLOUDINARY_CLOUD_NAME = require_env("CLOUDINARY_CLOUD_NAME")

# 允许的前端来源：前台 3000、管理端 3001
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:3001,"
        "http://127.0.0.1:3000,http://127.0.0.1:3001",
    ).split(",")
    if origin.strip()
]

# SQL 日志默认关闭，排查问题时设置 DB_ECHO=true
DB_ECHO = os.getenv("DB_ECHO", "false").lower() in ("1", "true", "yes", "on")