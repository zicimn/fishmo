# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

`fishmo` 是 **Galgame 信息发布社区 + 文章博客** 的全栈项目，仓库由三个可独立运行的应用组成：

| 应用 | 目录 | 端口 | 技术栈 |
| --- | --- | --- | --- |
| 后端 API | `app/` | 8000 | FastAPI 0.133 / SQLAlchemy 2.0 async / aiomysql / Pydantic v2 / Redis / APScheduler / Cloudinary / Resend |
| 前台 Web | `frontend/` | 3000 | Nuxt 4 / Vue 3 / TypeScript / Tailwind CSS v4（SSR） |
| 管理端 | `admin/` | 3001 | Nuxt 4 / Vue 3 / TypeScript / Tailwind CSS v4（SPA，`ssr: false`） |

业务域：用户与邮箱验证码；Galgame（发布/审核/搜索/浏览量/链接/评论/收藏）；文章（Markdown 发布、分类、插图、评论）。前台使用深色玻璃拟态设计，代码注释为中文。

## 常用命令

### 后端

必须在 **`app/`** 目录下运行（`app/` 是 import 根，模块导入均为绝对路径）：

```bash
cd app
python main.py                         # 开发服务器（uvicorn + reload）
# 或指定仓库根 venv：
D:/vscode/fishmo/.venv/Scripts/python.exe main.py
# 或直接：
uvicorn main:app --reload
```

依赖安装（仓库根）：

```bash
.venv/Scripts/pip install -r requirements.txt
```

- `app/.env` 为必需文件（不提交）。必需变量：`SECRET_KEY`、`ASYNC_DATABASE_URL`、`RESEND_API_KEY`、`CLOUDINARY_API_KEY`、`CLOUDINARY_API_SECRET`、`CLOUDINARY_CLOUD_NAME`；可选：`REDIS_HOST/PORT/DB/PASSWORD`、`RESEND_FROM`、`CORS_ORIGINS`、`DB_ECHO`。缺少必填项会在启动时直接报错。
- 健康检查 `GET /api/health`；OpenAPI 文档 `/docs`。
- MySQL/Redis 为外部依赖。Redis 未启动时缓存、限流、验证码、JWT 黑名单会降级（见下文），但验证码注册与登出不可用。
- **没有 pytest / lint / CI**。`test/` 下是手动验证脚本，不是自动化测试；改动后需手动调用接口验证。

### 前台 / 管理端

```bash
cd frontend && npm install
npm run dev            # http://localhost:3000
npm run build          # 生产构建
npx nuxi typecheck     # 类型检查

cd admin && npm install
npm run dev            # http://localhost:3001
npm run build
npx nuxi typecheck
```

管理端 `nuxt.config.ts` 支持 `NUXT_PUBLIC_API_BASE`（默认 `http://127.0.0.1:8000`）与 `NUXT_PUBLIC_SITE_BASE`（默认 `http://localhost:3000`）。前台 API 地址写在 `nuxt.config.ts`：开发直连 `127.0.0.1:8000`，生产（`$production`）浏览器走同源 `/api`。

### 部署

`nginx/dev.fishmo.conf` 将 `/` 反代到 3000、`/api/` 反代到 8000，并直接服务 `_nuxt` 静态资源。管理端是独立 SPA，需要单独部署/反代其 3001 构建产物。生产 SQL 初始化脚本在 `sql/web1.sql`。

## 后端架构

### 请求链路与分层

```
main.py
  └─ api/__init__.py（聚合 service_router）
       └─ api/*.py（路由：参数校验、Depends 注入）
            └─ deps.py（GetXxxService / GetCurrentUser / GetAdminUser / client_ip）
                 └─ services/*.py（业务逻辑、commit、缓存失效）
                      └─ models/*.py（SQLAlchemy 2.0 ORM）
```

- 路由层保持很薄：不写业务逻辑，不直接操作 ORM。
- 服务通过 `Depends(GetXxxService)` 构造，`db: AsyncSession` 由 `config.db.get_db` 提供；`get_db` 在请求正常结束时兜底 commit，异常时 rollback。
- `config/__init__.py` 是配置统一出口；`utils/responsed.py` 定义 `info()` 与 `AppError` 异常族。
- `utils/verify.py` 负责 JWT 与密码；`utils/sanitize.py` 负责评论消毒。

