# fishmo 路由文档（router.md）

> 适用仓库：`D:\vscode\fishmo`（分支 `main`）
> 文档版本：2026-08-12 · 基于当前工作区代码 + OpenAPI schema 核对撰写
> 说明：本文档如实反映仓库现状（含已实现功能与已知限制），未编造不存在的接口。

## 目录

- [1. 总览](#1-总览)
  - [1.1 基础信息](#11-基础信息)
  - [1.2 鉴权机制](#12-鉴权机制)
  - [1.3 通用约定](#13-通用约定)
- [2. 端点详解](#2-端点详解)
  - [user 模块](#user-模块)
    - [2.1 POST /api/v1/user/login 登录](#21-post-apiv1userlogin-登录)
    - [2.2 POST /api/v1/user/register 注册](#22-post-apiv1userregister-注册)
    - [2.3 PUT /api/v1/user/update 更新资料](#23-put-apiv1userupdate-更新资料)
    - [2.4 DELETE /api/v1/user/delete 删除用户](#24-delete-apiv1userdelete-删除用户)
    - [2.5 GET /api/v1/user/ 查看用户信息](#25-get-apiv1user-查看用户信息)
  - [email 模块](#email-模块)
    - [2.6 POST /api/v1/email/send 发送邮箱验证码](#26-post-apiv1emailsend-发送邮箱验证码)
  - [galgame 模块](#galgame-模块)
    - [2.7 GET /api/v1/galgame/ 游戏列表](#27-get-apiv1galgame-游戏列表)
    - [2.8 GET /api/v1/galgame/{id} 游戏详情](#28-get-apiv1galgameid-游戏详情)
    - [2.9 POST /api/v1/galgame/add 发布游戏](#29-post-apiv1galgameadd-发布游戏)
    - [2.10 DELETE /api/v1/galgame/delete 删除游戏](#210-delete-apiv1galgamedelete-删除游戏)
    - [2.11 PUT /api/v1/galgame/edit 编辑游戏](#211-put-apiv1galgameedit-编辑游戏)
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
| 路由注册 | `main.py` → `include_router(user_router)` / `include_router(email_router)` / `include_router(gal_router)`，无额外全局前缀 |
| 响应格式 | 裸 JSON dict（galgame 列表接口使用 `response_model=GalList`，其余未声明） |
| CORS | 已开启 `allow_origins=["*"]` + `allow_credentials=True`（见[已知限制](#5-已知限制与注意事项)） |

当前共 **11 个端点**，归属三个路由：

| 路由 | 前缀 | 端点 |
| --- | --- | --- |
| `api/v1/user.py` | `/api/v1/user` | login / register / update / delete / index |
| `api/v1/email.py` | `/api/v1/email` | send |
| `api/v1/galgame.py` | `/api/v1/galgame` | index / visit / add / delete / edit |

### 1.2 鉴权机制

- **方案**：`HTTPBearer` + JWT（HS256）。
- 需要鉴权的端点：
  - user：`PUT /update`、`DELETE /delete`
  - galgame：`POST /add`、`DELETE /delete`、`PUT /edit`
  - `GET /api/v1/user/`：可选（不传 `id` 时用 token 定位自身）
- 请求头携带：

```
Authorization: Bearer <access_token>
```

- 缺 token / token 无效统一返回 `401`（`HTTPBearer(auto_error=False)` + `verify_login` 判空处理，见 `utils/verify_user.py`）。
- **注意（当前限制）**：Token **不携带 `exp` 过期时间**，签发后永久有效，直至 `SECRET_KEY` 轮换。测试阶段已知问题，见[第 5 节](#5-已知限制与注意事项)。

### 1.3 通用约定

- **Pydantic v2** 校验请求体；`EmailStr` 邮箱格式、`min_length/max_length` 字符串长度、`Optional` 可选字段均由 schema 层强制。
- **数据来源**：`db: AsyncSession = Depends(get_db)` 注入异步会话，事务边界即请求边界（正常自动 commit，异常自动回滚）。
- 业务错误统一抛 `HTTPException(status_code, detail)`，`detail` 为中文提示。
- 图片/密码哈希等同步阻塞操作在 `update`、galgame 上传路径已用 `run_in_threadpool` 包裹（`login/register` 仍为同步调用，见[第 5 节](#5-已知限制与注意事项)）。
- **缓存**：Redis 驱动（`config/cache.py`），列表/详情缓存 key 带 `search_version` 版本号，数据变更后 `update_version()` 使旧 key 失效。

---

## 2. 端点详解

## user 模块

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
  "msg": "用户登录信息",
  "id": 1,
  "username": "zhangsan",
  "access_token": "<jwt>"
}
```
- **错误**：`401 用户名或密码不正确`。

### 2.2 POST /api/v1/user/register 注册

- **鉴权**：无
- **查询参数**：`code`（必填，邮箱验证码，先经 `POST /api/v1/email/send` 获取）。
- **请求体** `Account`：

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| username | str | ✅ | 2–20 字符 |
| password | str | ✅ | 6–20 字符（argon2 哈希后入库） |
| email | EmailStr | ✅ | 格式校验 |
| avatar | str? | ❌ | base64 图片，注册时**不会上传**，直接原样入库 |
| bio | str? | ❌ | 个人简介 |

- **处理流程**：
  1. `or_(username == ..., email == ...)` 查重，已存在 → `409 用户名或邮箱已存在`。
  2. `verify_email_code(email, code)` 校验验证码（一次性，成功即删除）→ 失败 `400 验证码不正确或已过期`。
  3. `pwd_context.hash` 哈希密码 → 写入 `user` 表 → commit + refresh。
- **成功 200**：
```json
{
  "msg": "用户注册信息",
  "id": 1,
  "username": "zhangsan",
  "email": "z@example.com",
  "bio": null,
  "avatar": null
}
```
- **错误**：`409`（用户名或邮箱已存在）、`400`（验证码不正确或已过期）。

### 2.3 PUT /api/v1/user/update 更新资料

- **鉴权**：Bearer token（必填）。
- **请求体** `AccountUpdate`（**全部可选**，传哪个字段改哪个，未传字段不修改）：

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| username | str? | ❌ | 若传：2–20 字符；与其它用户重名 → 409 |
| password | str? | ❌ | 若传：6–20 字符，重新哈希（不会误触发改密） |
| email | EmailStr? | ❌ | 若传：格式校验 + 排重（**无验证码校验**，见[第 5 节](#5-已知限制与注意事项)） |
| avatar | str? | ❌ | 若传：base64 图片 → 转 WebP 上传 Cloudinary，落库返回的 URL |
| bio | str? | ❌ | 若传：直接更新 |

- **处理流程**：
  1. `verify_login` 解析当前用户 ID → 加载用户（不存在 → `404 用户不存在`）。
  2. 改 `username` / `email` 前做**排除自身**唯一性查重（`User.id != user_id`）。
  3. `avatar` 非空：`run_in_threadpool(upload_image_to_cloudinary, ...)` 上传，成功写回 `user.avatar`（URL），失败 → `422 头像上传失败`。
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
- **错误**：`401`（未提供凭证 / token 无效）、`404 用户不存在`、`409`（用户名已存在 / 邮箱已存在）、`422`（头像上传失败）、`400`（唯一索引兜底）。

### 2.4 DELETE /api/v1/user/delete 删除用户

- **鉴权**：Bearer token（必填）。
- **请求体**：无。
- **处理流程**：
  1. `verify_login` 解析当前用户 ID → 加载用户（不存在 → `404`）。
  2. `db.delete(user)` **物理删除**（非软删除，见[第 5 节](#5-已知限制与注意事项)）→ commit。
  3. commit 捕获 `IntegrityError`（用户下存在关联 galgame 作品，外键 `ondelete=RESTRICT`）→ `400 该用户存在关联作品，无法删除`。
  4. 成功调用 `update_version()`。
- **成功 200**：
```json
{
  "msg": "用户已删除",
  "id": 1,
  "username": "zhangsan"
}
```
- **错误**：`401`、`404 用户不存在`、`400`（存在关联作品，无法删除）。

### 2.5 GET /api/v1/user/ 查看用户信息

- **鉴权**：可选（Bearer token）。
- **查询参数**：

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| id | int? | ❌ | 指定查看的用户 id；不传则用 token 定位自身 |

- **处理流程**：
  1. 既无 `id` 也无 token → `400 参数错误`。
  2. 传了 `id` 直接用；未传 `id` 则 `verify_login` 解析 token 得自身 id。
  3. 按 id 加载用户（不存在 → `404 用户不存在`）。
- **成功 200**：
```json
{
  "msg": "用户信息",
  "username": "zhangsan",
  "avatar": null,
  "bio": "hello",
  "email": "z@example.com"
}
```
- **错误**：`400 参数错误`、`401`、`404 用户不存在`。

---

## email 模块

### 2.6 POST /api/v1/email/send 发送邮箱验证码

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

## galgame 模块

### 2.7 GET /api/v1/galgame/ 游戏列表

- **鉴权**：无。
- **查询参数**：

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| category | str? | ❌ | 按作品类型过滤（精确匹配 `category` 列） |
| platform | PlatformEnum? | ❌ | 按支持平台过滤（`PC`=电脑端 / `AZ`=安卓端 / `OTHER`=Other） |
| page | int | ❌ | 页码，默认 1，`ge=1` |
| size | int | ❌ | 每页条数，默认 10，`ge=1, le=50` |

- **处理流程**：
  1. 取 `search_version` 版本号，拼缓存 key（`Galgame:v{version}:page=..:size=..:...`）；命中缓存直接返回。
  2. 过滤条件集中管理（`status == True` 可见状态 + category + platform），列表查询与总数统计共用同一组 WHERE。
  3. `join(Galgame.author)` 联表取作者用户名/头像，按 `updated_at` 倒序（无次级排序，见[第 5 节](#5-已知限制与注意事项)）分页。
  4. 名称展示取 `cn_name or jp_name or en_name or "undefind"`；结果写入缓存（TTL 5 分钟）。
- **成功 200**（`response_model=GalList`）：
```json
{
  "total": 2,
  "items": [
    {
      "name": "Everlasting Summer",
      "cover": "https://res.cloudinary.com/.../cover.webp",
      "views": 120,
      "author": "zhangsan",
      "avatar": null
    }
  ]
}
```
- **错误**：`422`（page/size 越界）。
- **⚠️ 已知缺陷**：当前代码中 `select` 引用 `User.name`（不存在，模型字段为 `username`），**该接口运行时抛 `AttributeError` → 500**。见[第 5 节 #1](#5-已知限制与注意事项)，待修复。

### 2.8 GET /api/v1/galgame/{id} 游戏详情

- **鉴权**：无。
- **路径参数**：`id`（int，游戏 id）。
- **处理流程**：
  1. 取版本号拼缓存 key（`Gal_visit:v{version}:id={id}`）。
  2. **浏览量计数与响应缓存解耦**：无论缓存是否命中都执行 Redis `INCR gal_views:{id}`（key 首次写入设 24h TTL）。
  3. 计数累计满阈值（`delta % 10 == 0`）时用 SQL 原子自增 `views = views + delta` 落库并重置计数 key，避免并发读-改-写丢更新。
  4. 缓存命中直接返回；未命中则 `join(author)` 查询详情，不存在 → `404 未找到`，`status == False` → `403 当前未被公开`。
  5. 展示浏览量 = DB 值 + 未落库的 Redis 计数；结果写入缓存（TTL 30 分钟）。
- **成功 200**：
```json
{
  "msg": "查询成功",
  "id": 1,
  "name": "Everlasting Summer",
  "content": "游戏简介",
  "company": ["Studio X"],
  "category": "Galgame",
  "cover": "https://res.cloudinary.com/.../cover.webp",
  "images": ["https://.../1.webp", "https://.../2.webp"],
  "tag": ["治愈"],
  "views": 120,
  "likes": 5,
  "favorite": 3,
  "platfrom": ["电脑端"],
  "update_at": "2026-08-12T10:00:00",
  "author_name": "zhangsan",
  "author_avatar": null
}
```
- **错误**：`404 未找到`、`403 当前未被公开`。
- **说明**：响应字段 `update_at`、`platfrom` 为代码中的拼写（模型为 `updated_at` / `platform`），保留现状。

### 2.9 POST /api/v1/galgame/add 发布游戏

- **鉴权**：Bearer token（必填，发布者为作者）。
- **请求体** `AddGal`：

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| cn_name / jp_name / en_name | str? | 至少一个 | 三者至少填一个非空，缺省项归一化为空串 |
| content | str? | ❌ | 游戏简介 |
| company | List[str]? | ❌ | 制作公司 |
| category | str? | ❌ | 作品类型 |
| cover | str | ✅ | base64 封面图（转 WebP 上传 Cloudinary） |
| images | List[str]? | ❌ | base64 截图列表（批量转 WebP 上传） |
| tag | List[str]? | ❌ | 标签 |
| platfrom | List[PlatformEnum]? | ❌ | 支持平台 |

- **处理流程**：
  1. `verify_login` 解析当前用户 ID。
  2. 对实际填写的名称做唯一性查重（只比较非空名称）→ 命中 `409 该游戏已存在`。
  3. `cover` 非空：`run_in_threadpool` 上传 → 失败 `500 图片上传失败...`。
  4. `images` 非空：`run_in_threadpool` 批量上传 → 失败 `500 图片上传错误`。
  5. 创建 `Galgame`，`status=True`（作者即发布者，新增即公开）、`author_id=user_id`。
  6. commit；清理列表缓存 + `update_version()`。
- **成功 200**：
```json
{
  "msg": "添加成功",
  "id": 5
}
```
- **错误**：`401`、`409`（该游戏已存在）、`422`（三名称全空）、`500`（图片上传失败）。

### 2.10 DELETE /api/v1/galgame/delete 删除游戏

- **鉴权**：Bearer token（必填，仅作者可删）。
- **查询参数**：`id`（int，游戏 id）。
- **处理流程**：
  1. `verify_login` 解析当前用户 ID。
  2. 按 `id + author_id` 查完整 ORM 对象，不存在或非发布者 → `403 没有该游戏或者您不是发布者`。
  3. `db.delete(result)` + commit。
  4. 清理缓存（列表 key、`Gal_visit:*id={id}`、浏览量计数 key）+ `update_version()`。
- **成功 200**：
```json
{
  "msg": "删除成功",
  "id": 5,
  "user_id": 1
}
```
- **错误**：`401`、`403`。

### 2.11 PUT /api/v1/galgame/edit 编辑游戏

- **鉴权**：Bearer token（必填，仅作者可编辑）。
- **查询参数**：`id`（int，游戏 id）。
- **请求体** `EditGal`（字段同 `AddGal`，均可选，传哪个改哪个；`cover`/`images` 传入时重新上传）：

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| cn_name / jp_name / en_name | str? | ❌ | 更新对应名称 |
| content / company / category / tag / platfrom | 同上 | ❌ | 对应字段更新 |
| cover | str? | ❌ | 若传：base64 封面 → 转 WebP 重新上传，替换封面 URL |
| images | List[str]? | ❌ | 若传：批量上传，整体替换截图列表 |

- **处理流程**：
  1. `verify_login`；按 `id + author_id` 查对象，无权限 → `403`。
  2. 依次按传入字段赋值；`cover`/`images` 走 `run_in_threadpool` 上传，失败 → `500`。
  3. commit；清理缓存（列表 key + `Gal_visit:*id={id}`）+ `update_version()`。
- **成功 200**：
```json
{
  "msg": "编辑成功",
  "id": 5,
  "user_id": 1
}
```
- **错误**：`401`、`403`、`500`（图片上传失败）。

---

## 3. 数据模型

### 请求/响应模型

**schemas/user.py**

| 模型 | 字段 | 用途 |
| --- | --- | --- |
| `LoginRequest` | username, password | 登录 |
| `Account` | username, password, email, avatar?, bio? | 注册（除 avatar/bio 外全必填） |
| `AccountUpdate` | username?, password?, email?, avatar?, bio? | 更新资料（全可选） |

**schemas/galgame.py**

| 模型 | 字段 | 用途 |
| --- | --- | --- |
| `GalItem` | name, cover, views, author, avatar? | 列表项 |
| `GalList` | total, items: List[GalItem] | 列表响应（`response_model`） |
| `AddGal` | 三名称(至少一)、content?, company?, category?, cover(必填), images?, tag?, platfrom? | 发布（含名称校验器） |
| `EditGal` | 同 AddGal 但全可选 | 编辑 |

**model/enums.py**

| 枚举 | 值 | 说明 |
| --- | --- | --- |
| `PlatformEnum` | `PC`="电脑端"、`AZ`="安卓端"、`OTHER`="Other" | 支持平台，model 与 schemas 共同引用 |

### 数据库表 `user`（model/user.py）

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| id | Integer | 主键自增 |
| username | String(50) | 唯一、非空、索引 |
| email | String(100) | 唯一、非空、索引 |
| password_hash | String(255) | argon2 哈希 |
| avatar | String(255)? | 头像 URL |
| bio | Text? | 简介 |
| status | SmallInteger | 默认 1（0-禁用 1-正常） |
| is_admin | SmallInteger | 默认 0 |
| created_at / updated_at | DateTime | 自动维护 |

> 关联：`galgames` 集合侧关系 `lazy="raise"`（禁止隐式加载，需显式 `selectinload`），避免任何 User 查询全量拉取 galgames。

### 数据库表 `galgame`（model/galgame.py）

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| id | Integer | 主键自增 |
| cn_name / en_name / jp_name | String(50) | 非空，Python 侧默认空串 |
| content | Text? | 游戏简介 |
| company | JSON? | 制作公司列表 |
| category | String(50) | 默认 `other` |
| cover | String(255) | 封面 URL |
| images | JSON? | 截图 URL 列表 |
| tag | JSON? | 标签列表 |
| views / likes / favorite | Integer | 默认 0 |
| platfrom | JSON? | 支持平台（枚举值列表，字段拼写保留现状） |
| status | Boolean | 默认 False；`add` 时置 True（作者即发布） |
| author_id | Integer | 外键 `user.id`，`ondelete=RESTRICT` |
| created_at / updated_at | DateTime | 自动维护 |

---

## 4. 错误码一览

| 状态码 | 场景 | 说明 |
| --- | --- | --- |
| 401 | 用户名或密码不正确 / 未提供凭证 / token 无效 | 鉴权失败统一 401 |
| 400 | 验证码不正确或已过期 / 参数错误 / 用户存在关联作品无法删除 / update 唯一索引兜底 | 业务校验失败 |
| 403 | galgame 非发布者 / 详情未公开 | 无权限 / 资源不可见 |
| 404 | 用户不存在 / 游戏未找到 | 按 id/token 定位不到 |
| 409 | 用户名或邮箱已存在（register/update）/ 该游戏已存在（add） | 唯一性冲突 |
| 422 | 头像上传失败 / Pydantic 校验失败（page、size 越界、三名称全空） | 请求不合法 |
| 500 | 发送验证码失败 / 图片上传失败 / 未捕获异常（含 galgame 列表 `User.name` 缺陷） | 依赖故障或兜底缺失 |

---

## 5. 已知限制与注意事项

1. **【Critical 待修复】galgame 列表接口 `User.name` 引用错误**：`api/v1/galgame.py` 的 `index` 查询使用 `User.name`（不存在），模型字段为 `username`，运行时抛 `AttributeError` → `GET /api/v1/galgame/` 返回 500。修复：改 `User.username`。
2. **Token 无过期时间**：`jwt.encode` 未带 `exp`，`security.py` 中 `ACCESS_TOKEN_EXPIRE_MINUTES` 被注释。测试阶段已知问题，上线前需补有效期。
3. **改绑邮箱无验证码校验**：`update` 修改 `email` 仅排重、不验证邮箱归属；`register` 是校验验证码的。若未来有「忘记密码」流程，此处是攻击入口。
4. **头像注册原样入库**：`register` 的 `avatar` 直接存请求原值，不经过 WebP 转换 / Cloudinary 上传（只有 `update` 与 galgame 上传走转换上传）。
5. **`login/register` 的密码校验/哈希为同步调用**：未用 `run_in_threadpool` 包裹（argon2 为刻意慢哈希），高并发下可能阻塞事件循环。
6. **删除为物理删除**：`db.delete` 硬删行，未利用 `status` 字段做软删除；用户删除在有 galgame 作品时会因外键 `RESTRICT` 返回 400（已兜底，但历史引用仍可能受影响）。
7. **`email/send` 的 email 是 query 参数**：请求形如 `?email=xxx`，不是 JSON body（既有框架文档此处有误，以本文档/OpenAPI 为准）。
8. **CORS**：`allow_origins=["*"]` + `allow_credentials=True` 组合不符合浏览器规范且有安全风险，生产需改为域名白名单。
9. **无速率限制**：验证码发送、登录接口均无限流，存在被刷风险。
10. **`register`/`update` 唯一性查重存在 TOCTOU 窗口**：`update` 已用唯一索引 + `IntegrityError` 兜底，`register` 尚未加该兜底。
11. **galgame 列表排序不稳定**：`order_by(updated_at)` 无次级排序，同值记录分页可能重复/遗漏。
12. **字段拼写问题**：`platfrom`（应为 platform）、`update_at`（应为 updated_at）为既有拼写，改库需迁移。
13. **`resend` 未入 `requirements.txt`**：venv 已装，新环境按清单安装后邮件功能会 `ImportError`。
14. **无 Alembic 迁移 / 无 `create_all`**：`user`/`galgame` 表需手动创建，结构漂移靠人眼比对。
15. **无测试、无 lint、无请求级日志**：全程 `print`/`logging`，无结构化日志与 trace_id。
