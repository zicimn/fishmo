# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概览

`fishmo` 是一个 **galgame（美少女游戏）信息发布社区 + 文章博客** 全栈项目。后端核心业务涵盖两个业务域：

**Galgame 域**：用户注册/登录、邮箱验证码、发布游戏（三名称/简介/封面/截图/标签/平台）、浏览量计数与 Redis 版本化缓存、随机游戏，以及围绕游戏的**链接分享**、**评论**、**收藏**三个扩展模块，外加**全文搜索**与**管理员审核**功能。

**Article 域**：文章发布（Markdown 编辑器）、文章列表（分类筛选/分页）、文章详情（Markdown 渲染 + 插图画廊 + 评论区），以及个人文章管理。

前端（Nuxt 3 + Element Plus）具有完整业务页面：首页（精选 Hero + 文章弹出面板）、全部游戏、全部文章、游戏详情、文章详情、发布游戏/文章、个人中心、管理员控制台，以及**设置面板**（外观/背景主题调节）。

技术栈：**Python 3.11+ / FastAPI 0.133 / SQLAlchemy 2.0 异步 / aiomysql / Pydantic v2 / python-jose(JWT) / passlib(argon2) / redis.asyncio / cloudinary（图片上传） / Nuxt 3 / Vue 3 / TypeScript / Element Plus / Pinia / markdown-it + DOMPurify**。代码注释为中文。

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

**重要**：`main.py` 里的 `uvicorn.run("main:app", ...)` 使用模块字符串，从仓库根或 `backend/` 运行会报 `ModuleNotFoundError`。项目目前**没有**测试、lint 配置或 CI；`test/` 下是手动验证脚本，非 pytest。

### 前端

```bash
cd frontend
npm install
npm run dev                             # Nuxt 3 开发服务器
npm run build                           # 生产构建（含 vue-tsc 类型检查）
npx nuxi typecheck                      # 仅类型检查
```

> 接口清单与请求/响应格式见 `docs/router.md`；开发修改与报错记录见 `docs/fastapi_log.md`。

## 架构与分层约定

```
backend/app/
  main.py                    — 应用入口：FastAPI 实例、CORS 中间件、include_router、lifespan（定时任务 + 引擎释放）
  api/service/               — 路由层（每域独立文件）：user.py、email.py、galgame.py（含 rvisit 随机游戏）、
                                link.py、comment.py、favorite.py、search.py、article.py
  api/admin/                 — 管理员路由：control.py（审核/删除游戏，前缀 /api/admin/control）
  config/                    — 基础设施配置：db.py（异步引擎/会话）、cache.py（Redis + 版本化缓存）、security.py（JWT + 环境变量）
  model/                     — SQLAlchemy ORM 模型：user.py、galgame.py、link.py、comment.py、favorite.py、article.py、enums.py
  schemas/                   — Pydantic v2 请求/响应模型：user.py、galgame.py、link.py、comment.py、article.py
  utils/                     — email.py（Resend 验证码）、verify_user.py（JWT 校验 + 管理员校验）、
                                webp.py（图片转换 + Cloudinary 上传）、counter.py（浏览量计数，含 Galgame + Article 双计数器）、
                                scheduler.py（定时落库）
  default/                   — 默认值：file.py（默认封面 URL）

frontend/
  pages/                     — 页面：index（首页）/ games（游戏列表）/ articles（文章列表）/ user（登录注册）/ admin（控制台）/
                                publish（发布游戏）/ galgame/[id]（游戏详情）/ article/[id]（文章详情）/
                                manage/index（管理） / manage/[id]（编辑游戏）/ manage/article/[id]（编辑文章）
  components/                — 组件：article/（ArticleForm 发布表单、ArticlePopup 首页弹出面板）、
                                comment/CommentList.vue（评论列表，支持 galgame + article 双类型）、
                                galgame/（GalgameForm 发布表单、GameCard 游戏卡片）、
                                link/（LinkList、LinkManage）、manage/（MyGames、MyArticles、MyComments、MyLinks）、
                                user/（MyFavorites、ProfileForm）
  composables/               — 组合函数：useAuth / useGalgame / useComment / useLink / useFavorite / useArticle / useColorMode
  stores/                    — Pinia 状态：auth.ts（token/isAdmin/userId/username/avatar，持久化到 localStorage）
  middleware/                — 路由守卫：auth.ts（登录守卫）、admin.ts（管理员守卫）
  types/                     — TypeScript 类型定义：index.ts（统一导出）、user.ts、galgame.ts、link.ts、comment.ts、article.ts
  layouts/                   — 默认布局：default.vue（顶栏含文章导航链接 + 搜索飞出面板 + 设置面板 + 随机游戏 + 移动端抽屉）
  utils/                     — request.ts（统一 API 请求，含自动 Bearer token 注入 + 401 处理）、
                                file.ts（图片 base64 转换）、link.ts（URL 安全校验）、color.ts（封面主色提取）、format.ts（大小格式化）
  plugins/                   — auth.client.ts（localStorage 登录态恢复）、element-plus.ts（EP 全局注册）
```