### 响应与异常

成功响应统一为：

```json
{ "msg": "查询成功", "code": 200, "data": { "total": 0, "items": [] } }
```

错误响应**不是**信封，而是 FastAPI 风格 `{"detail": "..."}`：

- 业务异常继承 `utils/responsed.AppError`（`BadRequest/Unauthorized/Forbidden/NotFound/Conflict/Busy/...`），由 `main.py` 的异常处理器转成对应 HTTP 状态码 + `detail`。
- Pydantic 校验失败返回 422，`detail` 为数组；前端 `describeError` 会提取其中的中文 `msg`。
- 新增接口必须用 `info(...)` 包装成功响应，否则前端统一解包会失败。

### 认证与安全

- JWT HS256，有效期 **7 天**，载荷 `{sub, username, jti, iat, exp}`；**`is_admin` 不写入 token**，每次请求由 `deps.GetAdminUser` / `GetCurrentUser` 回库判定。
- 登出把 `jti` 写入 Redis 黑名单（TTL 为剩余有效期）；每次 `decode_token` 都检查黑名单。
- 密码使用 argon2；登录对不存在的账号也执行一次校验以抹平时序差异。
- 限流（Redis 固定窗口，Redis 故障时放行）：登录 IP 60 次/5 分钟、账号 10 次/5 分钟；注册 IP 5 次/小时、邮箱 5 次/小时；验证码 IP 20 次/小时、邮箱 5 次/10 分钟；评论 20 次/分钟/用户。
- 评论入库前用 nh3 白名单清洗；文章正文按 Markdown 原样存储，前端用 markdown-it `html: false` 渲染（不引入 DOMPurify）。
- 用户被禁用（`status != 1`）时登录与鉴权均拒绝；管理员不能禁用自己或其他管理员。

### 缓存与 Redis 降级

- 所有列表/详情缓存 key 带业务域版本号：`GAL_VERSION_KEY`、`LINK_VERSION_KEY`、`COMMENT_VERSION_KEY`、`ARTICLE_VERSION_KEY`、`USER_VERSION_KEY`、`SEARCH_VERSION_KEY`。
- **任何增删改成功后必须使相关缓存失效**：`delete_cache_pattern(...)` + `update_version(对应域 KEY)`。评论变化会额外失效文章缓存；删除游戏会级联失效链接/评论版本。
- 缓存 key 前缀约定：`Galgame:*`、`Gal_visit:*`、`Article:*`、`Article_visit:*`、`links:*`、`links_user:*`、`comments:*`、`comments_user:*`、`Search:*`。
- `config/cache.py` 的读写失败降级为“未命中/不写入”；每次 Redis 操作有 2 秒超时，失败后熔断 30 秒。计数器通过 `redis_guard` 复用同一保护。登出写黑名单是失败关闭（Redis 故障会报错）。
- Redis 不可用时验证码、限流、JWT 黑名单实际不可用，因此生产必须运行 Redis。

### 浏览量计数

- `utils/counter.py` 中 `ViewCounter`（`gal_views`）与 `ArticleViewCounter`（`article_views`）用 Redis Hash 累积增量。
- `utils/scheduler.py` 每 10 分钟批量写回 `views` 列；详情接口返回 `数据库值 + Redis delta`。
- 详情缓存 30 分钟，列表缓存默认 5 分钟，评论列表 2 分钟。

### 数据层约定

- 集合侧关系（`.galgames`、`.links`、`.comments`、`.favorites`、`.articles`、`.replies`）全部 `lazy="raise"`；查询需要时显式 `selectinload()`。多对一侧（`.author`、`.galgame`）为 `lazy="selectin"`。
- 删除聚合根时用 SQLAlchemy Core `delete(...)` 绕过 ORM 级联，再手动删除关联行（游戏删除链接/评论/收藏；评论删除子回复）。
- 无 Alembic：表结构变更必须手动执行 DDL，并同步 `models/` 与 `sql/web1.sql`。
- 历史字段拼写 `Galgame.platfrom`（非 platform）需保留，改列名要同步数据库与前后端。
- 共享枚举在 `models/enums.py`；**models 不得反向依赖 schemas**。
- 静态路由必须注册在 `/{id}` 之前（如 `/rvisit`、`/manage`），否则会被当作 id。

