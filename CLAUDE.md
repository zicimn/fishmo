# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

`fishmo` 是一个 FastAPI 后端项目（目前尚无前端，CORS 已为前端预留），核心业务是 **galgame（美少女游戏）信息发布**：用户发布游戏（三名称/简介/封面/截图/标签/平台），带浏览量计数与 Redis 版本化缓存。技术栈：**Python 3.11+ / FastAPI 0.133 / SQLAlchemy 2.0 异步 / aiomysql / Pydantic v2 / python-jose(JWT) / passlib(argon2) / redis.asyncio / cloudinary（图片上传）**。代码注释为中文。

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

**重要**：`main.py` 里的 `uvicorn.run("main:app", ...)` 使用模块字符串，从仓库根或 `backend/` 运行会报 `ModuleNotFoundError`。项目目前**没有**测试、lint 配置或 CI；`test/` 下是手动验证脚本（`verify_email.py` / `verify_cloud.py`），非 pytest。

> 接口清单与请求/响应格式见 `docs/router.md`；开发修改与报错记录见 `docs/fastapi_log.md`。

## 架构与分层约定

```
backend/app/
  main.py      — 应用入口：FastAPI 实例、CORS 中间件、include_router、uvicorn 启动
  api/v1/      — 路由层：user.py、email.py、galgame.py（前缀 /api/v1/user、/api/v1/email、/api/v1/galgame）
  config/      — 基础设施配置：db.py（异步引擎/会话）、cache.py（Redis + 版本化缓存）、security.py（JWT + 环境变量）
  model/       — SQLAlchemy ORM 模型（user.py、galgame.py、enums.py）
  schemas/     — Pydantic v2 请求/响应模型（user.py、galgame.py）
  utils/       — email.py（Resend 验证码）、verify_user.py（JWT 校验）、webp.py（图片转换 + Cloudinary 上传）
```

- **分层设计**：计划为 router → service → repository 的领域分层，但目前 `api/v1/user.py`、`api/v1/galgame.py` 直接在路由里操作 ORM，尚未抽出 service/repository 层。
- **导入约定**：包内一律用相对导入（`from .user import ...`），跨模块用相对于 `backend/app` 的绝对导入（`from config.db import ...`、`from api.v1 import ...`）。`__init__.py` 统一从 `model`/`schemas` 导出领域对象。
- **共享枚举**：`PlatformEnum` 定义在 `model/enums.py`（model 与 schemas 共同引用）。**model 层禁止反向依赖 schemas 层**，跨层共享的常量一律下沉到 `model/enums.py`。

### 数据层（config/db.py、model/）
- SQLAlchemy 2.0 异步风格：`create_async_engine` + `async_sessionmaker`，MySQL 驱动 `aiomysql`。
- `get_db()` 是一个 yield 依赖：正常自动 commit、异常回滚并重新抛出、finally 关闭会话。所有端点通过 `db: AsyncSession = Depends(get_db)` 注入。
- **连接串来自环境变量**：`db.py` 用 `from config.security import ASYNC_DATABASE_URL`（非硬编码）；变量由 `backend/app/.env` 提供（`security.py` 的 `load_dotenv()` 按 CWD 加载，故须在 `backend/app` 下运行）。MySQL 未启动或库不存在时接口会失败（启动本身不连库，引擎是惰性的）。
- **无 Alembic 迁移**：`user`/`galgame` 表需手动创建，没有 `create_all` 调用。
- **关系加载**：`User.galgames` 集合侧 `lazy="raise"`——**任何 User 查询都不应隐式全量加载其 galgames**，需要时显式 `selectinload()`；多对一侧 `Galgame.author` 保持 `lazy="selectin"`。
- `galgame` 表三名称列（cn/en/jp）NOT NULL：Python 侧 `default=""` 兜底，schema 侧 `model_validator` 保证至少一个名称非空。

### 认证与安全（config/security.py、utils/verify_user.py、api/v1/）
- JWT（HS256）：`SECRET_KEY` / `ALGORITHM` 从 `config.security` 导入。变量均由环境变量注入（`backend/app/.env`），**无代码内默认值**，缺 `.env` 时 `SECRET_KEY` 为 None、JWT 签发/校验会失败。
- 密码哈希：`passlib` 的 `CryptContext(schemes=["argon2"])`。
- 鉴权模式：路由内 `security = HTTPBearer(auto_error=False)`，业务端点先 `verify_login(credentials)` 解析 user_id；缺 token / token 无效统一 `401`（`utils/verify_user.py`）。
- **galgame 业务规则**：作者即发布者——`add` 时 `status=True` 直接公开；`delete`/`edit` 必须校验 `author_id == 当前用户`（非作者 403）。删除用户时若其下有作品，外键 `ondelete="RESTRICT"` 触发 `IntegrityError`，`user.py` 已捕获返回 400。
- Cloudinary 凭据：`CLOUDINARY_API_KEY/SECRET` 优先读正确拼写，回退历史拼写错误名 `CLOUNDDINARY_*`，兼容新旧 .env。

### 缓存（config/cache.py）
- `redis.asyncio` 客户端（localhost:6379），惰性连接，不阻塞启动。
- 提供 `get_from_cache` / `set_to_cache` / `delete_cache` / `delete_cache_pattern`，以及基于 `search_version` 计数器的版本化缓存失效模式（`get_search_version` / `update_version`）。
- **约定**：列表/详情缓存 key 一律带 `version`；**任何增删改成功（user 的 update/delete、galgame 的 add/delete/edit）都必须 `await update_version()` 并使相关 key 失效**，否则缓存继续服务旧数据。注意 `get_search_version` / `get_from_cache` / `set_to_cache` 均为 async，必须 `await`。
- **浏览量计数与响应缓存解耦**（galgame 详情）：无论缓存是否命中都用 Redis `INCR gal_views:{id}` 计数（key 带 TTL），累计满阈值（`delta % 10 == 0`）时用 SQL 原子自增 `views += delta` 落库。

### 图片上传（utils/webp.py）
- 全部为**同步函数**（PIL 解码 CPU 密集 + Cloudinary 同步 HTTP），从 async 端点调用必须用 `run_in_threadpool` 包裹（或 `asyncio.to_thread`），否则阻塞事件循环。
- 反压缩炸弹防护：单图 base64 解码后 ≤ 5MB、像素 ≤ 50MP；**失败返回 `None`，调用方必须判空**，不能把 None 当成功结果用。
- 统一转 WebP（quality 75）等比缩放后上传，返回 `{status, url, public_id}` 或 `{status: False, error}`。

## 版本相关注意事项

- FastAPI 固定为 **0.133**：`APIRouter` 的 prefix 必须用关键字参数 `APIRouter(prefix=...)`（首位置参数已被移除）。
- Pydantic **v2**：禁止 `orm_mode` / `config.Config`，统一使用 `model_config = ConfigDict(from_attributes=True)`。
- 禁止使用 `on_event`（用 `lifespan`）。
