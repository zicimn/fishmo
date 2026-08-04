# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

`fishmo` 是一个 FastAPI 后端项目（目前尚无前端，CORS 已为前端预留）。技术栈：**Python 3.11+ / FastAPI 0.133 / SQLAlchemy 2.0 异步 / aiomysql / Pydantic v2 / python-jose(JWT) / passlib(argon2) / redis.asyncio**。代码注释为中文。

## 常用命令

必须在 **`backend/app`** 目录下运行（所有模块都按此目录作为 import 根来组织）：

```bash
cd backend/app
python main.py                          # 启动开发服务器（uvicorn + reload）
# 或直接运行 uvicorn：
uvicorn main:app --reload
```

Python 环境在仓库根的 `.venv` 中：

```bash
D:/vscode/fishmo/.venv/Scripts/python.exe main.py
```

**重要**：`main.py` 里的 `uvicorn.run("main:app", ...)` 使用模块字符串，从仓库根或 `backend/` 运行会报 `ModuleNotFoundError`。项目目前**没有**测试、lint 配置或 CI。

## 架构与分层约定

```
backend/app/
  main.py      — 应用入口：FastAPI 实例、CORS 中间件、include_router、uvicorn 启动
  api/v1/      — 路由层（user.py：/api/v1/user/login、/api/v1/user/register）
  config/      — 基础设施配置：db.py（异步引擎/会话）、cache.py（Redis）、security.py（JWT）
  model/       — SQLAlchemy ORM 模型（user.py：User 表）
  schemas/     — Pydantic v2 请求/响应模型
  utils/       — 目前为空
```

- **分层设计**：计划为 router → service → repository 的领域分层，但目前 `api/v1/user.py` 直接在路由里操作 ORM，尚未抽出 service/repository 层。
- **导入约定**：包内一律用相对导入（`from .user import ...`），跨模块用相对于 `backend/app` 的绝对导入（`from config.db import ...`、`from api.v1 import ...`）。`__init__.py` 统一从 `model`/`schemas` 导出领域对象。

### 数据层（config/db.py）
- SQLAlchemy 2.0 异步风格：`create_async_engine` + `async_sessionmaker`，MySQL 驱动 `aiomysql`。
- `get_db()` 是一个 yield 依赖：自动 commit、异常回滚并重新抛出、finally 关闭会话。所有端点通过 `db: AsyncSession = Depends(get_db)` 注入。
- **无 Alembic 迁移**：表需手动创建，没有 `create_all` 调用。MySQL 连接串硬编码在 `db.py`（`root@localhost:3306/web1`），MySQL 未启动或库不存在时，登录/注册接口会失败（启动本身不连库，引擎是惰性的）。

### 认证与安全（config/security.py、api/v1/user.py）
- JWT（HS256）：`SECRET_KEY` / `ALGORITHM` 从 `config.security` 导入，密钥通过环境变量 `SECRET_KEY` 注入，带本地开发默认值。
- 密码哈希：`passlib` 的 `CryptContext(schemes=["argon2"])`。库表 `user` 的 `password_hash` 列存哈希值。
- `config/db.py`、`config/cache.py` 中的连接凭据目前硬编码在代码里（生产需改为环境变量）。

### 缓存（config/cache.py）
- `redis.asyncio` 客户端（localhost:6379），惰性连接，不阻塞启动。
- 提供 `get_from_cache` / `set_to_cache` / `delete_cache` / `delete_cache_pattern`，以及基于 `search_version` 计数器的版本化缓存失效模式（`get_search_version` / `update_version`）。

## 版本相关注意事项

- FastAPI 固定为 **0.133**：`APIRouter` 的 prefix 必须用关键字参数 `APIRouter(prefix=...)`（首位置参数已被移除）。
- Pydantic **v2**：禁止 `orm_mode` / `config.Config`，统一使用 `model_config = ConfigDict(from_attributes=True)`。
- 禁止使用 `on_event`（用 `lifespan`）。
