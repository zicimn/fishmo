# fishmo 路由文档（router.md）

> 适用仓库：`D:\vscode\fishmo`（分支 `main`）
> 文档版本：2026-08-06 · 基于当前工作区代码 + OpenAPI schema 核对撰写
> 说明：本文档如实反映仓库现状（含已实现功能与已知限制），未编造不存在的接口。

## 目录

- [1. 总览](#1-总览)
  - [1.1 基础信息](#11-基础信息)
  - [1.2 鉴权机制](#12-鉴权机制)
  - [1.3 通用约定](#13-通用约定)
- [2. 端点详解](#2-端点详解)
  - [2.1 POST /api/v1/user/login 登录](#21-post-apiv1userlogin-登录)
  - [2.2 POST /api/v1/user/register 注册](#22-post-apiv1userregister-注册)
  - [2.3 PUT /api/v1/user/update 更新资料](#23-put-apiv1userupdate-更新资料)
  - [2.4 DELETE /api/v1/user/delete 删除用户](#24-delete-apiv1userdelete-删除用户)
  - [2.5 POST /api/v1/email/send 发送邮箱验证码](#25-post-apiv1emailsend-发送邮箱验证码)
- [3. 数据模型](#3-数据模型)
- [4. 错误码一览](#4-错误码一览)
- [5. 已知限制与注意事项](#5-已知限制与注意事项)

---

## 1. 总览

### 1.1 基础信息

| 项 | 值 |
| --- | --- |
| Base URL | `/api/v1` |
| 接口文档 | FastAPI 自动生成：`http://localhost:8000/docs`（Swagger UI） |
| 路由注册 | `main.py` → `include_router(user_router)` / `include_router(email_router)`，无额外全局前缀 |
| 响应格式 | 裸 JSON dict（未使用 `response_model`） |
| CORS | 已开启 `allow_origins=["*"]` + `allow_credentials=True`（见[已知限制](#5-已知限制与注意事项)） |

当前共 **5 个端点**，归属两个路由：

| 路由 | 前缀 | 端点 |
| --- | --- | --- |
| `api/v1/user.py` | `/api/v1/user` | login / register / update / delete |
| `api/v1/email.py` | `/api/v1/email` | send |

### 1.2 鉴权机制

- **方案**：`HTTPBearer` + JWT（HS256）。
- 需要鉴权的端点：`PUT /update`、`DELETE /delete`。请求头携带：

```
Authorization: Bearer <access_token>
```

- 缺 token / token 无效统一返回 `401`（`HTTPBearer(auto_error=False)` + `verify_login` 判空处理，见 `utils/verify_user.py`）。
- 登录成功后返回的 `access_token` 就是后续请求的凭证。
- **注意（当前限制）**：Token **不携带 `exp` 过期时间**，签发后永久有效，直至 `SECRET_KEY` 轮换。测试阶段已知问题，见[第 5 节](#5-已知限制与注意事项)。

### 1.3 通用约定

- **Pydantic v2** 校验请求体；`EmailStr` 邮箱格式、`min_length/max_length` 字符串长度、`Optional` 可选字段均由 schema 层强制。
- **数据来源**：`db: AsyncSession = Depends(get_db)` 注入异步会话，事务边界即请求边界（正常自动 commit，异常自动回滚）。
- 业务错误统一抛 `HTTPException(status_code, detail)`，`detail` 为中文提示。
- 图片/密码哈希等同步阻塞操作在 `update` 中已用 `run_in_threadpool` 包裹（`login/register` 仍为同步调用，见[第 5 节](#5-已知限制与注意事项)）。

---

## 2. 端点详解

### 2.1 POST /api/v1/user/login 登录

- **鉴权**：无
- **请求体** `LoginRequest`：

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| username | str | ✅ | 登录用户名 |
| password | str | ✅ | 明文密码（argon2 校验） |

- **处理流程**：
  1. 按 `username` 查用户。
  2. 用户不存在或 `pwd_context.verify` 校验失败 → 统一 `401`（不区分「用户不存在」与「密码错误」，防止用户名枚举）。
  3. 签发 JWT：payload `{sub: str(user.id), username}`，HS256 签名。
- **成功 200**：
```json
{
  "id": 1,
  "username": "zhangsan",
  "access_token": "<jwt>"
}
```
- **错误**：`401 用户名或密码不正确`。

### 2.2 POST /api/v1/user/register 注册

- **鉴权**：无
- **请求体** `Account`：

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| username | str | ✅ | 2–20 字符 |
| password | str | ✅ | 6–20 字符（argon2 哈希后入库） |
| email | EmailStr | ✅ | 格式校验 |
| avatar | str? | ❌ | base64 图片，注册时**不会上传**，直接原样入库 |
| bio | str? | ❌ | 个人简介 |

- **查询参数**：`code`（必填，邮箱验证码，先经 `POST /api/v1/email/send` 获取）。

- **处理流程**：
  1. `or_(username == ..., email == ...)` 查重，已存在 → `400 用户名或邮箱已存在`。
  2. `verify_email_code(email, code)` 校验验证码（一次性，成功即删除）→ 失败 `400 验证码不正确或已过期`。
  3. `pwd_context.hash` 哈希密码 → 写入 `user` 表 → commit + refresh。
- **成功 200**：
```json
{
  "id": 1,
  "username": "zhangsan",
  "email": "z@example.com",
  "bio": null,
  "avatar": null
}
```
- **错误**：`400`（用户名或邮箱已存在 / 验证码不正确或已过期）。

### 2.3 PUT /api/v1/user/update 更新资料

- **鉴权**：Bearer token（必填）。
- **请求体** `AccountUpdate`（**全部可选**，传哪个字段改哪个，未传字段不修改）：

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| username | str? | ❌ | 若传：2–20 字符；与其它用户重名 → 400 |
| password | str? | ❌ | 若传：6–20 字符，重新哈希（不会误触发改密） |
| email | EmailStr? | ❌ | 若传：格式校验 + 排重（**无验证码校验**，见[第 5 节](#5-已知限制与注意事项)） |
| avatar | str? | ❌ | 若传：base64 图片 → 转 WebP 上传 Cloudinary，落库返回的 URL |
| bio | str? | ❌ | 若传：直接更新 |

- **处理流程**：
  1. `verify_login` 解析当前用户 ID → 加载用户（不存在 → `404 用户不存在`）。
  2. 改 `username` / `email` 前做**排除自身**唯一性查重（`User.id != user_id`）。
  3. `avatar` 非空：`run_in_threadpool(upload_image_to_cloudinary, ...)` 上传，成功写回 `user.avatar`（URL），失败 → `400 头像上传失败`。
  4. `password` 非空：`run_in_threadpool(pwd_context.hash, ...)` 重哈希。
  5. commit；唯一索引兜底 `IntegrityError` → `400`；成功调用 `update_version()` 使缓存版本号自增。
- **成功 200**：
```json
{
  "msg": "用户信息更新成功",
  "id": 1,
  "username": "zhangsan",
  "email": "z@example.com",
  "bio": "hello",
  "avatar": "https://res.cloudinary.com/.../xxx.webp"
}
```
- **错误**：`401`（未提供凭证 / token 无效）、`404 用户不存在`、`400`（用户名已存在 / 邮箱已存在 / 头像上传失败 / 用户名或邮箱已存在）。

### 2.4 DELETE /api/v1/user/delete 删除用户

- **鉴权**：Bearer token（必填）。
- **请求体**：无。
- **处理流程**：
  1. `verify_login` 解析当前用户 ID → 加载用户（不存在 → `404`）。
  2. `db.delete(user)` **物理删除**（非软删除，见[第 5 节](#5-已知限制与注意事项)）→ commit。
  3. 成功调用 `update_version()`。
- **成功 200**：
```json
{
  "msg": "用户已删除",
  "id": 1,
  "username": "zhangsan"
}
```
- **错误**：`401`、`404 用户不存在`。

### 2.5 POST /api/v1/email/send 发送邮箱验证码

- **鉴权**：无。
- **查询参数**（⚠️ 注意是 query 参数，不是请求体）：

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| email | EmailStr | ✅ | 接收验证码的邮箱 |

- **处理流程**（`utils/email.py`）：
  1. 生成 6 位数字验证码，写入 Redis（key `email_code:{email}`，TTL 300s）。
  2. `asyncio.to_thread` 调用 Resend SDK 发送邮件（同步 SDK 丢线程池，不阻塞事件循环）。
  3. 发送失败 → 删除缓存验证码 → `500 发送验证码失败: ...`。
- **成功 200**：
```json
{
  "message": "验证码已发送，请检查你的邮箱。"
}
```
- **错误**：`500`（发送失败）。
- **请求示例**：`POST /api/v1/email/send?email=z@example.com`

---

## 3. 数据模型

### 请求模型（schemas/user.py）

| 模型 | 字段 | 用途 |
| --- | --- | --- |
| `LoginRequest` | username, password | 登录 |
| `Account` | username, password, email, avatar?, bio? | 注册（全必填除 avatar/bio） |
| `AccountUpdate` | username?, password?, email?, avatar?, bio? | 更新资料（全可选） |

### 数据库表 `user`（model/user.py）

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| id | Integer | 主键自增 |
| username | String(50) | 唯一、非空、索引 |
| email | String(100) | 唯一、非空、索引 |
| password_hash | String(255) | argon2 哈希 |
| avatar | String(255) | 头像 URL |
| bio | Text | 简介 |
| status | SmallInteger | 默认 1（0-禁用 1-正常） |
| is_admin | SmallInteger | 默认 0 |
| created_at / updated_at | DateTime | 自动维护 |

---

## 4. 错误码一览

| 状态码 | 场景 | 说明 |
| --- | --- | --- |
| 401 | 用户名或密码不正确 / 未提供凭证 / token 无效 | 鉴权失败统一 401 |
| 400 | 用户名或邮箱已存在 / 验证码不正确或已过期 / 头像上传失败 | 业务校验失败 |
| 404 | 用户不存在 | 按 token 定位不到用户 |
| 500 | 邮箱发送失败 / 未捕获异常 | 依赖故障或兜底缺失 |

---

## 5. 已知限制与注意事项

1. **Token 无过期时间**：`jwt.encode` 未带 `exp`，`security.py` 中 `ACCESS_TOKEN_EXPIRE_MINUTES` 被注释。测试阶段已知问题，上线前需补有效期。
2. **改绑邮箱无验证码校验**：`update` 修改 `email` 仅排重、不验证邮箱归属；`register` 是校验验证码的。若未来有「忘记密码」流程，此处是攻击入口。
3. **头像注册原样入库**：`register` 的 `avatar` 直接存请求原值，不经过 WebP 转换 / Cloudinary 上传（只有 `update` 走转换上传）。
4. **`login/register` 的密码校验/哈希为同步调用**：未用 `run_in_threadpool` 包裹（argon2 为刻意慢哈希），高并发下可能阻塞事件循环。
5. **删除为物理删除**：`db.delete(user)` 硬删行，未利用 `status` 字段做软删除，可能破坏外键/历史引用。
6. **`email/send` 的 email 是 query 参数**：请求形如 `?email=xxx`，不是 JSON body（既有框架文档此处有误，以本文档/OpenAPI 为准）。
7. **CORS**：`allow_origins=["*"]` + `allow_credentials=True` 组合不符合浏览器规范且有安全风险，生产需改为域名白名单。
8. **无速率限制**：验证码发送、登录接口均无限流，存在被刷风险。
9. **`register`/`update` 唯一性查重存在 TOCTOU 窗口**：`update` 已用唯一索引 + `IntegrityError` 兜底，`register` 尚未加该兜底。