### 路由注册总表

| 路由文件 | 前缀 | 端点 |
| --- | --- | --- |
| `api/service/user.py` | `/api/v1/user` | login / register / update / delete / index(查看用户信息) |
| `api/service/email.py` | `/api/v1/email` | send |
| `api/service/galgame.py` | `/api/v1/galgame` | index(列表) / visit(详情) / rvisit(随机) / add / delete / edit |
| `api/service/link.py` | `/api/v1/link` | get_list(按游戏) / get_list_by_user / add / review(编辑) / delete |
| `api/service/comment.py` | `/api/v1/comment` | get_list(按目标, 支持 ?type=galgame\|article) / get_list_by_user / add / edit / delete |
| `api/service/favorite.py` | `/api/v1/favorite` | add / remove / visit(检查是否收藏) / list |
| `api/service/search.py` | `/api/v1/search` | search |
| `api/service/article.py` | `/api/v1/article` | index(列表, 支持 ?category) / visit(详情) / manage(个人管理) / add / edit / delete |
| `api/admin/control.py` | `/api/admin/control` | BrowseGal / UpdateStatus / DeleteGal |

平台即用户：`delete`/`edit` 必须校验 `author_id == 当前用户`，非作者返回 403。删除用户时若其下有作品（galgame/article），外键 `ondelete="RESTRICT"` 触发 `IntegrityError`，`user.py` 已捕获返回 400。

### 评论多态（receive_type）

评论系统通过 `receive_type` 字段实现多态，支持同时为 galgame 和 article 两个业务域服务：

- `ReceiveEnum.article = 0` → 文章评论
- `ReceiveEnum.galgame = 1` → 游戏评论

评论列表端点 `GET /api/v1/comment/{target_id}?type=galgame|article` 根据 type 参数设置 `receive_type` 过滤。添加评论时同理。ORM 层面 `receive_id` 为裸 Integer（无外键约束），兼容多态目标。

### 浏览量计数

两个业务域各自独立的 Redis 哈希表 + 定时落库：

- `ViewCounter`（HASH_KEY = `"gal_views"`）→ 游戏浏览量，同步到 `Galgame.views`
- `ArticleViewCounter`（HASH_KEY = `"article_views"`）→ 文章浏览量，同步到 `Article.views`

定时任务（`utils/scheduler.py`）批量将增量写入数据库。详情端点使用 `incr()` 的实时 delta + 数据库存储值计算展示总数（`views_total + delta`）。

### 数据层（config/db.py、model/）

- SQLAlchemy 2.0 异步风格：`create_async_engine` + `async_sessionmaker`，MySQL 驱动 `aiomysql`。
- `get_db()` 是一个 yield 依赖：正常自动 commit、异常回滚并重新抛出、finally 关闭会话。所有端点通过 `db: AsyncSession = Depends(get_db)` 注入。
- **连接串来自环境变量**：`db.py` 用 `from config.security import ASYNC_DATABASE_URL`（非硬编码）；变量由 `backend/app/.env` 提供（`security.py` 的 `load_dotenv()` 按 CWD 加载，故须在 `backend/app` 下运行）。
- **无 Alembic 迁移**：所有表需手动创建。
- **关系加载**：集合侧（`.galgames` / `.links` / `.comments` / `.favorites` / `.articles`）均为 `lazy="raise"`——**任何查询都不应隐式全量加载关联集合**，需要时显式 `selectinload()`；多对一侧（`.author` / `.galgame`）保持 `lazy="selectin"`。

