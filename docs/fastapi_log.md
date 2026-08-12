# fishmo 修改与报错记录（fastapi_log.md）

> 作用：记录后端开发过程中的**代码修改**与**报错/排查**过程，便于追溯。
> 记录区间：2026-08-06 ~ 2026-08-12
> 说明：文档如实记录，包含已修复、待处理、待确认三类条目。

## 目录

- [1. 修改记录](#1-修改记录)
- [2. 报错/缺陷排查记录](#2-报错缺陷排查记录)
- [3. 遗留未修（测试阶段刻意跳过）](#3-遗留未修测试阶段刻意跳过)
- [4. 待用户确认的改动](#4-待用户确认的改动)
- [5. 既有已知问题（尚未处理）](#5-既有已知问题尚未处理)

---

## 1. 修改记录

### 1.1 图片工具：`utils/we-bp.py` → `utils/webp.py` 重命名

- **文件**：`backend/app/utils/webp.py`（原 `we-bp.py`，已删除）
- **原因**：文件名含连字符 `we-bp.py`，`import utils.we-bp` 为非法语法，代码不可达（孤儿代码）。
- **修复**：重命名为 `webp.py`；在 `utils/__init__.py` 导出转换/上传函数。

### 1.2 `utils/webp.py` 批量上传崩溃修复

- **根因**：`convert_image_to_webp` 失败返回 `None`，`None` 混入转换列表；批量上传循环对 `None` 做 `res['status']` 下标 → `TypeError` 500。
- **修复**：转换函数在源头过滤 `None`（失败即跳过）；批量上传对返回结果判空后再取字段。

### 1.3 `utils/webp.py` 消除二次有损转码

- **根因**：批量函数先 `convert_images_to_webp` 转一次，`upload_image_to_cloudinary` 内部又转一次（webp→webp 二次压缩，画质损失 + 浪费 CPU）。
- **修复**：抽出私有 `_upload_webp()`，每张图只转换一次、只上传一次。

### 1.4 `utils/webp.py` 补反压缩炸弹（DoS）防护

- **修复**：
  - `MAX_IMAGE_BYTES = 5MB`：base64 解码后、PIL 打开前拒收超大输入。
  - `MAX_IMAGE_PIXELS = 50MP`：解码后、缩放前检查像素总量。
- 另将 `print()` 改为 `logging`、`floder`→`folder`、补正确类型注解、`Image.Resampling.LANCZOS`、上传加 `data:image/webp;base64,` 前缀、quality 统一 75、`cloud_name` 改环境变量读取。

### 1.5 依赖清单补全

- **文件**：`requirements.txt`
- **修改**：新增 `cloudinary==1.45.0`（此前仅 .venv 手动安装，新环境会 `ModuleNotFoundError`）。
- 备注：`resend` 仍未入清单（见[第 5 节](#5-既有已知问题尚未处理)）。

### 1.6 `config/db.py` 导入修复

- **文件**：`backend/app/config/db.py`
- **修改**：`from security import ASYNC_DATABASE_URL` → `from config.security import ASYNC_DATABASE_URL`。
- 详见[报错 #2.1](#21-modulenotfounderror-no-module-named-security)。

### 1.7 `api/v1/user.py` 更新路由修复

- **`update` 改用 `AccountUpdate`**（全可选字段）：改资料不再强制带密码，不再误触发改密。
- **头像 bug 修复**：`data.avatar = image`（改请求对象）→ 写回 `user.avatar = result["url"]`；上传结果判空，失败返回 `400 头像上传失败`。
- **同步阻塞**：`upload_image_to_cloudinary`、`pwd_context.hash` 用 `run_in_threadpool` 包裹。
- **唯一索引兜底**：commit 捕获 `IntegrityError` → `400 用户名或邮箱已存在`。
- **401 语义统一**：`security = HTTPBearer(auto_error=False)`，`update`/`delete` 的 credentials 改 `Optional[...]`。

### 1.8 `utils/verify_user.py` 修复

- **删除** `print("TOKEN:", token)`（Token 明文泄露到日志）。
- **`verify_login` 支持 None**：缺 token 时返回 `401 未提供凭证`（配合 1.7 的 `auto_error=False`）。

### 1.9 `schemas/user.py` 新增模型

- **新增** `AccountUpdate`：`username?/password?/email?/avatar?/bio?` 全可选，供 `PUT /update` 使用。
- `Account`（注册用）保持不变。

### 1.10 `config/security.py` 新增配置

- **新增** `CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")`。
- 注：API key/secret 沿用历史拼写 `CLOUNDDINARY_API_KEY/SECRET`（兼容现有 .env，未改名）。
- ~~后续已改为「正确拼写优先 + 旧拼写兜底」，本条记录已过时，见 [1.15](#115-configsecuritypy-cloudinary-变量兼容改造)。~~

### 1.11 新增 galgame 业务模块

- **文件**：`model/galgame.py`、`model/enums.py`（新建）、`schemas/galgame.py`、`api/v1/galgame.py`、`api/v1/__init__.py`、`main.py`。
- **内容**：
  - 新增 `galgame` 表：三名称（cn/en/jp）、内容、公司、分类、封面、截图、标签、浏览量/点赞/收藏、平台枚举、`author_id` 外键（`ondelete=RESTRICT`）。
  - 新增 5 个端点：`GET /`（列表）、`GET /{id}`（详情+浏览量）、`POST /add`、`DELETE /delete`、`PUT /edit`。
  - 列表/详情均走 Redis 版本化缓存（key 带 `search_version`）。
- **业务规则**：`add` 时 `status=True`（作者即发布者，新增即公开）。

### 1.12 代码审核与批量修复（8 Critical + 15 Major）

- **背景**：对 galgame 新代码做五维审核（架构/性能/安全/可维护/测试），发现 8 个 Critical + 15 个 Major。
- **修复范围**（明细见 [2.8](#28-代码审核发现的阻塞性缺陷本会话)）：
  - visit 缓存命中判断写错变量（永远返回 null）、`set_to_cache` 参数顺序颠倒、404 检查死代码、`get_search_version()` 缺 await。
  - `or_()` 关键字参数 TypeError、`images`/`cover` 未初始化 UnboundLocalError、delete 对 Row 调 `db.delete()`。
  - 过滤条件 `stmt.where()` 结果丢弃、总数口径不一致、集合侧 `lazy="selectin"` 性能红线、同步上传阻塞事件循环、缓存失效 pattern 不匹配 / edit 无失效、Cloudinary 变量兼容、`size` 无上限、model 反向依赖 schemas 等。
- **状态**：✅ 除 `User.name` 引用错误（见 [3.9](#39-新增galgame-列表接口-user-name-引用错误)）外，其余全部修复。

### 1.13 `edit` 端点补全

- **文件**：`api/v1/galgame.py`。
- **背景**：原 `edit` 端点残缺（无 commit / 无 return / 无缓存失效）。
- **修复**：补 `await db.commit()`、返回体、缓存清理 + `update_version()`；并支持 `cover`/`images` 更新（`run_in_threadpool` 上传，失败返回 500）。

### 1.14 `User.galgames` 集合侧 `lazy="raise"`

- **文件**：`model/user.py`。
- **原因**：集合侧 `lazy="selectin"` 会让任何 User 查询（登录/注册/查询用户/galgame 的 join）全量加载其 galgames，用户与作品越多越致命。
- **修复**：改为 `lazy="raise"`，需要时显式 `selectinload()`；已确认全仓库无代码访问该集合。

### 1.15 `config/security.py` Cloudinary 变量兼容改造

- **文件**：`config/security.py`。
- **背景**：变量曾用历史拼写 `CLOUNDDINARY_API_KEY/SECRET`；审核指出注释与代码自相矛盾，且旧 .env 用拼写错误名。
- **修复**：优先读正确拼写、找不到时回退旧拼写，兼容新旧 .env：
  ```python
  CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY") or os.getenv("CLOUNDDINARY_API_KEY")
  ```
  secret 同理；注释同步更新。本项覆盖 1.10 的"未改名"记录。

### 1.16 新建 `model/enums.py`（依赖方向修正）

- **文件**：`model/enums.py`（新建）。
- **背景**：`PlatformEnum` 原定义在 `schemas/galgame.py`，model 层反向 import schemas 层，依赖方向反了。
- **修复**：枚举下沉为独立领域模块，model 与 schemas 共同引用，单一来源。

---

## 2. 报错/缺陷排查记录

### 2.1 ModuleNotFoundError: No module named 'security'

- **位置**：`config/db.py:3`
- **报错**：`from security import ASYNC_DATABASE_URL` → `ModuleNotFoundError: No module named 'security'`。`main.py` 无法启动。
- **根因**：`security` 不是顶层模块（实际是 `config/security.py`），`from security import` 违反「相对 `backend/app` 的绝对导入」约定。
- **修复**：改为 `from config.security import ASYNC_DATABASE_URL`。
- **状态**：✅ 已修复，`main.py` 可正常导入。

### 2.2 TypeError: 'NoneType' object is not subscriptable（原 we-bp.py 批量上传）

- **触发**：任一图片转换失败时批量上传必然 500。
- **根因**：`convert_image_to_webp` 失败返回 `None` 且混入列表，`convert_images_to_webp` 的 `except` 是死代码；后续 `res['status']` 对 `None` 下标。
- **修复**：见[修改 1.2](#12-utilswebppy-批量上传崩溃修复)。
- **状态**：✅ 已修复（冒烟测试覆盖：损坏图跳过、上传失败返回 None 不崩溃）。

### 2.3 ImportError: cannot import name 'CLOUDINARY_API_KEY' from 'config.security'

- **触发**：webp.py 初稿按正确拼写 `CLOUDINARY_API_KEY` 导入。
- **根因**：`security.py` 变量名是历史拼写错误 `CLOUNDDINARY_API_KEY/SECRET`。
- **修复**：webp.py 导入对齐历史拼写。
- **状态**：✅ 已修复。

### 2.4 AttributeError: module 'cloudinary' has no attribute '__version__'

- **触发**：验证脚本用 `cloudinary.__version__` 查版本。
- **根因**：cloudinary 包不暴露 `__version__`；经 `pip show cloudinary` 确认版本为 1.45.0。
- **状态**：⚠️ 验证脚本问题，非应用缺陷。

### 2.5 SQLAlchemy 子句 `bool()` 报错（仅测试脚本）

- **触发**：冒烟测试脚本 `str(getattr(stmt, 'whereclause', '') or '')`，`or` 对 SQLAlchemy 子句求值触发 `TypeError: Boolean value of this clause is not defined`。
- **根因**：测试脚本问题，`or ''` 对子句对象调 `bool()`。
- **修复**：改用 `str(stmt.whereclause)`。
- **状态**：✅ 测试脚本已修，非应用代码问题。

### 2.6 二次有损转码（逻辑缺陷）

- **说明**：批量上传对每张图转两次 WebP。非崩溃报错，属逻辑缺陷。
- **修复**：见[修改 1.3](#13-utilswebppy-消除二次有损转码)。
- **状态**：✅ 已修复。

### 2.7 Token 打印泄露（安全缺陷）

- **说明**：`verify_user.py` 的 `print("TOKEN:", token)` 把明文凭证写进日志。
- **修复**：删除该行。
- **状态**：✅ 已修复。

### 2.8 代码审核发现的阻塞性缺陷（本会话）

> 来源：对 galgame 模块的五维代码审核报告（Critical 级）。逐项已修复，除 [2.9](#29-galgame-列表接口-user-name-引用错误) 外。

| # | 缺陷 | 位置 | 根因 / 修复 |
| --- | --- | --- | --- |
| 1 | visit 永远返回 null | `galgame.py` visit | 缓存命中判断写成 `if cache_key:`（恒真）→ 改 `if cache_data:` |
| 2 | `set_to_cache` 参数颠倒 | visit | key/value 传反 → `set_to_cache(cache_key, data, ...)` |
| 3 | 404 检查是死代码 | visit | `row` 为 None 先解包抛 TypeError → 先判空再解包 |
| 4 | `get_search_version()` 缺 await | index / visit | 缓存 key 含协程对象、永不命中 → 补 `await` |
| 5 | 引用不存在的 `User.name` | index | 模型只有 `username` → ⚠️ 见 [2.9](#29-galgame-列表接口-user-name-引用错误) |
| 6 | `or_()` 关键字参数 TypeError | add | 改为条件列表 + `or_(*conditions)`，只比较非空名称 |
| 7 | `images`/`cover` 未初始化 | add | `UnboundLocalError` → 条件块前绑定默认值 |
| 8 | delete 对 Row 调 `db.delete()` | delete | `select(Galgame.id, author_id)` 返回元组 → 改查完整 ORM 对象 |
| 9 | 同步上传阻塞事件循环 | add/edit | PIL+HTTP 同步调用 → `run_in_threadpool` 包裹 |
| 10 | 过滤条件静默失效 | index | `stmt.where()` 返回值丢弃 → 集中为 `filters` 列表单处应用 |
| 11 | 总数口径不一致 / total 是页数 | index | count 复用同一组 WHERE，`total` 返回真实总条数 |
| 12 | `lazy="selectin"` 性能红线 | model/user.py | 集合侧改 `lazy="raise"` |

- **状态**：✅ 已修复（编译、import、OpenAPI、Pydantic 校验器均验证通过）。

### 2.9 galgame 列表接口 `User.name` 引用错误

- **位置**：`api/v1/galgame.py` `index`（`select(... User.name, User.avatar)`）。
- **报错**：`AttributeError: type object 'User' has no attribute 'name'`，列表接口 `GET /api/v1/galgame/` 直接 500。
- **根因**：模型字段为 `username`（`model/user.py`），查询误写 `User.name`。import 时不会报错（运行时才求值），故此前 `import main` 验证通过未暴露。
- **状态**：⚠️ **未修复**，见 [第 3 节 #9](#39-新增galgame-列表接口-user-name-引用错误)。

---

## 3. 遗留未修（测试阶段刻意跳过）

> 由用户明确决定本轮不修，供后续回归。新增项标注来源。

| # | 项 | 位置 | 风险 |
| --- | --- | --- | --- |
| 1 | JWT 无过期时间（`exp` 未设置） | `user.py` 登录签发 / `security.py` | token 泄露即永久有效 |
| 2 | 邮箱换绑无验证码校验 | `user.py` update 的 email 分支 | 改绑邮箱无归属验证 |
| 3 | 硬删除改软删除 | `user.py` delete | 破坏外键/历史引用（模型已有 `status` 字段可用） |
| 4 | `update_version()` 无异常兜底 | `user.py` update/delete、`galgame.py` | Redis 故障会让已成功的业务请求 500 |
| 5 | `int(payload['sub'])` 缺防御 | `verify_user.py` | `KeyError`/`ValueError` 可能漏成 500 |
| 6 | `login/register` 密码哈希未包线程池 | `user.py` login/register | argon2 慢哈希阻塞事件循环 |
| 7 | `register` 无 IntegrityError 兜底 | `user.py` register | 并发注册撞唯一索引 → 500 |
| 8 | `Account.password` 仅 6 位 | `schemas/user.py` | 弱口令 |
| 9 | 【新增·Critical】galgame 列表接口 `User.name` 引用错误 | `galgame.py` index | 字段不存在 → `GET /api/v1/galgame/` 返回 500（详见 [2.9](#29-galgame-列表接口-user-name-引用错误)） |

> 补充：第 3 项部分缓解——`delete` 已捕获关联作品 `IntegrityError` 返回 400，但仍是物理删除，未利用 `status` 做软删除。

---

## 4. 待用户确认的改动

> 以下两项已合并进当前代码，视为用户已确认保留。原为审核子代理越权改动，已如实上报。

| # | 改动 | 说明 | 当前状态 |
| --- | --- | --- | --- |
| 1 | `pytest/verify_email.py` → `test/verify_email.py` | 内容逐字节相同（仅换行符差异），纯文件移动 | ✅ 已合并（`test/` 目录现存 `verify_email.py` / `verify_cloud.py`，无 `pytest/` 目录） |
| 2 | `config/__init__.py` 新增导出 | 追加 `ASYNC_DATABASE_URL` / `RESEND_API_KEY` / `CLOUDINARY_*` | ✅ 已合并（当前 `config/__init__.py` 已含这些导出，供 `from config import ...` 使用） |

---

## 5. 既有已知问题（尚未处理）

> 源自既有框架文档 + 本次审核建议，已修复的不再重复列，以下为仍存在项。

1. **CORS**：`allow_origins=["*"]` + `allow_credentials=True` 组合不符合浏览器规范且有安全风险，生产需白名单化。
2. **`resend` 未入 `requirements.txt`**：venv 已装 2.35.0，新环境按清单安装后邮件功能会 `ImportError`（已复核 requirements.txt，仍未补）。
3. **无 Alembic 迁移 / 无 `create_all`**：`user`/`galgame` 表需手动创建，结构漂移靠人眼比对。
4. **无请求级日志/可观测性**：全程 `print`/`logging`，无结构化日志、无 trace_id（`sentry-sdk` 已装未用）。
5. **`email/send` 的 `email` 是 query 参数**：既有框架文档误写为 body，实际为 `?email=xxx`（已以 router.md/OpenAPI 为准）。
6. **无测试、无 lint、无 CI**：本次审核建议引入 `ruff`（未使用导入/拼写）、`mypy`（类型错误，可拦截 `User.name` 这类问题）、`pytest`（核心路径补测试，含查询条数断言防 `selectin` 回归）。
7. **字段拼写**：`platfrom`（应为 platform）、`update_at`（应为 updated_at）为既有拼写，改动需数据库迁移。
8. **galgame 列表排序不稳定**：`order_by(updated_at)` 无次级排序，同值记录分页可能重复/遗漏。