### 业务规则要点

- **Galgame**：`name` 唯一；`name/cn_name/jp_name/en_name` 至少填一个，缺省用其他名称兜底；新发布 `status=False`，需管理员审核；列表仅返回已公开，作者/管理员可看自己的未公开作品；编辑/删除校验 `author_id`。
- **Article**：`category` 在数据库是逗号分隔字符串，API 输入可接受字符串或数组，输出为数组；发布即 `status=True`；无封面时用第一张插图或 `default/file.py` 默认封面；评论数通过子查询统计。
- **Comment**：多态 `receive_type`（`article=0`、`galgame=1`），`receive_id` 为裸整数；嵌套仅 2 层；`parent_id` 指向顶级评论，`reply_to_id` 字段最终存的是**被回复用户的 user_id**（前端传的是评论 id，服务层解析）；顶级评论分页，子评论 `selectinload` 一次加载。
- **Link**：新增即 `status=True`；URL 只允许 `http://` / `https://`；编辑/删除仅作者。
- **Favorite**：`(user_id, gal_id)` 唯一约束；收藏数在 `galgame.favorite` 上同步增减。
- **用户注销**：若仍有关联作品，外键 `RESTRICT` 触发 `IntegrityError`，返回 400。

### 端点总表

| 前缀 | 端点 |
| --- | --- |
| `/api/v1/user` | `POST /login`、`POST /register?code`、`POST /logout`、`PUT /update`、`DELETE /delete`、`GET /?id` |
| `/api/v1/email` | `POST /send?email&purpose=register\|reset` |
| `/api/v1/galgame` | `GET /`（page/size/category/platform/author_id/keyword/sort）、`GET /rvisit`、`GET /{id}`、`POST /add`、`PUT /edit?id`、`DELETE /delete?id` |
| `/api/v1/link` | `GET /{game_id}`、`GET /user/{user_id}`、`POST /add?game_id`、`PUT /review?link_id`、`DELETE /delete?link_id` |
| `/api/v1/comment` | `GET /{target_id}?type=galgame\|article`、`GET /user/{user_id}`、`POST /add?game_id&type`、`PUT /edit?comment_id`、`DELETE /delete?comment_id` |
| `/api/v1/favorite` | `POST /add?gal_id`、`DELETE /remove?gal_id`、`GET /visit?gal_id`、`GET /list` |
| `/api/v1/search` | `GET /?keyword&search_type=name\|tag\|company&page&size` |
| `/api/v1/article` | `GET /`、`GET /manage`、`GET /{id}`、`POST /add`、`PUT /edit?id`、`DELETE /delete?id` |
| `/api/admin/control` | `GET Stats`、`GET BrowseGal?status=pending\|published\|all`、`PUT UpdateStatus?gal_id&status`、`DELETE DeleteGal?gal_id`、`GET Users?keyword`、`PUT UserStatus?user_id&status`、`GET Articles?status=all\|published\|hidden`、`PUT UpdateArticleStatus?article_id&status`、`DELETE DeleteArticle?article_id` |
| `/api/health` | 健康检查 |

游戏列表的 `keyword` 只匹配三个名称字段；标签/公司搜索走 `/api/v1/search/`。

### 图片上传

- `utils/cloudinary.py` 全是同步函数（PIL CPU 密集 + Cloudinary 同步 HTTP），必须通过 `services/image.py` 的 `asyncio.to_thread` 调用，不要在 async 端点里直接调用。
- base64 输入限制：解码后 ≤ 5MB、像素 ≤ 50MP；统一转 WebP（quality 75）并缩放后上传；失败返回 `None` 或 `{status: False}`，`ImageService` 会转成 422。
- 已托管 URL（`http(s)://`）直接复用；仅 base64 新图上传。头像/封面/截图/文章插图分别使用不同 Cloudinary 文件夹。

## 前台 Web（`frontend/`）