### 共享枚举（model/enums.py）

`PlatformEnum`、`CategoryEnum`、`ReceiveEnum`、`SizeUnitEnum`、`SearchEnum` 定义在 `model/enums.py`（model 与 schemas 共同引用）。**model 层禁止反向依赖 schemas 层**，跨层共享的常量一律下沉到 `model/enums.py`。

### 前端架构重要约定

- **深色模式独家**：项目已移除亮色模式，仅保留深色模式。`nuxt.config.ts` 内联脚本始终添加 `dark` class。`useColorMode.ts` 仅返回 `isDark: ref(true)`。
- **SSR 水合一致性**：`layouts/default.vue` 使用 `isMounted` 门控，挂载前统一渲染"未登录"状态，避免水合 mismatch。
- **路由守卫**：`middleware/auth.ts`（登录守卫）、`middleware/admin.ts`（管理员守卫，客户端判断，SSR 阶段放行）。
- **类型对齐**：`types/` 下的 TypeScript 类型与后端 `schemas/` 严格对齐，枚举传输中文值（如 `"电脑端"`、`"剧情向"`）。
- **前端请求代理**：`nuxt.config.ts` 的 `routeRules: { '/api/**': { proxy: process.env.NUXT_API_BASE || 'http://localhost:8000' } }`，前后端开发时通过 Nitro 代理规避 CORS。`utils/request.ts` 的 `api()` 自动附加 `Authorization` 头、401 时清理登录态并跳转。
- **设置面板与背景系统**：`layouts/default.vue` 内嵌 `el-dialog` 设置面板（左右结构：菜单侧栏 + 内容区），外观 Tab 控制 `--fish-brightness`/`--fish-alpha`/`--fish-shadow-intensity` CSS 变量，背景 Tab 用 `import.meta.glob` 发现 `public/background/` 图片并设置 `--fish-bg-image`。所有设置持久化到 localStorage。
- **卡片透明化**：GameCard、MyGames、MyArticles 等卡片设置 `background: transparent`，露出 body 的背景图片与深色遮罩层。
- **状态插图**：错误/空状态统一使用 `public/status/1.png`（加载失败）或 `public/status/2.png`（空数据）。

### 导航栏链接

顶栏导航包含：首页、全部游戏、随机（触发 `/api/v1/galgame/rvisit`）、文章（指向 `/articles`）、发布（登录后显示）、登录/注册（未登录显示）。移动端抽屉同步包含以上链接。

### 认证与安全（config/security.py、utils/verify_user.py）

- JWT（HS256）：`SECRET_KEY` / `ALGORITHM` 从 `config.security` 导入。变量均由环境变量注入（`backend/app/.env`），**无代码内默认值**，缺 `.env` 时 `SECRET_KEY` 为 None、JWT 签发/校验会失败。
- JWT payload 包含 `{sub: str(user.id), username, is_admin}`。
- 密码哈希：`passlib` 的 `CryptContext(schemes=["argon2"])`。
- **用户鉴权**：路由内 `security = HTTPBearer(auto_error=False)`，业务端点先 `verify_login(credentials)` 解析 user_id；缺 token / token 无效统一 `401`。
- **管理员鉴权**：`verify_admin(credentials)` 解析 JWT 中的 `is_admin` 字段，非管理员返回 `False`（admin 端点据此返回 `403`）。

### 缓存（config/cache.py）

- `redis.asyncio` 客户端（localhost:6379），惰性连接，不阻塞启动。
- 提供 `get_from_cache` / `set_to_cache` / `delete_cache` / `delete_cache_pattern` / `get_cache_key`，以及基于版本计数器的版本化缓存失效模式（`get_search_version` / `update_version`）。
- **版本计数按业务域拆分**：`GAL_VERSION_KEY` / `LINK_VERSION_KEY` / `COMMENT_VERSION_KEY` / `ARTICLE_VERSION_KEY`（全局 `SEARCH_VERSION_KEY` 保留向后兼容），某域增删改只自增该域版本号。
- **约定**：列表/详情缓存 key 一律带 `version`；**任何增删改成功都必须 `await update_version(对应域KEY)` 并使相关 key 失效**，否则缓存继续服务旧数据。注意所有缓存函数均为 async，必须 `await`。

