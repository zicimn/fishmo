# fishmo 路由文档（router.md）

> 适用仓库：`D:\vscode\fishmo`（分支 `main`）
> 文档版本：2026-09-17 · 基于当前工作区代码 + OpenAPI schema 核对撰写
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
  - [link 模块](#link-模块)
    - [2.12 GET /api/v1/link/{game_id} 链接列表](#212-get-apiv1linkgame_id-链接列表)
    - [2.13 POST /api/v1/link/add 添加链接](#213-post-apiv1linkadd-添加链接)
    - [2.14 PUT /api/v1/link/review 编辑链接](#214-put-apiv1linkreview-编辑链接)
    - [2.15 DELETE /api/v1/link/delete 删除链接](#215-delete-apiv1linkdelete-删除链接)
    - [2.20 GET /api/v1/link/user/{user_id} 按用户获取链接列表](#220-get-apiv1linkuseruser_id-按用户获取链接列表)
  - [comment 模块](#comment-模块)
    - [2.16 GET /api/v1/comment/{game_id} 评论列表](#216-get-apiv1commentgame_id-评论列表)
    - [2.17 POST /api/v1/comment/add 发表评论](#217-post-apiv1commentadd-发表评论)
    - [2.18 PUT /api/v1/comment/edit 编辑评论](#218-put-apiv1commentedit-编辑评论)
    - [2.19 DELETE /api/v1/comment/delete 删除评论](#219-delete-apiv1commentdelete-删除评论)
    - [2.21 GET /api/v1/comment/user/{user_id} 按用户获取评论列表](#221-get-apiv1commentuseruser_id-按用户获取评论列表)
  - [favorite 模块](#favorite-模块)
    - [2.22 POST /api/v1/favorite/add 收藏游戏](#222-post-apiv1favoriteadd-收藏游戏)
    - [2.23 DELETE /api/v1/favorite/remove 取消收藏](#223-delete-apiv1favoriteremove-取消收藏)
    - [2.24 GET /api/v1/favorite/visit 访问收藏](#224-get-apiv1favoritevisit-访问收藏)
    - [2.25 GET /api/v1/favorite/list 收藏列表](#225-get-apiv1favoritelist-收藏列表)
  - [search 模块](#search-模块)
    - [2.26 GET /api/v1/search/ 搜索游戏](#226-get-apiv1search-搜索游戏)
  - [admin 模块](#admin-模块)
    - [2.27 GET /api/admin/control/BrowseGal 浏览待审核游戏](#227-get-apiadmincontrolbrowsegal-浏览待审核游戏)
    - [2.28 PUT /api/admin/control/UpdateStatus 更新审核状态](#228-put-apiadmincontrolupdatestatus-更新审核状态)
    - [2.29 DELETE /api/admin/control/DeleteGal 管理员删除游戏](#229-delete-apiadmincontroldeletegal-管理员删除游戏)
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
| 路由注册 | `main.py` → `include_router(user_router)` / `include_router(email_router)` / `include_router(gal_router)` / `include_router(link_router)` / `include_router(comment_router)` / `include_router(favorite_router)` / `include_router(search_router)` / `include_router(control_router)`，无额外全局前缀 |
| 响应格式 | 裸 JSON dict；列表接口使用 `response_model`：galgame=`GalList` / link=`LinkList` / comment=`CommentList` / favorite=`GalBaseList` / search=`GalList`，其余未声明 |
| CORS | 已开启 `allow_origins=["*"]` + `allow_credentials=True`（见[已知限制](#5-已知限制与注意事项)） |

当前共 **28 个端点**，归属八个路由：

| 路由 | 前缀 | 端点 |
| --- | --- | --- |
| `api/v1/user.py` | `/api/v1/user` | login / register / update / delete / index |
| `api/v1/email.py` | `/api/v1/email` | send |
| `api/v1/galgame.py` | `/api/v1/galgame` | index / visit / add / delete / edit |
| `api/v1/link.py` | `/api/v1/link` | get_list / get_list_by_user / add / review / delete |
| `api/v1/comment.py` | `/api/v1/comment` | get_list / get_list_by_user / add / edit / delete |
| `api/v1/favorite.py` | `/api/v1/favorite` | add / remove / visit / list |
| `api/v1/search.py` | `/api/v1/search` | search |
| `api/admin/control.py` | `/api/admin/control` | BrowseGal / UpdateStatus / DeleteGal |

### 1.2 鉴权机制

- **方案**：`HTTPBearer` + JWT（HS256）。
- 需要鉴权的端点：
  - user：`PUT /update`、`DELETE /delete`
  - galgame：`POST /add`、`DELETE /delete`、`PUT /edit`
  - link：`POST /add`、`PUT /review`、`DELETE /delete`
  - comment：`POST /add`、`PUT /edit`、`DELETE /delete`
  - favorite：`POST /add`、`DELETE /remove`、`GET /list`
  - admin control：`GET /BrowseGal`、`PUT /UpdateStatus`、`DELETE /DeleteGal`（需管理员身份，`verify_admin` 校验 JWT `is_admin` 字段）
  - `GET /api/v1/user/`：可选（不传 `id` 时用 token 定位自身）
  - `GET /api/v1/galgame/{id}`：可选（管理员可绕过 `status=False` 限制查看未审核游戏）
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
- **缓存**：Redis 驱动（`config/cache.py`）。版本计数按业务域拆分：`gal_version` / `link_version` / `comment_version`（全局 `search_version` 保留向后兼容）；列表/详情缓存 key 内嵌对应域的版本号，该域数据变更后 `update_version(域KEY)` 使旧 key 失效。

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
| category | CategoryEnum? | ❌ | 按作品类型过滤（精确匹配，枚举：剧情向 / 治愈系 / 日常系 / 恋爱模拟 / 文字冒险 / RPG / 经营模拟 / 拔作 / 全年龄 / 其他） |
| platform | PlatformEnum? | ❌ | 按支持平台过滤（`PC`=电脑端 / `AZ`=安卓端 / `OTHER`=Other） |
| author_id | int? | ❌ | 按作者 id 过滤（我的游戏 / 个人主页列表） |
| keyword | str? | ❌ | 按游戏名称关键词模糊搜索（`ilike` 匹配三语言列 cn/en/jp） |
| page | int | ❌ | 页码，默认 1，`ge=1` |
| size | int | ❌ | 每页条数，默认 10，`ge=1, le=50` |

- **处理流程**：
  1. 取 `gal_version` 版本号，拼缓存 key（`Galgame:v{version}:page=..:size=..:...`，`author_id`/`keyword` 亦参与 key 拼接）；命中缓存直接返回。
  2. 过滤条件集中管理（`status == True` 可见状态 + category + platform + author_id + keyword），列表查询与总数统计共用同一组 WHERE。**注意**：当指定 `author_id` 时不做 `status` 过滤（作者可见自己未审核的作品），其他人只能看到公开的。
  3. `join(Galgame.author)` 联表取作者用户名/头像，按 `updated_at` 倒序（最新发布在前）分页。
  4. 名称展示取统一 `name` 字段；结果写入缓存（TTL 5 分钟）。
- **已知问题**：`keyword` 的 `ilike` 未转义 SQL LIKE 通配符（`%`/`_`），用户输入这些字符时可能导致非预期匹配。`search.py` 已做转义但此处遗漏。
- **成功 200**（`response_model=GalList`）：
```json
{
  "total": 2,
  "items": [
    {
      "id": 1,
      "name": "Everlasting Summer",
      "cover": "https://res.cloudinary.com/.../cover.webp",
      "views": 120,
      "author": "zhangsan",
      "avatar": null,
      "author_id": 1
    }
  ]
}
```
- **错误**：`422`（page/size 越界）。

### 2.8 GET /api/v1/galgame/{id} 游戏详情

- **鉴权**：可选（Bearer token，管理员可绕过 `status=False` 限制）。
- **路径参数**：`id`（int，游戏 id）。
- **处理流程**：
  1. 取版本号拼缓存 key（`Gal_visit:v{version}:id={id}`）。
  2. **浏览量计数与响应缓存解耦**：无论缓存是否命中都执行 `ViewCounter.incr(id)`（Redis 累积计数，由定时任务批量落库）。
  3. 缓存命中直接返回；未命中则 `join(author)` 查询详情，不存在 → `404 未找到`。
  4. **管理员绕过**：调用 `verify_admin(credentials)` 校验身份，若 `status == False` 且非管理员 → `403 当前未被公开`；管理员可查看未审核游戏。
  5. 展示浏览量 = DB 值 + 未落库的 Redis 计数；结果写入缓存（TTL 30 分钟）。
- **成功 200**：
```json
{
  "msg": "查询成功",
  "id": 1,
  "name": "Everlasting Summer",
  "content": "游戏简介",
  "company": ["Studio X"],
  "category": "剧情向",
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
| name | str? | ❌ | 统一名称（可选，后端自动从 cn_name/jp_name/en_name 派生） |
| cn_name / jp_name / en_name | str? | 至少一个 | 三者至少填一个非空，缺省项归一化为空串 |
| content | str? | ❌ | 游戏简介 |
| company | List[str]? | ❌ | 制作公司 |
| category | CategoryEnum? | ❌ | 作品类型（枚举同列表参数；缺省落库兜底"其他"） |
| cover | str | ✅ | base64 封面图（转 WebP 上传 Cloudinary） |
| images | List[str]? | ❌ | base64 截图列表（批量转 WebP 上传） |
| tag | List[str]? | ❌ | 标签 |
| platfrom | List[PlatformEnum]? | ❌ | 支持平台 |

- **处理流程**：
  1. `verify_login` 解析当前用户 ID。
  2. `name` 字段由 schema `_normalize_names` 校验器自动派生（优先 cn_name → jp_name → en_name），最终 `name` 为必填唯一字段。
  3. 按 `name` 做唯一性查重 → 命中 `409 该游戏已存在`。
  4. `cover` 非空：`run_in_threadpool` 上传 → 失败 `422 封面图上传失败...`。
  5. `images` 非空：`run_in_threadpool` 批量上传 → 失败 `422 图片上传失败...`。
  6. 创建 `Galgame`，**`status=False`**（新增游戏默认待审核，管理员审核通过后公开）、`author_id=user_id`。
  7. commit；清理列表缓存 + `update_version(GAL_VERSION_KEY)`。
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
  3. `db.delete(result)` + commit；捕获 `IntegrityError`（游戏下存在关联链接 `link.game_id` 外键 `ondelete=RESTRICT`）→ `400 该游戏存在关联链接，无法删除`。
  4. 清理缓存（列表 key、`Gal_visit:*id={id}`、浏览量计数 key、`links:*game_id={id}`）+ `update_version(GAL_VERSION_KEY)`。
- **成功 200**：
```json
{
  "msg": "删除成功",
  "id": 5,
  "user_id": 1
}
```
- **错误**：`401`、`403`、`400`（该游戏存在关联链接，无法删除）。

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
  3. commit；清理缓存（列表 key + `Gal_visit:*id={id}`）+ `update_version(GAL_VERSION_KEY)`。
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

## link 模块

### 2.12 GET /api/v1/link/{game_id} 链接列表

- **鉴权**：无。
- **路径参数**：`game_id`（int，游戏 id）。
- **查询参数**：

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| page | int | ❌ | 页码，默认 1，`ge=1` |
| size | int | ❌ | 每页条数，默认 10，`ge=1, le=50` |

- **处理流程**：
  1. 取 `link_version` 版本号拼缓存 key（`links:v{n}:game_id=X:page=Y:size=Z`），命中缓存直接返回。
  2. 先校验游戏存在（不存在 → `404 未找到该游戏`），避免对不存在的游戏返回空列表。
  3. 过滤条件集中管理：`Link.game_id == game_id` 且 `Link.status == True`（仅展示公开链接），列表查询与总数统计共用同一组 WHERE（不带 offset/limit）。
  4. `join(Link.author)` 联表取作者用户名/头像，按 `updated_at` 倒序分页。
  5. 结果写入缓存（TTL 5 分钟）。
- **成功 200**（`response_model=LinkList`）：
```json
{
  "total": 1,
  "items": [
    {
      "item": {
        "id": 3,
        "url": "https://pan.example.com/s/abc",
        "content": "百度网盘",
        "code": "1234",
        "category": "网盘",
        "size": 2.5,
        "size_unit": "GB",
        "status": true,
        "game_id": 5
      },
      "account": {
        "username": "zhangsan",
        "avatar": null
      }
    }
  ]
}
```
- **错误**：`404 未找到该游戏`、`422`（page/size 越界）。
- **说明**：响应项新增 `id`、`game_id` 字段——`game_id` 供按用户过滤列表跳转对应游戏/管理页使用。

### 2.13 POST /api/v1/link/add 添加链接

- **鉴权**：Bearer token（必填，发布者为作者）。
- **查询参数**：`game_id`（int，目标游戏 id）。
- **请求体** `AddLink`：

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| url | str | ✅ | 链接，1–255 字符 |
| content | str? | ❌ | 链接内容（如网盘名），≤255 字符 |
| code | str? | ❌ | 提取码，≤255 字符 |
| category | str? | ❌ | 链接类型，≤255 字符 |
| size | float? | ❌ | 大小数值（≥0，配合 size_unit 使用） |
| size_unit | str? | ❌ | 大小单位：`KB` / `MB` / `GB`（正则校验） |

- **处理流程**：
  1. `verify_login` 解析当前用户 ID；校验游戏存在（不存在 → `404 未找到该游戏`）。
  2. 创建 `Link`，`status=True`（新增即公开，后续可由 control 路由管理）、`author_id=user_id`、`game_id=game_id`。
  3. commit + refresh；`delete_cache_pattern("links:*")` + `update_version(LINK_VERSION_KEY)`。
- **成功 200**：
```json
{
  "msg": "添加成功",
  "id": 3
}
```
- **错误**：`401`、`404 未找到该游戏`、`422`（url 为空 / 越界）。

### 2.14 PUT /api/v1/link/review 编辑链接

- **鉴权**：Bearer token（必填，仅作者可编辑）。
- **查询参数**：`link_id`（int，链接 id）。
- **请求体** `EditLink`（全可选，传哪个字段改哪个；用 `is not None` 判断，允许显式清空字段）：

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| content / code / category | str? | ❌ | 对应字段更新，≤255 字符 |
| size | float? | ❌ | 大小数值（≥0） |
| size_unit | str? | ❌ | 大小单位：`KB` / `MB` / `GB` |

- **处理流程**：
  1. `verify_login`；按 `Link.id == link_id` 且 `Link.author_id == user_id` 查对象，非作者 → `403 没有该链接或者您不是发布者`。
  2. 仅当字段非 `None` 时更新。
  3. commit；`delete_cache_pattern("links:*")` + `update_version(LINK_VERSION_KEY)`。
- **成功 200**：
```json
{
  "msg": "编辑成功",
  "id": 3,
  "user_id": 1
}
```
- **错误**：`401`、`403`。

### 2.15 DELETE /api/v1/link/delete 删除链接

- **鉴权**：Bearer token（必填，仅作者可删）。
- **查询参数**：`link_id`（int，链接 id）。
- **处理流程**：
  1. `verify_login`；按 `id + author_id` 查对象，非作者 → `403 没有该链接或者您不是发布者`。
  2. `db.delete` + commit；捕获 `IntegrityError` → `400 无法删除`。
  3. `delete_cache_pattern("links:*")` + `update_version(LINK_VERSION_KEY)`。
- **成功 200**：
```json
{
  "msg": "链接已删除",
  "id": 3,
  "user_id": 1
}
```
- **错误**：`401`、`403`、`400`。

### 2.20 GET /api/v1/link/user/{user_id} 按用户获取链接列表

- **鉴权**：无。
- **路径参数**：`user_id`（int，用户 id）。
- **查询参数**：

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| page | int | ❌ | 页码，默认 1，`ge=1` |
| size | int | ❌ | 每页条数，默认 10，`ge=1, le=50` |

- **处理流程**：
  1. 取 `link_version` 版本号拼缓存 key（`links_user:v{n}:user_id=X:page=Y:size=Z`），命中缓存直接返回。
  2. 过滤条件集中管理：`Link.author_id == user_id`（**不做公开状态过滤**——作者可看到自己全部链接），列表与总数共用同一组 WHERE。
  3. `join(Link.author)` 联表取作者用户名/头像，按 `updated_at` 倒序分页。
  4. 结果写入缓存（TTL 5 分钟）。
- **成功 200**（`response_model=LinkList`，响应结构同 [2.12](#212-get-apiv1linkgame_id-链接列表)，`item.game_id` 为所属游戏 id）：
```json
{
  "total": 1,
  "items": [
    {
      "item": {
        "id": 3,
        "url": "https://pan.example.com/s/abc",
        "content": "百度网盘",
        "code": "1234",
        "category": "网盘",
        "size": 2.5,
        "size_unit": "GB",
        "status": true,
        "game_id": 5
      },
      "account": {
        "username": "zhangsan",
        "avatar": null
      }
    }
  ]
}
```
- **错误**：`422`（page/size 越界）。
- **路由顺序**：`/user/{user_id}` 声明在 `/{game_id}` 之前（两者段数不同无真实冲突，仍按先具体后通配声明，符合 FastAPI 路由匹配惯例）。
- **缓存失效**：link 的 add/review/delete 均额外清理 `links_user:*` 模式（`links:*` 不匹配 `links_user:*`），避免「我的链接」列表返回旧数据。

---

## comment 模块

### 2.16 GET /api/v1/comment/{game_id} 评论列表

- **鉴权**：无。
- **路径参数**：`game_id`（int，游戏 id）。
- **查询参数**：

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| page | int | ❌ | 页码，默认 1，`ge=1` |
| size | int | ❌ | 每页条数，默认 10，`ge=1, le=50` |

- **处理流程**：
  1. 取 `comment_version` 版本号拼缓存 key（`comments:v{n}:game_id=X:page=Y:size=Z`），命中缓存直接返回。
  2. 先校验游戏存在（不存在 → `404 未找到该游戏`）。
  3. 过滤条件集中管理：`Comment.receive_id == game_id` 且 `Comment.receive_type == int(ReceiveEnum.galgame)`（`ReceiveEnum.galgame=1`），列表与总数共用同一组 WHERE。
  4. `join(Comment.author)` 联表取作者用户名/头像，分页返回。
  5. 结果写入缓存（TTL 5 分钟）。
- **成功 200**（`response_model=CommentList`）：
```json
{
  "total": 1,
  "items": [
    {
      "item": {
        "content": "感谢分享！",
        "receive_id": 5
      },
      "account": {
        "username": "zhangsan",
        "avatar": null
      }
    }
  ]
}
```
- **错误**：`404 未找到该游戏`、`422`（page/size 越界）。

### 2.17 POST /api/v1/comment/add 发表评论

- **鉴权**：Bearer token（必填）。
- **查询参数**：`game_id`（int，目标游戏 id）。
- **请求体** `AddComment`：

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| content | str? | ✅ | 评论内容，1–2000 字符 |

- **处理流程**：
  1. `verify_login` 解析当前用户 ID；校验游戏存在（不存在 → `404 未找到该游戏`）。
  2. 创建 `Comment(content, author_id, receive_id=game_id, receive_type=int(ReceiveEnum.galgame))`。`receive_id` 为裸 Integer 多态设计：`receive_type=galgame` 时存游戏 id，未来兼容 article 等类型。
  3. commit + refresh；`delete_cache_pattern(f"comments:*game_id={game_id}")` + `update_version(COMMENT_VERSION_KEY)`。
- **成功 200**：
```json
{
  "msg": "添加成功",
  "id": 9
}
```
- **错误**：`401`、`404 未找到该游戏`、`422`（content 为空 / 越界）。

### 2.18 PUT /api/v1/comment/edit 编辑评论

- **鉴权**：Bearer token（必填，仅作者可编辑）。
- **查询参数**：`comment_id`（int，评论 id）。
- **请求体** `EditComment`（仅 content）：

| 字段 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| content | str? | ✅ | 评论内容，1–2000 字符 |

- **处理流程**：
  1. `verify_login`；按 `Comment.id == comment_id` 且 `Comment.author_id == user_id` 查对象，找不到或非作者 → `404 没有该评论`。
  2. `content` 非 `None` 时更新。
  3. commit；`delete_cache_pattern("comments:*")` + `update_version(COMMENT_VERSION_KEY)`。
- **成功 200**：
```json
{
  "msg": "编辑成功",
  "id": 9,
  "user_id": 1
}
```
- **错误**：`401`、`404 没有该评论`。

### 2.19 DELETE /api/v1/comment/delete 删除评论

- **鉴权**：Bearer token（必填，仅作者可删）。
- **查询参数**：`comment_id`（int，评论 id）。
- **处理流程**：
  1. `verify_login`；按 `id + author_id` 查对象，找不到或非作者 → `403 没有该评论或者您不是发布者`。
  2. `db.delete` + commit；捕获 `IntegrityError` → `400 无法删除`。
  3. `delete_cache_pattern("comments:*")` + `update_version(COMMENT_VERSION_KEY)`。
- **成功 200**：
```json
{
  "msg": "评论已删除",
  "id": 9,
  "user_id": 1
}
```
- **错误**：`401`、`403`、`400`。

### 2.21 GET /api/v1/comment/user/{user_id} 按用户获取评论列表

- **鉴权**：无。
- **路径参数**：`user_id`（int，用户 id）。
- **查询参数**：

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| page | int | ❌ | 页码，默认 1，`ge=1` |
| size | int | ❌ | 每页条数，默认 10，`ge=1, le=50` |

- **处理流程**：
  1. 取 `comment_version` 版本号拼缓存 key（`comments_user:v{n}:user_id=X:page=Y:size=Z`），命中缓存直接返回。
  2. 过滤条件集中管理：`Comment.author_id == user_id`，列表与总数共用同一组 WHERE。
  3. `join(Comment.author)` 联表取作者用户名/头像，按 `updated_at` 倒序分页。
  4. 结果写入缓存（TTL 5 分钟）。
- **成功 200**（`response_model=CommentList`，响应结构同 [2.16](#216-get-apiv1commentgame_id-评论列表)）：
```json
{
  "total": 1,
  "items": [
    {
      "item": {
        "id": 9,
        "content": "感谢分享！",
        "receive_id": 5
      },
      "account": {
        "username": "zhangsan",
        "avatar": null
      }
    }
  ]
}
```
- **错误**：`422`（page/size 越界）。
- **缓存失效**：comment 的 add/edit/delete 均额外清理 `comments_user:*` 模式（`comments:*` 不匹配 `comments_user:*`），避免「我的评论」列表返回旧数据。

---

## favorite 模块

### 2.22 POST /api/v1/favorite/add 收藏游戏

- **鉴权**：Bearer token（必填）。
- **查询参数**：`gal_id`（int，游戏 id）。
- **处理流程**：
  1. `verify_login` 解析当前用户 ID。
  2. 校验游戏存在（不存在 → `404 游戏不存在`）。
  3. 创建 `Favorite(user_id, gal_id)`，commit；唯一约束冲突（已收藏）→ `409 已收藏`。
  4. SQL 原子自增 `Galgame.favorite += 1`，二次 commit。
  5. `update_version(GAL_VERSION_KEY)` 使缓存版本号自增。
- **成功 200**：
```json
{
  "message": "收藏成功",
  "favorite_id": 1
}
```
- **错误**：`401`、`404 游戏不存在`、`409 已收藏`。

### 2.23 DELETE /api/v1/favorite/remove 取消收藏

- **鉴权**：Bearer token（必填）。
- **查询参数**：`gal_id`（int，游戏 id）。
- **处理流程**：
  1. `verify_login` 解析当前用户 ID。
  2. 按 `user_id + gal_id` 查 `Favorite` 记录，不存在 → `404 收藏不存在`。
  3. `db.delete` + commit。
  4. SQL 原子自减 `Galgame.favorite -= 1`（不低于 0），二次 commit。
  5. `update_version(GAL_VERSION_KEY)`。
- **成功 200**：
```json
{
  "message": "取消收藏成功"
}
```
- **错误**：`401`、`404 收藏不存在`。

### 2.24 GET /api/v1/favorite/visit 访问收藏

- **鉴权**：无。
- **查询参数**：`id`（int，收藏记录 id）。
- **处理流程**：按 id 查 `Favorite`，不存在 → `404 收藏不存在`。
- **成功 200**：
```json
{
  "message": "访问成功",
  "gal_id": 5
}
```
- **错误**：`404 收藏不存在`。

### 2.25 GET /api/v1/favorite/list 收藏列表

- **鉴权**：Bearer token（必填，返回当前用户的收藏）。
- **查询参数**：

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| page | int | ❌ | 页码，默认 1，`ge=1` |
| size | int | ❌ | 每页条数，默认 10，`ge=1` |

- **处理流程**：
  1. `verify_login` 解析当前用户 ID。
  2. 按 `Favorite.user_id == user_id` 过滤，`join(Galgame)` 联表取游戏名称/封面。
  3. 分页返回（`response_model=GalBaseList`）。
- **成功 200**（`response_model=GalBaseList`）：
```json
{
  "total": 2,
  "items": [
    {
      "id": 1,
      "name": "Everlasting Summer",
      "cover": "https://res.cloudinary.com/.../cover.webp"
    }
  ]
}
```
- **错误**：`401`、`422`（page/size 越界）。
- **说明**：收藏列表无缓存（个人数据，命中率低）。

---

## search 模块

### 2.26 GET /api/v1/search/ 搜索游戏

- **鉴权**：无。
- **查询参数**：

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| keyword | str | ✅ | 搜索关键词，`min_length=1` |
| search_type | str? | ❌ | 搜索类型：`name`（默认）/ `tag` / `company` |
| page | int | ❌ | 页码，默认 1，`ge=1` |
| size | int | ❌ | 每页条数，默认 10，`ge=1` |

- **处理流程**：
  1. 拼缓存 key（`Search:keyword=..:search_type=..:page=..:size=..`），命中缓存直接返回。
  2. 关键词转义（`\`/`%`/`_` 替换为转义序列），构造 `LIKE` pattern。
  3. 过滤条件：`status == True`（仅公开作品）+ 按 `search_type` 选择匹配列：
     - `name`：`or_(cn_name.ilike, jp_name.ilike, en_name.ilike)`
     - `tag`：`cast(Galgame.tag, String).ilike`
     - `company`：`cast(Galgame.company, String).ilike`
  4. `join(Galgame.author)` 联表取作者信息，按 `updated_at` 倒序分页。
  5. 总数统计复用同一组 WHERE；结果写入缓存。
- **成功 200**（`response_model=GalList`，结构同游戏列表）：
```json
{
  "total": 1,
  "items": [
    {
      "id": 1,
      "name": "Everlasting Summer",
      "cover": "https://res.cloudinary.com/.../cover.webp",
      "views": 120,
      "author": "zhangsan",
      "avatar": null,
      "author_id": 1
    }
  ]
}
```
- **错误**：`422`（keyword 为空 / page/size 越界）。
- **已知问题**：缓存 key 未携带 `version` 参数，增删改后搜索结果不会立即失效，需等 TTL 过期。

---

## admin 模块

> 管理员专用路由，所有端点需 `verify_admin` 校验 JWT 中的 `is_admin` 字段。

### 2.27 GET /api/admin/control/BrowseGal 浏览待审核游戏

- **鉴权**：Bearer token（必填，管理员）。
- **查询参数**：

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| page | int | ❌ | 页码，默认 1，`ge=1` |
| size | int | ❌ | 每页条数，默认 10，`ge=1` |

- **处理流程**：
  1. `verify_admin` 校验管理员身份，非管理员 → `403 无权限访问`。
  2. 按 `Galgame.status == 0`（待审核/未公开）过滤，按 `id` 倒序分页。
  3. 返回 ID 列表与总数。
- **成功 200**：
```json
{
  "message": "获取成功",
  "total": 5,
  "data": [1, 2, 3, 4, 5]
}
```
- **错误**：`401`、`403 无权限访问`。
- **说明**：当前仅返回 ID 列表，前端需逐个调用 `/api/v1/galgame/{id}` 补充详情（N+1 问题，待优化）。

### 2.28 PUT /api/admin/control/UpdateStatus 更新审核状态

- **鉴权**：Bearer token（必填，管理员）。
- **查询参数**：

| 参数 | 类型 | 必填 | 约束 |
| --- | --- | --- | --- |
| gal_id | int | ✅ | 游戏 id |
| status | bool | ✅ | `true`=通过审核（公开），`false`=拒绝（隐藏） |

- **处理流程**：
  1. `verify_admin` 校验管理员身份。
  2. 执行 `UPDATE galgame SET status=? WHERE id=?`。
  3. commit；清理缓存（`Galgame:*` + `Gal_visit:*id={gal_id}`）+ `update_version(GAL_VERSION_KEY)`。
- **成功 200**：
```json
{
  "message": "已通过该游戏",
  "gal_id": 5,
  "status": true
}
```
- **错误**：`401`、`403`、`500`（更新状态时发生错误）。
- **已知问题**：不校验 `gal_id` 是否存在，不存在的 id 也返回成功消息并触发缓存失效。

### 2.29 DELETE /api/admin/control/DeleteGal 管理员删除游戏

- **鉴权**：Bearer token（必填，管理员）。
- **查询参数**：`gal_id`（int，游戏 id）。
- **处理流程**：
  1. `verify_admin` 校验管理员身份。
  2. 执行 `DELETE FROM galgame WHERE id=?`。
  3. commit；捕获 `IntegrityError`（存在关联数据）→ `400 该游戏存在关联数据，无法删除`。
  4. 清理缓存（`Galgame:*` + `Gal_visit:*id={gal_id}` + `gal_views:{gal_id}` + `links:*game_id={gal_id}`）+ `update_version(GAL_VERSION_KEY)`。
- **成功 200**：
```json
{
  "message": "已删除该游戏",
  "gal_id": 5
}
```
- **错误**：`401`、`403`、`400`（存在关联数据）、`500`。
- **已知问题**：同 2.28，不校验 `gal_id` 是否存在。

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
| `GalItem` | id, name, cover, views, author, avatar?, author_id? | 列表项（含作者 id，供作者校验/管理入口判断） |
| `GalList` | total, items: List[GalItem] | 列表响应（`response_model`） |
| `AddGal` | name?, 三名称(至少一)、content?, company?, category?(CategoryEnum), cover(必填), images?, tag?, platfrom? | 发布（含名称校验器，`_normalize_names` 自动派生 name） |
| `EditGal` | name?, 同 AddGal 但全可选 | 编辑 |
| `GalBase` | id, name, cover | 收藏列表项（精简字段） |
| `GalBaseList` | total, items: List[GalBase] | 收藏列表响应（`response_model`） |

**schemas/link.py**

| 模型 | 字段 | 用途 |
| --- | --- | --- |
| `LinkItem` | id, url, content?, code?, category?, size?(float), size_unit?, status, game_id | 列表项（含审核状态与所属游戏 id） |
| `LinkItems` | item: LinkItem, account: UserInfo | 列表项 + 发布者信息 |
| `LinkList` | total, items: List[LinkItems] | 列表响应（`response_model`） |
| `AddLink` | url(必填, 1–255), content?, code?, category?, size?(float), size_unit? | 新增（服务端强制 status=True，请求体不含 status） |
| `EditLink` | content?, code?, category?, size?(float), size_unit? | 编辑（全可选，不含 url） |

**schemas/comment.py**

| 模型 | 字段 | 用途 |
| --- | --- | --- |
| `CommentItem` | content?, receive_id | 单条评论内容（含所属游戏 id） |
| `CommentItems` | item: CommentItem, account: UserInfo | 列表项 + 发布者信息 |
| `CommentList` | total, items: List[CommentItems] | 列表响应（`response_model`） |
| `AddComment` | content(1–2000) | 新增（接收对象由路由参数 game_id 传入） |
| `EditComment` | content(1–2000) | 编辑（仅 content） |

**model/enums.py**

| 枚举 | 值 | 说明 |
| --- | --- | --- |
| `PlatformEnum` | `PC`="电脑端"、`AZ`="安卓端"、`OTHER`="Other" | 支持平台，model 与 schemas 共同引用 |
| `CategoryEnum` | `PLOT`="剧情向"、`HEALING`="治愈系"、`DAILY`="日常系"、`ROMANCE`="恋爱模拟"、`ADV`="文字冒险"、`RPG`="RPG"、`MANAGEMENT`="经营模拟"、`ERO`="拔作"、`ALL_AGES`="全年龄"、`OTHER`="其他" | 作品分类 |
| `ReceiveEnum` | `article`=0、`galgame`=1 | 接收对象类型（`comment.receive_type` 使用，int 枚举） |
| `SizeUnitEnum` | `KB`="KB"、`MB`="MB"、`GB`="GB" | 链接大小单位 |
| `SearchEnum` | `name`="name"、`tag`="tag"、`company`="company" | 搜索类型（已定义但 search.py 尚未绑定使用） |

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

> 关联：`galgames` / `links` / `comments` 三个集合侧关系均为 `lazy="raise"`（禁止隐式加载，需显式 `selectinload`），避免任何 User 查询全量拉取关联数据。

### 数据库表 `galgame`（model/galgame.py）

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| id | Integer | 主键自增 |
| name | String(50) | **唯一、非空**（统一名称，由 schema 自动从三名称派生） |
| cn_name / en_name / jp_name | String(50) | 非空，Python 侧默认空串 |
| content | Text? | 游戏简介 |
| company | JSON? | 制作公司列表 |
| category | String(50) | 默认 `其他`（列保持字符串，兼容历史自由文本；枚举约束在 schema/筛选层） |
| cover | String(255) | 封面 URL |
| images | JSON? | 截图 URL 列表 |
| tag | JSON? | 标签列表 |
| views / likes / favorite | Integer | 默认 0 |
| platfrom | JSON? | 支持平台（枚举值列表，字段拼写保留现状） |
| status | Boolean | 默认 False（新增游戏待审核，管理员审核后公开） |
| author_id | Integer | 外键 `user.id`，`ondelete=RESTRICT` |
| created_at / updated_at | DateTime | 自动维护 |

> 关系：`author` 多对一 `lazy="selectin"`；`links` / `favorites` 集合侧 `lazy="raise"`（禁止隐式加载，需显式 `selectinload`）。

### 数据库表 `link`（model/link.py）

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| id | Integer | 主键自增 |
| url | String(255) | 链接（非空） |
| content | String(255)? | 链接内容 |
| code | String(255)? | 提取码 |
| author_id | Integer | 外键 `user.id`，`ondelete=RESTRICT` |
| game_id | Integer | 外键 `galgame.id`，`ondelete=RESTRICT` |
| category | String(255)? | 链接类型 |
| size | Float? | 大小数值（配合 size_unit 使用） |
| size_unit | Enum(KB/MB/GB)? | 大小单位 |
| status | Boolean | 默认 True（新增即公开） |
| created_at / updated_at | DateTime | 自动维护 |

> 关系：`author` / `galgame` 多对一均为 `lazy="selectin"`；`Galgame.links` / `User.links` 集合侧 `lazy="raise"`。

### 数据库表 `comment`（model/comment.py）

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| id | Integer | 主键自增 |
| content | Text? | 评论内容 |
| author_id | Integer | 外键 `user.id`，`ondelete=RESTRICT` |
| receive_id | Integer | 接收对象 id（裸 Integer 多态：`receive_type=galgame` 时存游戏 id，不做外键，兼容未来 article 等类型） |
| receive_type | Integer | 接收类型（`ReceiveEnum.galgame=1`） |
| created_at / updated_at | DateTime | 自动维护 |

> 关系：`author` 多对一 `lazy="selectin"`；`User.comments` 集合侧 `lazy="raise"`。

### 数据库表 `favorite`（model/favorite.py）

| 字段 | 类型 | 约束 |
| --- | --- | --- |
| id | Integer | 主键自增 |
| user_id | Integer | 外键 `user.id`，`ondelete=RESTRICT` |
| gal_id | Integer | 外键 `galgame.id`，`ondelete=RESTRICT` |
| created_at | DateTime | `server_default=func.now()` |

> 唯一约束：`UniqueConstraint("user_id", "gal_id", name="uq_favorite_user_gal")`，同一用户对同一游戏只能收藏一次。
> 关系：`author`（User）/ `galgame`（Galgame）多对一均为 `lazy="selectin"`；`User.favorites` / `Galgame.favorites` 集合侧 `lazy="raise"`。

---

## 4. 错误码一览

| 状态码 | 场景 | 说明 |
| --- | --- | --- |
| 401 | 用户名或密码不正确 / 未提供凭证 / token 无效 | 鉴权失败统一 401 |
| 400 | 验证码不正确或已过期 / 参数错误 / 用户存在关联作品无法删除 / 该游戏存在关联链接无法删除 / 该游戏存在关联数据无法删除（admin）/ 无法删除（link/comment 删除兜底）/ update 唯一索引兜底 | 业务校验失败 |
| 403 | galgame/link/comment 非发布者 / 详情未公开 / admin 无权限 | 无权限 / 资源不可见 |
| 404 | 用户不存在 / 游戏未找到 / 游戏不存在（favorite）/ 收藏不存在 / 没有该评论（comment edit） | 按 id/token 定位不到 |
| 409 | 用户名或邮箱已存在（register/update）/ 该游戏已存在（add）/ 已收藏（favorite add） | 唯一性冲突 |
| 422 | 头像上传失败 / 封面图上传失败 / 图片上传失败 / Pydantic 校验失败（page、size 越界、三名称全空、url/content 越界） | 请求不合法 |
| 500 | 发送验证码失败 / 图片上传失败 / admin 操作异常 / 未捕获异常 | 依赖故障或兜底缺失 |

---

## 5. 已知限制与注意事项

1. **galgame 列表接口 `User.name` 引用错误（已修复）**：此前 `index` 查询误写 `User.name`（模型字段为 `username`），运行时抛 `AttributeError` → `GET /api/v1/galgame/` 返回 500；当前代码已改为 `User.username`，接口正常。
2. **Token 无过期时间**：`jwt.encode` 未带 `exp`，`security.py` 中 `ACCESS_TOKEN_EXPIRE_MINUTES` 被注释。测试阶段已知问题，上线前需补有效期。
3. **改绑邮箱无验证码校验**：`update` 修改 `email` 仅排重、不验证邮箱归属；`register` 是校验验证码的。若未来有「忘记密码」流程，此处是攻击入口。
4. **头像注册原样入库**：`register` 的 `avatar` 直接存请求原值，不经过 WebP 转换 / Cloudinary 上传（只有 `update` 与 galgame 上传走转换上传）。
5. **`login/register` 的密码校验/哈希为同步调用**：未用 `run_in_threadpool` 包裹（argon2 为刻意慢哈希），高并发下可能阻塞事件循环。
6. **删除为物理删除**：`db.delete` 硬删行，未利用 `status` 字段做软删除；用户删除在有 galgame 作品时会因外键 `RESTRICT` 返回 400（已兜底，但历史引用仍可能受影响）。
7. **`email/send` 的 email 是 query 参数**：请求形如 `?email=xxx`，不是 JSON body（既有框架文档此处有误，以本文档/OpenAPI 为准）。
8. **CORS**：`allow_origins=["*"]` + `allow_credentials=True` 组合不符合浏览器规范且有安全风险，生产需改为域名白名单。
9. **无速率限制**：验证码发送、登录接口均无限流，存在被刷风险。
10. **`register`/`update` 唯一性查重存在 TOCTOU 窗口**：`update` 已用唯一索引 + `IntegrityError` 兜底，`register` 尚未加该兜底。
11. **列表排序不稳定**：galgame/link/comment 列表均按 `updated_at` 倒序但无次级排序，同值记录分页可能重复/遗漏。
12. **字段拼写问题**：`platfrom`（应为 platform）、`update_at`（应为 updated_at）为既有拼写，改库需迁移。
13. **`resend` 未入 `requirements.txt`**：venv 已装，新环境按清单安装后邮件功能会 `ImportError`。
14. **无 Alembic 迁移 / 无 `create_all`**：`user`/`galgame`/`link`/`comment`/`favorite` 表需手动创建，结构漂移靠人眼比对。新增 `galgame.name` 列（UNIQUE + NOT NULL）和 `favorite` 表需要手动 DDL 迁移。
15. **无测试、无 lint、无请求级日志**：全程 `print`/`logging`，无结构化日志与 trace_id。
16. **link/comment 非本人状态码语义不一致**：comment `edit` 非本人返回 `404 没有该评论`，`delete` 非本人返回 `403`；link `review`/`delete` 非本人均返回 `403`。同为「非本人」场景状态码未统一。
17. **comment 缓存清理粒度不一致**：`add` 只清理 `comments:*game_id={game_id}`，`edit`/`delete` 清理 `comments:*`（全量）。功能正确但粒度不同，量大时可统一为按游戏清理。注意 `comments:*` 不匹配按用户的 `comments_user:*` key，故三处均额外 `delete_cache_pattern("comments_user:*")`；link 模块同理（`links_user:*`）。
18. **link 编辑端点命名不统一**：link 的编辑端点为 `PUT /link/review`，galgame/comment 均为 `/edit`。
19. **link/comment 的 `receive_id` 多态设计**：comment 以「裸 Integer `receive_id` + `receive_type`」区分目标对象，目前仅实现 `galgame` 类型且未做外键，无外键约束时脏 id 不会在 DB 层被拦截。
20. **search 缓存 key 未携带 version**：`search.py` 的 `get_cache_key("Search", ...)` 未传入 `version` 参数，增删改后搜索结果不会立即失效，需等 TTL（300s）过期。
21. **galgame 列表 keyword 搜索未转义 LIKE 通配符**：`galgame.py` 的 `index` 端点 `ilike` 未转义 `%`/`_`，`search.py` 已做转义但此处遗漏，两处应共用转义函数。
22. **admin 接口不校验目标是否存在**：`UpdateStatus` 和 `DeleteGal` 在 `gal_id` 不存在时 `rowcount=0`，仍返回成功消息并无意义地递增版本号。
23. **admin BrowseGal 仅返回 ID 列表**：前端被迫逐个调用详情接口补充信息，产生 N+1 请求问题。
24. **`main.py` 重复导入 `CORSMiddleware`**：第 2 行和第 9 行重复导入同一模块，无害但冗余。
25. **`SearchEnum` 已定义但未使用**：`model/enums.py` 定义了 `SearchEnum`，但 `search.py` 的 `search_type` 参数为 `Optional[str]`，未绑定枚举校验，非法值静默走 `name` 分支。
26. **`control.py` 使用 `print` 而非 logger**：异常处理中使用 `print` 输出错误信息，生产环境下不会被日志收集器捕获。
27. **`control.py` 中 `Galgame.status == 0` 与 Boolean 语义不一致**：其他文件使用 `== True`/`== False`，此处用 `== 0`，MySQL 下行为等价但语义不统一。
