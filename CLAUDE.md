# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

`fishmo` 是一个 **galgame（美少女游戏）信息发布社区** 全栈项目。后端核心业务：用户注册/登录、邮箱验证码、发布游戏（三名称/简介/封面/截图/标签/平台）、浏览量计数与 Redis 版本化缓存，以及围绕游戏的**链接分享**、**评论**、**收藏**三个扩展模块，外加**全文搜索**与**管理员审核**功能。前端（Nuxt 3 + Element Plus）已具备完整业务页面。技术栈：**Python 3.11+ / FastAPI 0.133 / SQLAlchemy 2.0 异步 / aiomysql / Pydantic v2 / python-jose(JWT) / passlib(argon2) / redis.asyncio / cloudinary（图片上传）**。代码注释为中文。

## 常用命令

### 后端

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

### 前端

```bash
cd frontend
npm install
npm run dev                             # Nuxt 3 开发服务器
npm run build                           # 生产构建
```

> 接口清单与请求/响应格式见 `docs/router.md`；开发修改与报错记录见 `docs/fastapi_log.md`。

## 架构与分层约定

```
backend/app/
  main.py       — 应用入口：FastAPI 实例、CORS 中间件、include_router、lifespan（定时任务 + 引擎释放）
  api/v1/       — 路由层：user.py、email.py、galgame.py、link.py、comment.py、favorite.py、search.py
  api/admin/    — 管理员路由：control.py（审核/删除游戏，前缀 /api/admin/control）
  config/       — 基础设施配置：db.py（异步引擎/会话）、cache.py（Redis + 版本化缓存）、security.py（JWT + 环境变量）
  model/        — SQLAlchemy ORM 模型（user.py、galgame.py、link.py、comment.py、favorite.py、enums.py）
  schemas/      — Pydantic v2 请求/响应模型（user.py、galgame.py、link.py、comment.py）
  utils/        — email.py（Resend 验证码）、verify_user.py（JWT 校验 + 管理员校验）、webp.py（图片转换 + Cloudinary 上传）、counter.py（浏览量计数 ViewCounter）

frontend/
  pages/        — 页面：index / games / user / admin / publish / galgame
  composables/  — 组合函数：useAuth / useGalgame 等
  stores/       — Pinia 状态：auth.ts（token/isAdmin/userId/username/avatar）
  middleware/   — 路由守卫：auth.ts（登录守卫）、admin.ts（管理员守卫）
  types/        — TypeScript 类型定义（与后端 schema 对齐）
  layouts/      — 布局：default.vue（顶栏导航 + 搜索 + 移动端抽屉）
```

- **分层设计**：计划为 router → service → repository 的领域分层，但目前路由层直接操作 ORM，尚未抽出 service/repository 层。
- **导入约定**：包内一律用相对导入（`from .user import ...`），跨模块用相对于 `backend/app` 的绝对导入（`from config.db import ...`、`from api.v1 import ...`）。`__init__.py` 统一从 `model`/`schemas` 导出领域对象。
- **共享枚举**：`PlatformEnum`、`CategoryEnum`、`ReceiveEnum`、`SizeUnitEnum`、`SearchEnum` 定义在 `model/enums.py`（model 与 schemas 共同引用）。**model 层禁止反向依赖 schemas 层**，跨层共享的常量一律下沉到 `model/enums.py`。

### 数据层（config/db.py、model/）
- SQLAlchemy 2.0 异步风格：`create_async_engine` + `async_sessionmaker`，MySQL 驱动 `aiomysql`。
- `get_db()` 是一个 yield 依赖：正常自动 commit、异常回滚并重新抛出、finally 关闭会话。所有端点通过 `db: AsyncSession = Depends(get_db)` 注入。
- **连接串来自环境变量**：`db.py` 用 `from config.security import ASYNC_DATABASE_URL`（非硬编码）；变量由 `backend/app/.env` 提供（`security.py` 的 `load_dotenv()` 按 CWD 加载，故须在 `backend/app` 下运行）。MySQL 未启动或库不存在时接口会失败（启动本身不连库，引擎是惰性的）。
- **无 Alembic 迁移**：`user`/`galgame`/`link`/`comment`/`favorite` 表需手动创建，没有 `create_all` 调用。
- **关系加载**：`User.galgames` / `User.links` / `User.comments` / `User.favorites` / `Galgame.links` / `Galgame.favorites` 集合侧均为 `lazy="raise"`——**任何查询都不应隐式全量加载关联集合**，需要时显式 `selectinload()`；多对一侧（`Galgame.author` / `Link.author` / `Link.galgame` / `Comment.author` / `Favorite.author` / `Favorite.galgame`）保持 `lazy="selectin"`。
- `galgame` 表：`name` 字段（String(50), UNIQUE, NOT NULL）为统一名称，由 schema `_normalize_names` 自动从三语言名称派生；三名称列（cn/en/jp）NOT NULL，Python 侧 `default=""` 兜底。
- `favorite` 表：`UniqueConstraint("user_id", "gal_id")` 防止重复收藏，外键均 `ondelete=RESTRICT`。