### 图片上传（utils/webp.py）

- 全部为**同步函数**（PIL 解码 CPU 密集 + Cloudinary 同步 HTTP），从 async 端点调用必须用 `run_in_threadpool` 包裹（或 `asyncio.to_thread`），否则阻塞事件循环。
- 反压缩炸弹防护：单图 base64 解码后 ≤ 5MB、像素 ≤ 50MP；**失败返回 `None`，调用方必须判空**，不能把 None 当成功结果用。
- 统一转 WebP（quality 75）等比缩放后上传，返回 `{status, url, public_id}` 或 `{status: False, error}`。
- 编辑时已托管 URL（`http://`/`https://` 开头）直接复用，不重复上传；仅 base64 新图走上传流程。

## 文章模块说明

### 后端

- **模型**（`model/article.py`）：`Article` 表含 `title`/`content`(Text)/`cover`/`category`(逗号分隔String)/`tag`(JSON)/`images`(JSON)/`status`(bool)/`views`(int)/`author_id`(FK→user)。
- **路由**（`api/service/article.py`）：
  - `GET /` — 公开列表（只返回 status=True），支持 `?category` LIKE 筛选 + 评论数子查询 + 分页 + Redis 缓存
  - `GET /{id}` — 详情（浏览量计数 + 缓存，管理员可查看未公开）
  - `GET /manage` — 个人管理列表（仅作者，`?page&size`）
  - `POST /add` — 发布（自动 status=True，图片上传 Cloudinary）
  - `PUT /edit` — 编辑（校验作者身份）
  - `DELETE /delete` — 删除（校验作者身份）
- **缓存失效**：任何增删改后 `delete_cache_pattern("Article:*")` + `update_version(ARTICLE_VERSION_KEY)`。

### 前端

- **文章列表页**（`pages/articles/index.vue`）：4 列网格布局，分类标签筛选（攻略/资讯/公告/教程/其他），16:10 封面，浏览量/评论数徽标，分页，SSR 友好。
- **文章详情页**（`pages/article/[id].vue`）：Markdown 渲染（markdown-it + DOMPurify），21:9 宽幅封面（移动端 16:9），统计数据行，标签链接，插图画廊（预览模式），评论区（`CommentList type="article"`）。
- **文章发布页**（`components/article/ArticleForm.vue`）：双栏布局（左侧栏：分类/标签/封面设定，右侧：标题 + Markdown 编辑器 + 工具栏 + 预览切换 + 插图上传），草稿自动保存（localStorage，每 30s + 内容变更触发）。
- **文章编辑页**（`pages/manage/article/[id].vue`）：复用 ArticleForm + 作者身份校验。
- **管理组件**（`components/manage/MyArticles.vue`）：小型卡片网格（仅 name + cover），编辑/删除按钮，类似 GameCard 风格。
- **首页文章弹出面板**（`components/article/ArticlePopup.vue`）：4 列网格，快速浏览文章列表，入口指向 `/articles`。

## 已知限制（开发时需注意）

1. **JWT 无过期时间**：`jwt.encode` 未带 `exp`，token 签发后永久有效。
2. **CORS**：`allow_origins=["*"]` + `allow_credentials=True` 组合不符合浏览器规范，生产需白名单化。
3. **无 Alembic 迁移**：表结构变更需手动 DDL，model 文件变更后务必同步数据库。
4. **字段拼写**：`platfrom`（应为 platform）、`update_at`（应为 updated_at）为既有拼写，改动需数据库迁移。
5. **无测试/lint/CI**：修改后需手动验证。
6. **`logs/` 目录不应纳入版本控制**：需在 `.gitignore` 中添加 `logs/` 和 `*.log`。
7. **无输入净化/XSS 防护**：评论内容、文章内容等用户输入字段在存储前未做 sanitize。前端仅通过 DOMPurify 在**渲染时**消毒 Markdown 输出，数据库层存储原始内容。如需 HTML 富文本场景，需补充后端 `sanitize_html()` 逻辑。
8. **无边限流**：登录、评论、发送验证码等端点无防滥用限流，后续可在 `config/cache.py` 中补充 `rate_limit()` 后接入。