- Nuxt 4 默认 `app/` 作为源码目录；Tailwind v4 通过 `vite.plugins: [tailwindcss()]` 接入，样式在 `app/assets/css/main.css`。项目**只有深色模式**，无 Element Plus/Pinia。
- 设计体系：`app.vue` 全屏背景 + 深色遮罩 + 玻璃卡片（`.glass-panel`、`.glass-card`、`.btn-primary` 等）；`useAppearance` 管理背景图/亮度/遮罩，持久化到 `localStorage` 的 `fishmo_appearance`，默认 `/background/2.jpg`。
- API 基地址：`useApiBase()` 在 SSR 用私有 `runtimeConfig.apiBaseServer`，浏览器用 `public.apiBase`；生产 `public.apiBase='/api'`，SSR 仍直连后端。浏览器端有“回环地址防呆”，线上配置成 localhost 会回退 `/api`。
- `useApi()` 统一注入 Bearer、拆开 `{msg, code, data}`、抛 `ApiError`；401 时清空登录态（可用 `keepAuthOn401` 关闭）。
- 登录态：`useAuth()` 使用 `useState`（`auth-token` / `auth-user` / `auth-ready`），持久化 key 为 `fishmo_access_token`、`fishmo_user`；`plugins/auth.client.ts` 在客户端恢复，SSR 不读 localStorage。UI 依赖登录态时必须用 `ready` / `mounted` 门控，避免水合不一致。
- 路由守卫 `middleware/auth.ts` 只在客户端运行：未登录时打开全局 `AuthDialog` 并跳回首页，登录后按 `?redirect` 返回原页面。发布页与个人管理页使用该守卫。
- 数据获取：公开页面用 `useAsyncData` + SSR；key 通常包含 `route.fullPath`（如 `games-${route.fullPath}`）。列表筛选全部由 URL query 驱动。依赖 token 的私有数据使用 `server: false`。
- 评论渲染使用后端已消毒的 HTML（`v-html`）；文章 Markdown 由 `utils/markdown.ts` 渲染，`html: false`。
- 图片上传先用 `utils/file.ts` 在浏览器缩放并转 WebP base64，再提交给后端。
- 类型集中在 `app/types/index.ts`，与后端 schemas 对齐；枚举线上传中文值（`"电脑端"`、`"剧情向"`）。

## 管理端（`admin/`）

- 独立 Nuxt 4 SPA（`ssr: false`，端口 3001），共享前台深色玻璃风格，但**独立登录态**：`fishmo_admin_token` / `fishmo_admin_user`。
- `useAdminAuth.login()` 复用 `/api/v1/user/login`，客户端拒绝非 `is_admin` 账号；后端每个管理端点还会回库校验管理员身份。
- `middleware/auth.global.ts` 对所有页面生效：未登录跳 `/login?redirect=...`；登录页 `layout: false`。
- `useAdminApi()` 负责 Bearer、信封解包、401 清理并跳登录页。
- 页面：概览（`index.vue`）、游戏审核（`games.vue`）、用户管理（`users.vue`）、文章管理（`articles.vue`）。审核/下架/禁用等操作成功后刷新列表。

## 修改代码时的硬性约定

1. **后端命令必须在 `app/` 下执行**；新增文件使用 `from config import ...`、`from models import ...` 这类绝对导入。
2. **新接口成功响应必须用 `info()`**；错误抛 `AppError` 子类，不要手写 `JSONResponse`。
3. **任何写操作都要考虑缓存失效**：至少 bump 对应域版本号并删除相关列表/详情 key；涉及评论数时同步文章缓存。
4. **新增集合关系一律 `lazy="raise"`**，查询时显式 `selectinload`；删除聚合时优先用 Core `delete` + 手动关联删除。
5. **接口契约变更三处同步**：后端 `schemas/` + `services/` 的响应构造函数、前台 `app/types/index.ts`、管理端 `admin/app/types/index.ts`（若涉及）。
6. **异步端点不要直接调用同步图片/邮件函数**，用 `asyncio.to_thread`（或 `ImageService`）。
7. **SSR 水合**：不要在渲染期直接读 `localStorage`/`window`；用客户端插件或 `onMounted`，并用 `ready`/`mounted` 门控依赖登录态的 UI。
8. 新增页面路由注意静态路径先于 `/{id}` 动态路由。
9. 不提交 `app/.env`、`logs/`、构建产物；仓库当前无自动化测试，改完至少运行后端 import、两端 `nuxi typecheck` 与 `npm run build`，并手动验证相关接口。