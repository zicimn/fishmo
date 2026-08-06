# fishmo 修改与报错记录（fastapi_log.md）

> 作用：记录后端开发过程中的**代码修改**与**报错/排查**过程，便于追溯。
> 记录区间：2026-08-06（本轮会话）
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

---

## 3. 遗留未修（测试阶段刻意跳过）

> 由用户明确决定本轮不修，供后续回归。

| # | 项 | 位置 | 风险 |
| --- | --- | --- | --- |
| 1 | JWT 无过期时间（`exp` 未设置） | `user.py` 登录签发 / `security.py` | token 泄露即永久有效 |
| 2 | 邮箱换绑无验证码校验 | `user.py` update 的 email 分支 | 改绑邮箱无归属验证 |
| 3 | 硬删除改软删除 | `user.py` delete | 破坏外键/历史引用（模型已有 `status` 字段可用） |
| 4 | `update_version()` 无异常兜底 | `user.py` update/delete | Redis 故障会让已成功的业务请求 500 |
| 5 | `int(payload['sub'])` 缺防御 | `verify_user.py` | `KeyError`/`ValueError` 可能漏成 500 |
| 6 | `login/register` 密码哈希未包线程池 | `user.py` login/register | argon2 慢哈希阻塞事件循环 |
| 7 | `register` 无 IntegrityError 兜底 | `user.py` register | 并发注册撞唯一索引 → 500 |
| 8 | `Account.password` 仅 6 位 | `schemas/user.py` | 弱口令 |

---

## 4. 待用户确认的改动

> 审核子代理在「只检查」任务中越权改动了仓库，非本会话主动修改，已如实上报，待用户决定保留或回滚。

| # | 改动 | 说明 |
| --- | --- | --- |
| 1 | `pytest/verify_email.py` 删除 → 新建 `test/verify_email.py` | 内容逐字节相同（仅换行符差异），纯文件移动 |
| 2 | `config/__init__.py` 新增导出 | 追加 `ASYNC_DATABASE_URL` / `RESEND_API_KEY` / `CLOUNDDINARY_*` / `CLOUDINARY_CLOUD_NAME`；与现有 `from config.security import` 直接导入方式冗余 |

---

## 5. 既有已知问题（尚未处理）

> 源自既有框架文档，已修复的不再重复列，以下为仍存在项。

1. **CORS**：`allow_origins=["*"]` + `allow_credentials=True` 组合不符合浏览器规范且有安全风险，生产需白名单化。
2. **`resend` 未入 `requirements.txt`**：venv 已装 2.35.0，新环境按清单安装后邮件功能会 `ImportError`。
3. **无 Alembic 迁移 / 无 `create_all`**：`user` 表需手动创建，结构漂移靠人眼比对。
4. **无请求级日志/可观测性**：全程 `print`，无结构化日志、无 trace_id（`sentry-sdk` 已装未用）。
5. **`email/send` 的 `email` 是 query 参数**：既有框架文档误写为 body，实际为 `?email=xxx`（已以 router.md/OpenAPI 为准）。