### 认证与安全（config/security.py、utils/verify_user.py、api/v1/、api/admin/）
- JWT（HS256）：`SECRET_KEY` / `ALGORITHM` 从 `config.security` 导入。变量均由环境变量注入（`backend/app/.env`），**无代码内默认值**，缺 `.env` 时 `SECRET_KEY` 为 None、JWT 签发/校验会失败。
- JWT payload 包含 `{sub: str(user.id), username, is_admin}`，其中 `is_admin` 供管理员校验使用。
- 密码哈希：`passlib` 的 `CryptContext(schemes=["argon2"])`。
- **用户鉴权**：路由内 `security = HTTPBearer(auto_error=False)`，业务端点先 `verify_login(credentials)` 解析 user_id；缺 token / token 无效统一 `401`（`utils/verify_user.py`）。
- **管理员鉴权**：`verify_admin(credentials)` 解析 JWT 中的 `is_admin` 字段，非管理员返回 `False`（admin 端点据此返回 `403`）。
- **galgame 审核流程**：`add` 时 `status=False`（待审核），管理员通过 `PUT /api/admin/control/UpdateStatus?status=true` 审核后公开；`visit` 端点管理员可绕过 `status=False` 限制查看未审核游戏。
- **galgame 业务规则**：作者即发布者——`delete`/`edit` 必须校验 `author_id == 当前用户`（非作者 403）。删除用户时若其下有作品，外键 `ondelete="RESTRICT"` 触发 `IntegrityError`，`user.py` 已捕获返回 400。
- Cloudinary 凭据：`CLOUDINARY_API_KEY/SECRET` 优先读正确拼写，回退历史拼写错误名 `CLOUNDDINARY_*`，兼容新旧 .env。

### 缓存（config/cache.py）
- `redis.asyncio` 客户端（localhost:6379），惰性连接，不阻塞启动。
- 提供 `get_from_cache` / `set_to_cache` / `delete_cache` / `delete_cache_pattern` / `get_cache_key`，以及基于版本计数器的版本化缓存失效模式（`get_search_version` / `update_version`）。
- **版本计数按业务域拆分**：`GAL_VERSION_KEY` / `LINK_VERSION_KEY` / `COMMENT_VERSION_KEY`（全局 `SEARCH_VERSION_KEY` 保留向后兼容），某域增删改只自增该域版本号。
- **约定**：列表/详情缓存 key 一律带 `version`；**任何增删改成功（user 的 update/delete、galgame 的 add/delete/edit、admin 的 UpdateStatus/DeleteGal、favorite 的 add/remove）都必须 `await update_version(对应域KEY)` 并使相关 key 失效**，否则缓存继续服务旧数据。注意 `get_search_version` / `get_from_cache` / `set_to_cache` 均为 async，必须 `await`。
- **浏览量计数与响应缓存解耦**（galgame 详情）：无论缓存是否命中都用 `ViewCounter.incr(id)`（Redis 累积计数），由定时任务（`utils/counter.py` + `utils/__init__.py` 的 scheduler）批量落库。

### 图片上传（utils/webp.py）
- 全部为**同步函数**（PIL 解码 CPU 密集 + Cloudinary 同步 HTTP），从 async 端点调用必须用 `run_in_threadpool` 包裹（或 `asyncio.to_thread`），否则阻塞事件循环。
- 反压缩炸弹防护：单图 base64 解码后 ≤ 5MB、像素 ≤ 50MP；**失败返回 `None`，调用方必须判空**，不能把 None 当成功结果用。
- 统一转 WebP（quality 75）等比缩放后上传，返回 `{status, url, public_id}` 或 `{status: False, error}`。
- 编辑时已托管 URL（`http://`/`https://` 开头）直接复用，不重复上传；仅 base64 新图走上传流程。

### 前端架构（frontend/）
- **Nuxt 3 + Vue 3 + TypeScript + Pinia + Element Plus**，深色主题设计系统。
- **认证状态**：`stores/auth.ts` 管理 token/userId/username/avatar/isAdmin，持久化到 localStorage；SSR 阶段不可访问 localStorage，由客户端 `initFromStorage()` 恢复。
- **SSR 水合一致性**：`layouts/default.vue` 使用 `isMounted` 门控，挂载前统一渲染"未登录"状态，避免水合 mismatch。
- **路由守卫**：`middleware/auth.ts`（登录守卫）、`middleware/admin.ts`（管理员守卫，客户端判断，SSR 阶段放行）。
- **类型对齐**：`types/` 下的 TypeScript 类型与后端 `schemas/` 和 `model/enums.py` 严格对齐，枚举传输中文值（如 `"电脑端"`、`"剧情向"`）。

## 版本相关注意事项

- FastAPI 固定为 **0.133**：`APIRouter` 的 prefix 必须用关键字参数 `APIRouter(prefix=...)`（首位置参数已被移除）。
- Pydantic **v2**：禁止 `orm_mode` / `config.Config`，统一使用 `model_config = ConfigDict(from_attributes=True)`。
- 禁止使用 `on_event`（用 `lifespan`）。`main.py` 使用 `@asynccontextmanager` 的 `lifespan` 管理启动/关闭生命周期。

## 已知限制（开发时需注意）

1. **JWT 无过期时间**：`jwt.encode` 未带 `exp`，token 签发后永久有效。
2. **CORS**：`allow_origins=["*"]` + `allow_credentials=True` 组合不符合浏览器规范，生产需白名单化。
3. **无 Alembic 迁移**：表结构变更需手动 DDL，model 文件变更后务必同步数据库。
4. **字段拼写**：`platfrom`（应为 platform）、`update_at`（应为 updated_at）为既有拼写，改动需数据库迁移。
5. **无测试/lint/CI**：修改后需手动验证。
6. **`logs/` 目录不应纳入版本控制**：需在 `.gitignore` 中添加 `logs/` 和 `*.log`。
