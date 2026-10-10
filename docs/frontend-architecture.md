# Fishmo 前端架构说明

> 本文档基于 `frontend/` 目录的源码分析生成，涵盖中间件、路由/页面、组件、布局、组合函数、类型定义、工具函数、插件与样式主题的完整说明。

---

## 目录结构概览

```
frontend/
├── app.vue                   # 应用入口：NuxtLayout + NuxtPage
├── nuxt.config.ts             # Nuxt 3 配置（开发工具、组件、模块、CSS、代理、类型检查、页面过渡、head）
├── package.json               # 依赖声明
│
├── layouts/
│   └── default.vue            # 默认布局：固定顶栏 + 移动端抽屉 + 主内容 + 页脚
│
├── pages/                     # 路由页面（Nuxt 文件路由）
│   ├── index.vue              # 首页
│   ├── games/
│   │   └── index.vue          # 全部游戏页
│   ├── galgame/
│   │   └── [id].vue           # 游戏详情页
│   ├── user/
│   │   ├── index.vue          # 登录/注册页
│   │   └── profile.vue        # 个人主页
│   ├── publish/
│   │   └── index.vue          # 发布游戏页
│   ├── articles/
│   │   └── index.vue          # 文章列表页（分类筛选 + 4 列网格 + 分页）
│   ├── article/
│   │   └── [id].vue           # 文章详情页（Markdown 渲染 + 插图画廊 + 评论）
│   ├── manage/
│   │   ├── index.vue          # 我的管理总览页（游戏/文章/评论/链接四 Tab）
│   │   ├── [id].vue           # 单个游戏管理页
│   │   └── article/
│   │       └── [id].vue       # 文章编辑页
│   └── admin/
│       └── index.vue          # 管理员控制台
│
├── middleware/
│   ├── auth.ts                # 登录守卫
│   └── admin.ts               # 管理员守卫
│
├── components/                # 组件（pathPrefix: false，组件名直接使用文件名）
│   ├── article/
│   │   ├── ArticleForm.vue    # 文章发布/编辑表单（双栏：设定侧栏 + Markdown 编辑器 + 草稿自动保存）
│   │   └── ArticlePopup.vue   # 首页文章弹出面板（4 列网格，快速浏览）
│   ├── user/
│   │   ├── LoginForm.vue      # 登录表单
│   │   ├── RegisterForm.vue   # 注册表单（含邮箱验证码）
│   │   ├── ProfileForm.vue    # 个人资料编辑（头像/用户名/邮箱/简介/密码/删除账号）
│   │   └── MyFavorites.vue    # 我的收藏（封面网格 + 分页）
│   ├── galgame/
│   │   ├── GameCard.vue       # 游戏卡片（首页/列表的网格项）
│   │   └── GalgameForm.vue    # 游戏发布/编辑分步表单
│   ├── comment/
│   │   └── CommentList.vue    # 评论区（支持 galgame/article 双类型，含发表/编辑/删除）
│   ├── link/
│   │   ├── LinkList.vue       # 链接列表展示
│   │   ├── LinkAddDialog.vue  # 添加链接弹窗
│   │   └── LinkManage.vue     # 链接管理（增删改）
│   └── manage/
│       ├── MyGames.vue        # 我的游戏列表（小型卡片网格）
│       ├── MyArticles.vue     # 我的文章列表（小型卡片网格）
│       ├── MyComments.vue     # 我的评论列表
│       └── MyLinks.vue        # 我的链接列表
│
├── composables/               # 组合函数（useXxx 模式）
│   ├── useGalgame.ts          # 游戏相关：列表/详情/增/删/改
│   ├── useComment.ts          # 评论相关：列表/用户列表/增/删/改
│   ├── useLink.ts             # 链接相关：列表/用户列表/增/删/改
│   ├── useAuth.ts             # 认证相关：登录/注册/发码/资料查看与编辑/删除账号
│   ├── useFavorite.ts         # 收藏相关：添加/取消/列表（分页）
│   ├── useArticle.ts          # 文章相关：列表/详情/管理列表/发布/编辑/删除
│   └── useColorMode.ts        # 仅深色模式（始终返回 isDark=true，无切换功能）
│
├── stores/
│   └── auth.ts                # Pinia 认证状态（token/userId/username/avatar/isAdmin）
│
├── types/                     # TypeScript 类型定义
│   ├── index.ts               # 统一导出入口（export * from 五个模块）
│   ├── user.ts                # 用户模块类型
│   ├── galgame.ts             # galgame 模块类型（含枚举常量和收藏类型）
│   ├── link.ts                # 链接模块类型
│   ├── comment.ts             # 评论模块类型
│   └── article.ts             # 文章模块类型（ArticleItem / ArticleList / ArticlePublish / ArticleDetail 等）
│
├── plugins/
│   ├── auth.client.ts         # 客户端插件：从 localStorage 恢复登录态
│   └── element-plus.ts        # Element Plus 全局注册（中文语言包 + 图标 + SSR 兼容）
│
├── utils/
│   ├── request.ts             # 统一请求封装（api/cleanParams/getErrDetail）
│   ├── file.ts                # 文件读取（base64 转换 + 大小校验）
│   ├── link.ts                # 链接安全校验（协议白名单）
│   ├── color.ts               # 封面主色提取（客户端 Canvas 采样）
│   └── format.ts              # 链接大小格式化（新旧数据兼容）
│
├── assets/
│   └── css/
│       └── theme.css          # 设计系统令牌 + Element Plus 变量覆盖 + 全局样式（仅深色模式）

└── public/
    ├── status/
    │   ├── 1.png              # 加载失败/错误状态插图
    │   └── 2.png              # 空数据状态插图
    └── background/            # 背景图片（用户可在设置面板中选取）
```

---

## 1. 中间件（middleware/）

Nuxt 3 的路由中间件，在页面渲染前执行守卫逻辑。项目有两个中间件，均在客户端侧判断（SSR 阶段不做跳转）。

### 1.1 `auth.ts` —— 登录守卫

| 属性 | 说明 |
|---|---|
| **用途** | 拦截需要登录才能访问的页面，未登录用户跳转登录页 |
| **拦截路由** | `/user/profile`、`/publish`、`/manage`、`/manage/[id]`、`/manage/article/[id]` |
| **工作原理** | 读取 `useAuthStore().token`；仅在 `import.meta.client` 时判断（SSR 阶段 localStorage 不可用，token 为空）。未登录时跳转 `/user?redirect=<当前路径>` ，登录页完成后回跳 |
| **涉及存储** | `stores/auth.ts`（token） |
| **涉及页面** | `user/profile.vue`（调用 `definePageMeta({ middleware: 'auth' })`）、`publish/index.vue`、`manage/index.vue`、`manage/[id].vue` |

### 1.2 `admin.ts` —— 管理员守卫

| 属性 | 说明 |
|---|---|
| **用途** | 拦截非管理员用户访问管理后台 |
| **拦截路由** | `/admin` |
| **工作原理** | 读取 `useAuthStore().isAdmin`；仅在 `import.meta.client` 时判断。非管理员跳转首页 `/` |
| **涉及存储** | `stores/auth.ts`（isAdmin） |
| **涉及页面** | `admin/index.vue`（调用 `definePageMeta({ middleware: 'admin' })`） |

---

## 2. 路由 / 页面（pages/）

Nuxt 3 文件路由，每个 `.vue` 文件对应一个路由路径。

### 2.1 首页 —— `/`（`pages/index.vue`）

| 属性 | 说明 |
|---|---|
| **功能** | 网站首页，展示精选 Hero + 热门游戏 + 最新发布三个区块 |
| **数据来源** | `useGalgameList()` 组合函数，分别按 `sort: 'views'`（热门）与默认时间倒序（最新）拉取 top 10 |
| **精选 Hero** | 取热门列表首项作为精选，封面大图背景 + 底部渐变遮罩（`0→rgba(0,0,0,0.85)`）+ 玻璃拟态标签（`backdrop-filter: blur(8px)`）+ 标题/作者/浏览量；深色模式增加 `0 0 0 1px rgba(143,142,245,0.08)` 微光边框；hover 时向上微移 3px |
| **热门游戏** | 横向滚动列表，封面缩略图 + 排名序号（前 3 高亮） |
| **最新发布** | 网格展示，使用 `GameCard` 组件 |
| **使用组件** | `GameCard` |
| **调用 API** | `GET /api/v1/galgame/?page=1&size=10&sort=views` 和 `GET /api/v1/galgame/?page=1&size=10` |
| **Hero CSS 关键样式** | `.hero-overlay { background: linear-gradient(to top, rgba(0,0,0,0.85) 0%, rgba(0,0,0,0.45) 35%, transparent 65%) }`、`.hero-badge { background: rgba(143,142,245,0.15); backdrop-filter: blur(8px) }`、`html.dark .hero-card { box-shadow: 0 0 0 1px rgba(143,142,245,0.08) }` |

### 2.2 全部游戏 —— `/games`（`pages/games/index.vue`）

| 属性 | 说明 |
|---|---|
| **功能** | 游戏列表浏览与筛选，支持分类、平台筛选，从详情页标签跳转的标签搜索 |
| **URL 同步** | 筛选条件（category / platform / page / search_type / keyword）同步到 URL query，支持分享/刷新/前进后退 |
| **筛选逻辑** | 当 `searchType=tag` 时调用搜索 API，否则调用游戏列表 API |
| **状态处理** | 加载骨架屏（`el-skeleton`）、错误提示使用 `/status/1.png` 插图 + 重试按钮、空状态使用 `el-empty` |
| **使用组件** | `GameCard` |
| **调用 API** | `GET /api/v1/galgame/`（常规列表）或 `GET /api/v1/search/`（标签搜索） |
| **引用类型** | `CATEGORY_OPTIONS`、`PLATFORM_OPTIONS`、`GalgameListQuery`（来自 `types/galgame.ts`） |
| **工具函数** | `api`、`cleanParams`（来自 `utils/request.ts`） |

### 2.3 游戏详情 —— `/galgame/[id]`（`pages/galgame/[id].vue`）

| 属性 | 说明 |
|---|---|
| **功能** | 游戏完整详情页：影院式 Hero 区、游戏简介、截图画廊、资源链接、评论、信息侧栏 |
| **数据来源** | `useGalgameDetail(id)` 组合函数，响应式监听 `route.params.id` |
| **封面主色** | `onMounted` 时调用 `extractCoverAccent()` 将提取色写入 `--cover-accent` CSS 变量 |
| **收藏交互** | 客户端状态管理 `isFavorited` + `favoriteCount`，调用 `addFavorite` / `removeFavorite` |
| **作者操作** | 通过 `isOwner`（user_id === author_id）判断显示"编辑游戏"和"删除游戏"按钮 |
| **组件组合** | |
| | 区块一：影院 Hero（封面大图 / 遮罩 / 标题 / 标签 / 三名称 / 元数据 / 收藏按钮 / 作者操作按钮） |
| | 区块二：游戏简介（富文本行内容） |
| | 区块三：截图画廊（`el-image` 预览组） |
| | 区块四：资源链接（`LinkList` + `LinkAddDialog`） |
| | 区块五：评论（`CommentList`） |
| | 侧栏：游戏信息 / 数据统计（`sticky` 定位） |
| **使用组件** | `LinkList`、`LinkAddDialog`、`CommentList` |
| **调用 API** | `GET /api/v1/galgame/{id}` |
| **认证相关** | 收藏与链接操作需登录，未登录提示跳转 `/user?redirect=...` |

### 2.4 登录 / 注册 —— `/user`（`pages/user/index.vue`）

| 属性 | 说明 |
|---|---|
| **功能** | 登录与注册双 Tab 页 |
| **URL 控制** | `?mode=register` 初始默认注册 Tab；已登录或 `?mode=profile` 跳转 `/user/profile` |
| **组件组合** | Tab 面板：`LoginForm` / `RegisterForm` |
| **安全** | 注册成功后 `@registered` 事件自动切回登录 Tab |
| **使用组件** | `LoginForm`、`RegisterForm` |

### 2.5 个人主页 —— `/user/profile`（`pages/user/profile.vue`）

| 属性 | 说明 |
|---|---|
| **守卫** | `definePageMeta({ middleware: 'auth' })` |
| **功能** | 用户个人主页：资料展示 + 侧边菜单数据面板（游戏/评论/链接/收藏/设置） |
| **资料卡片** | 头像（渐变光晕边框）、用户名、UID、邮箱、简介；管理员显示管理控制台入口 |
| **菜单面板** | `games` → `MyGames` / `comments` → `MyComments` / `links` → `MyLinks` / `favorites` → `MyFavorites` / `settings` → `ProfileForm` |
| **登出按钮** | 侧边栏底部红色退出按钮 |
| **使用组件** | `MyGames`、`MyComments`、`MyLinks`、`MyFavorites`、`ProfileForm` |
| **调用 API** | `GET /api/v1/user/`（获取用户信息） |
| **引用类型** | `UserProfile` |

### 2.6 文章列表 —— `/articles`（`pages/articles/index.vue`）

| 属性 | 说明 |
|---|---|
| **功能** | 文章列表浏览，支持分类标签筛选（攻略/资讯/公告/教程/其他），分页 |
| **数据来源** | `useArticleList(page, size, activeCategory)` |
| **布局** | 4 列网格（16:10 封面 + 浏览量/评论数徽标 + 标题 + 时间），响应式 3/2/1 列 |
| **状态处理** | 加载骨架屏（8 个骨架卡片）、错误使用 `/status/1.png` 插图、空使用 `/status/2.png` 插图 |
| **调用 API** | `GET /api/v1/article/` |
| **引用类型** | `ArticleItem`（来自 `types/article.ts`） |

### 2.7 文章详情 —— `/article/[id]`（`pages/article/[id].vue`）

| 属性 | 说明 |
|---|---|
| **功能** | 文章完整详情页：21:9 宽幅封面（移动端 16:9）+ Markdown 渲染正文 + 标签链接 + 插图画廊 + 评论区 |
| **数据来源** | `useArticleDetail(articleId)`，响应式监听 `route.params.id` |
| **Markdown 渲染** | `markdown-it`（html/linkify/typographer 开启）+ `DOMPurify` 客户端消毒 |
| **浏览计数** | 页面加载时 `ArticleViewCounter.incr()` + DB 存储值叠加展示 |
| **评论区** | `<CommentList :game-id="numericId" type="article" />`，`receive_type=0` 限定文章评论 |
| **使用组件** | `CommentList` |
| **调用 API** | `GET /api/v1/article/{id}` |

### 2.8 发布游戏 —— `/publish`（`pages/publish/index.vue`）

| 属性 | 说明 |
|---|---|
| **守卫** | `definePageMeta({ middleware: 'auth' })` |
| **功能** | 发布新游戏表单 |
| **组件组合** | `GalgameForm`（mode="add"） |
| **提交流程** | `addGalgame(payload)` → 成功后跳转 `navigateTo(/galgame/${res.id})` |
| **使用组件** | `GalgameForm` |
| **调用 API** | `POST /api/v1/galgame/add` |
| **引用类型** | `AddGal`、`EditGal` |

### 2.9 我的管理 —— `/manage`（`pages/manage/index.vue`）

| 属性 | 说明 |
|---|---|
| **守卫** | `definePageMeta({ middleware: 'auth' })` |
| **功能** | 管理我的游戏 / 文章 / 评论 / 链接（四个 Tab） |
| **URL 同步** | `?tab=comment` / `?tab=link` / `?tab=article` 支持 Tab 切换同步到 URL |
| **组件组合** | Tab 面板：`MyGames` / `MyArticles` / `MyComments` / `MyLinks` |
| **使用组件** | `MyGames`、`MyArticles`、`MyComments`、`MyLinks` |

### 2.10 单个游戏管理 —— `/manage/[id]`（`pages/manage/[id].vue`）

| 属性 | 说明 |
|---|---|
| **守卫** | `definePageMeta({ middleware: 'auth' })` |
| **功能** | 编辑单个游戏信息 + 管理该游戏下载链接 |
| **作者校验** | 客户端水合后通过 `isOwner` 判断；非作者显示错误提示 |
| **组件组合** | 作者区域：`GalgameForm`（mode="edit"） + 删除按钮 + `LinkManage` |
| **使用组件** | `GalgameForm`、`LinkManage` |
| **调用 API** | `GET /api/v1/galgame/{id}`（加载）、`PUT /api/v1/galgame/edit`（编辑）、`DELETE /api/v1/galgame/delete`（删除） |

### 2.11 文章编辑 —— `/manage/article/[id]`（`pages/manage/article/[id].vue`）

| 属性 | 说明 |
|---|---|
| **守卫** | `definePageMeta({ middleware: 'auth' })` |
| **功能** | 编辑单个文章信息（Markdown 内容/封面/标签/分类等）|
| **作者校验** | 客户端水合后通过 `isOwner`（`author_id === auth.userId`）判断；非作者显示错误提示 |
| **组件组合** | `ArticleForm`（mode="edit"） + 删除按钮 |
| **使用组件** | `ArticleForm` |
| **调用 API** | `GET /api/v1/article/{id}`（加载）、`PUT /api/v1/article/edit`（编辑）、`DELETE /api/v1/article/delete`（删除） |

### 2.12 管理员控制台 —— `/admin`（`pages/admin/index.vue`）

| 属性 | 说明 |
|---|---|
| **守卫** | `definePageMeta({ middleware: 'admin' })` |
| **功能** | 游戏审核管理：查看待审核游戏列表，支持通过/拒绝/删除操作 |
| **工作原理** | 调用 `/api/admin/control/BrowseGal` 获取待审核游戏 ID 列表 → 批量请求详情 → 展示审核列表 |
| **状态处理** | 加载骨架屏、错误提示使用 `/status/1.png` 插图、空状态（无待审核游戏）使用 `/status/1.png` 插图 |
| **审核操作** | 通过（`UpdateStatus?status=true`）、拒绝（`UpdateStatus?status=false`）、删除（`DeleteGal`） |
| **批量详情** | 并行 `Promise.allSettled(fetchGameDetails(ids))` 批量获取游戏封面/名称/作者 |
| **调用 API** | `GET /api/admin/control/BrowseGal`、`PUT /api/admin/control/UpdateStatus`、`DELETE /api/admin/control/DeleteGal` |

---

## 3. 组件（components/）

Nuxt 3 配置了 `pathPrefix: false`，组件名直接使用文件名，无需目录前缀（例如 `components/user/LoginForm.vue` 使用 `<LoginForm />` 而非 `<UserLoginForm />`）。

### 3.1 用户相关（components/user/）

#### `LoginForm.vue`
| 属性 | 说明 |
|---|---|
| **用途** | 用户名 + 密码登录表单 |
| **交互** | 支持 Enter 提交；登录成功后根据 `redirect` 参数回跳（安全校验：仅允许站内相对路径） |
| **调用 API** | `POST /api/v1/user/login`（通过 `useAuth().login()`） |
| **涉及存储** | 登录成功后调用 `authStore.setAuth()` 写入 token/userId/username/isAdmin |

#### `RegisterForm.vue`
| 属性 | 说明 |
|---|---|
| **用途** | 用户注册表单（用户名 + 邮箱 + 验证码 + 密码 + 个人简介） |
| **邮箱验证码** | 先发送验证码（`useEmail().sendCode()`），带 60 秒倒计时防重复发送 |
| **校验** | 用户名 2-20 字符、密码 6-20 字符、两次密码一致、验证码非空 |
| **事件** | `@registered` 注册成功后通知父组件切到登录 Tab |
| **调用 API** | `POST /api/v1/email/send`（发送验证码）、`POST /api/v1/user/register`（注册） |

#### `ProfileForm.vue`
| 属性 | 说明 |
|---|---|
| **用途** | 个人资料编辑表单（头像上传、用户名、邮箱、个人简介、修改密码、删除账号） |
| **头像处理** | `el-upload` 客户端选择图片 → `readImageAsBase64()` 转为 base64 → 提交时作为 avatar 字段 |
| **安全** | 删除账号前弹出 `ElMessageBox.confirm` 确认；后端外键限制有游戏时无法删除 |
| **布局特点** | 头像左移 150px（`.form-top-row .avatar-item { margin-left: 150px }`），表单字段右移 100px（`.form-fields-group { margin-left: 100px }`，输入框 max-width 250px），简介左右各收缩 50px（`.bio-item { padding: 65px }`），保存按钮右对齐 |
| **调用 API** | `GET /api/v1/user/`（加载）、`PUT /api/v1/user/update`（更新）、`DELETE /api/v1/user/delete`（删除账号） |

#### `MyFavorites.vue`
| 属性 | 说明 |
|---|---|
| **用途** | 我的收藏：封面小网格 + 分页 + 取消收藏 |
| **状态** | 从未收藏时显示空状态插图；取消收藏后刷新列表 |
| **调用 API** | `GET /api/v1/favorite/list`（收藏列表）、`DELETE /api/v1/favorite/remove`（取消收藏） |

### 3.2 游戏相关（components/galgame/）

#### `GameCard.vue`
| 属性 | 说明 |
|---|---|
| **用途** | 游戏列表卡片，首页/全部游戏页的网格项 |
| **Props** | `item: GalItem`（id, name, cover, views, author, avatar） |
| **展示** | 2:3 封面图（hover 微缩放 + accent 光晕）+ 标题 + 作者（头像+名称）+ 浏览量，全卡片可点 |
| **构成** | 使用 `el-card`（shadow="never"，自带 padding 覆盖为 0） |
| **透明背景** | `.game-card { background: transparent !important; }` 露出 body 背景图 |

#### `GalgameForm.vue`
| 属性 | 说明 |
|---|---|
| **用途** | 游戏发布与编辑共用的多步骤表单（分步向导） |
| **Props** | `mode: 'add' | 'edit'`、`initial?: GalgameDetail`（编辑模式回填）、`submitting?: boolean` |
| **步骤** | 3 步：基本信息（三名称/分类/标签/平台）→ 游戏简介（textarea）→ 封面与截图 + 卡片预览 |
| **封面/截图** | 客户端选取 → `readImageAsBase64()` → base64 提交（后端统一转 WebP） |
| **编辑器** | 公司/标签使用 `el-select` allow-create（回车添加新选项） |
| **平台选择** | 自定义 chip 按钮多选 |
| **预览** | 步骤 3 右侧实时卡片预览，展示名称/副名/标签 |
| **校验** | add 模式：至少一个名称 + 封面必填；edit 模式后端全可选，放宽校验 |
| **事件** | `@submit(payload)` 发射 AddGal 或 EditGal（编辑模式仅携带变更字段） |
| **引用类型** | `PLATFORM_OPTIONS`、`CATEGORY_OPTIONS`、`PlatformValue`、`CategoryValue` |

### 3.3 文章相关（components/article/）

#### `ArticleForm.vue`
| 属性 | 说明 |
|---|---|
| **用途** | 文章发布与编辑共用的双栏表单（侧栏设定 + Markdown 主编辑器） |
| **Props** | `mode: 'add' \| 'edit'`、`initial?: Partial<ArticlePublish>`、`submitting?: boolean` |
| **侧栏（220px）** | 分类输入（`CATEGORY_OPTIONS`: 游戏评测/推荐/攻略教程/业界资讯/玩家杂谈/技术分享/其他）、标签输入、封面上传（建议 16:9） |
| **主编辑器** | 标题输入 + Markdown 工具栏（加粗/斜体/删除线/标题/列表/代码/预览切换）+ textarea（auto-resize）+ 插图 strip |
| **草稿自动保存** | 每 30s 定时 + 内容变更时写入 localStorage（key `article_draft`），含保存时间显示 |
| **预览** | 工具栏"预览"按钮切换，markdown-it + DOMPurify 渲染 |
| **引用类型** | `ArticlePublish`（来自 `types/article.ts`） |

#### `ArticlePopup.vue`
| 属性 | 说明 |
|---|---|
| **用途** | 首页弹出面板，快速浏览文章列表（4 列网格） |
| **Props** | 无（内部调用 `useArticleList(page=1, size=8)`） |
| **展示** | 标题行 + "查看更多"链接到 `/articles` + 4 列文章卡片 |
| **调用 API** | `GET /api/v1/article/` |

### 3.4 评论相关（components/comment/）

#### `CommentList.vue`
| 属性 | 说明 |
|---|---|
| **用途** | 评论区（复用支持游戏和文章双类型）：显示评论列表 + 发表新评论 + 行内编辑/删除自己评论 |
| **Props** | `gameId: number`、`type?: string`（默认 `'galgame'`，传 `'article'` 时为文章评论） |
| **类型区分** | 评论使用多态 `receive_type`：`type='article'` → `receive_type=0`（`ReceiveEnum.article`）；`type='galgame'` → `receive_type=1`（`ReceiveEnum.galgame`） |
| **状态** | 加载骨架屏、加载失败使用 `/status/1.png` 插图、空评论使用 `/status/2.png` 插图 |
| **发表** | 最多 2000 字符，实时字数统计；未登录跳转到登录页 |
| **编辑/删除** | 仅作者可见（`isOwnComment` 按用户名匹配）；编辑为行内 textarea |
| **SSR 兼容** | 作者操作按钮通过 `isMounted` 门控，SSR 首帧不显示编辑/删除按钮 |
| **调用 API** | `GET /api/v1/comment/{target_id}?type=galgame|article`（列表）、`POST /api/v1/comment/add`（发表）、`PUT /api/v1/comment/edit`（编辑）、`DELETE /api/v1/comment/delete`（删除） |
| **引用类型** | `CommentItems` |

### 3.5 链接相关（components/link/）

#### `LinkList.vue`
| 属性 | 说明 |
|---|---|
| **用途** | 游戏详情页资源链接展示列表 |
| **Props** | `gameId: number` |
| **状态** | 加载骨架屏、加载失败错误提示、空链接显示"暂无下载链接" |
| **安全** | URL 通过 `isSafeLink()` 白名单校验（http/https/magnet/ed2k/ftp/thunder/bt），不安全链接仅展示文本 |
| **展开** | `defineExpose({ refresh })` 供父组件调用刷新 |
| **标签** | 显示链接分类（el-tag）和大小（formatLinkSize 格式化） |
| **调用 API** | `GET /api/v1/link/{game_id}` |

#### `LinkAddDialog.vue`
| 属性 | 说明 |
|---|---|
| **用途** | 添加游戏链接弹窗，在详情页资源链接区打开 |
| **Props** | `gameId: number` |
| **v-model** | `visible: boolean` 控制弹窗显示 |
| **表单** | URL（必填, 协议白名单校验）、分类、大小（el-input-number + 单位选择器）、备注、提取码 |
| **事件** | `@success` 添加成功后通知父组件刷新列表 |
| **调用 API** | `POST /api/v1/link/add` |
| **引用类型** | `AddLink`、`SizeUnit` |

#### `LinkManage.vue`
| 属性 | 说明 |
|---|---|
| **用途** | 游戏管理页的完整链接管理（列表展示 + 添加 + 行内编辑） |
| **Props** | `gameId: number` |
| **三区布局** | 现有链接列表 → 添加新链接表单 → 编辑链接表单 |
| **编辑流程** | 点击列表中某链接的"编辑"按钮回填到下方编辑表单 → 修改后点击"保存修改" |
| **旧数据兼容** | `bytesToSizeUnit()` 自动将旧数据字节值换算为合适单位（GB/MB/KB） |
| **调用 API** | `GET /api/v1/link/{game_id}`（列表）、`POST /api/v1/link/add`（添加）、`PUT /api/v1/link/review`（编辑）、`DELETE /api/v1/link/delete`（删除） |

### 3.6 管理组件（components/manage/）

这三个组件被 `/user/profile` 和 `/manage` 页面共享复用。

#### `MyGames.vue`
| 属性 | 说明 |
|---|---|
| **用途** | 当前用户发布的游戏列表（分页），含编辑/删除操作 |
| **查询参数** | `author_id` 使用当前登录用户 ID（来自 `authStore.userId`） |
| **SSR** | `server: false`（依赖客户端 localStorage 恢复的 userId） |
| **调用 API** | `GET /api/v1/galgame/?author_id=...`（列表）、`DELETE /api/v1/galgame/delete`（删除） |

#### `MyArticles.vue`
| 属性 | 说明 |
|---|---|
| **用途** | 当前用户发布的文章列表（分页，小型卡片网格），含编辑/删除操作 |
| **布局** | `auto-fill, minmax(150px, 1fr)` 网格，2:3 封面比例 + 居中名称 + 编辑/删除按钮 |
| **SSR** | `server: false`（依赖客户端 localStorage 恢复的 userId）|
| **空状态** | 使用 `el-empty` |
| **调用 API** | `GET /api/v1/article/manage`（列表）、`DELETE /api/v1/article/delete`（删除） |

#### `MyComments.vue`
| 属性 | 说明 |
|---|---|
| **用途** | 当前用户发表的评论列表（分页），含编辑/删除操作 |
| **编辑** | 弹窗编辑评论文本 |
| **跳转** | 每条评论显示所属游戏 `receive_id` 链接 |
| **调用 API** | `GET /api/v1/comment/user/{user_id}`（列表）、`PUT /api/v1/comment/edit`（编辑）、`DELETE /api/v1/comment/delete`（删除） |

#### `MyLinks.vue`
| 属性 | 说明 |
|---|---|
| **用途** | 当前用户发布的链接列表（分页），含编辑/删除操作 |
| **编辑** | 弹窗编辑链接分类/大小/备注/提取码 |
| **跳转** | 每条链接显示所属游戏 `game_id` 链接 |
| **旧数据兼容** | 同 `LinkManage.vue` 的 `bytesToSizeUnit()` 兼容 |
| **调用 API** | `GET /api/v1/link/user/{user_id}`（列表）、`PUT /api/v1/link/review`（编辑）、`DELETE /api/v1/link/delete`（删除） |

---

## 4. 布局（layouts/）

### `default.vue` —— 默认布局

| 区域 | 说明 |
|---|---|
| **固定顶栏** | 粘性定位（`position: sticky; z-index: 100`），半透明毛玻璃背景（`backdrop-filter: blur(12px)`，透明度由 `--fish-alpha` 控制） |
| **品牌标识** | 左侧 favicon 图片 + "和泉的小站" 文字，链接到首页 |
| **导航链接** | 首页 / 全部游戏 / 随机游戏（新） / 发布游戏（登录后显示）/ 登录注册（未登录显示），支持 `exact-active-class` 激活态 |
| **搜索框** | 圆形图标按钮 → 点击展开悬浮搜索面板（`search-flyout`），支持关键词 + 搜索类型选择，回车跳转 `/games?keyword=...` |
| **设置面板** | 齿轮图标按钮 → 弹出居中 `el-dialog`（左右结构），含外观 Tab（主题切换/亮度增强开关/透明度滑块/阴影强度滑块）与背景 Tab（`public/background/` 图片网格选择器） |
| **随机游戏** | 导航栏"随机"链接 + 移动端抽屉，调用 `GET /api/v1/galgame/rvisit` 跳转随机公开游戏详情页 |
| **深色模式切换** | 导航栏保留快捷太阳/月亮图标按钮；设置面板内也有主题切换按钮（`theme-switch-btn`） |
| **用户菜单** | 登录后显示头像+用户名链接到 `/user/profile`；未登录显示`"登录"`按钮 |
| **移动端汉堡** | 1024px 以下隐藏导航链接，显示汉堡按钮，展开抽屉侧边栏 |
| **主内容区** | `<slot />` 插槽 + `<main class="content">` 约束最大宽度 1320px |
| **页脚** | 底部"和泉的小站 · 美少女游戏信息站" |

#### 设置面板详解

外观 Tab（`activeMenu === 'appearance'`）：
- **主题模式**：按钮式切换（`theme-switch-btn`），图标 + 文字，调用 `useColorMode().toggle()`
- **亮度增强**：`el-switch` 开关，开启时 `brightness=150` 关闭时 `100`，通过 `--fish-brightness` CSS 变量作用到 `<html>` 的 `filter`
- **透明度**：`el-slider` 0–100%，通过 `--fish-alpha` CSS 变量作用于顶栏背景
- **阴影强度**：`el-slider` 0–200%，通过 `--fish-shadow-intensity` CSS 变量实时重算 `--fish-shadow` 系列变量

背景 Tab（`activeMenu === 'background'`）：
- 使用 `import.meta.glob` 静态发现 `public/background/*.{jpg,jpeg,png,webp,avif}`
- 网格展示缩略图（3 列，16:10 比例），点击选中的图片设置到 `--fish-bg-image` CSS 变量
- `selectBg(null)` 清除背景（显示"无"占位块）
- 选择持久化到 localStorage（key `theme-bg`）

**CSS 变量系统**：
```css
--fish-brightness: 1;        /* brightness 开关，html 的 filter */
--fish-alpha: 0.3;           /* 顶栏背景透明度 */
--fish-shadow-intensity: 1;  /* 阴影强度系数 */
--fish-bg-image: none;       /* 背景图片 URL，应用到 body background */
```

**body 背景样式**（`theme.css`）：
```css
/* 深色模式 */
body {
  background:
    linear-gradient(rgba(11,11,15,0.55), rgba(11,11,15,0.55)),
    var(--fish-bg-image, none) center/cover fixed,
    #0b0b0f;
}
/* 浅色模式 */
html:not(.dark) body {
  background:
    linear-gradient(rgba(246,246,248,0.6), rgba(246,246,248,0.6)),
    var(--fish-bg-image, none) center/cover fixed,
    #f6f6f8;
}
```

#### 随机游戏实现

```typescript
async function goRandomGame() {
  const res = await api<{ msg: string; id: number | null }>('/api/v1/galgame/rvisit')
  if (res.id != null) navigateTo(`/galgame/${res.id}`)
  else ElMessage.info('暂无公开游戏')
}
```

#### 设置持久化
```typescript
// 从 localStorage 读取（onMounted 时恢复）
const sb = localStorage.getItem('theme-brightness')
const sa = localStorage.getItem('theme-alpha')
const ss = localStorage.getItem('theme-shadow')
const sbg = localStorage.getItem('theme-bg')
// 值变更时写入 localStorage
localStorage.setItem('theme-brightness', String(brightness.value))

#### SSR 兼容策略

| 问题 | 解决方案 |
|---|---|
| 水合不一致 | 使用 `isMounted` 门控：未挂载前统一渲染"未登录"态（无头像、显示"登录"按钮），挂载后根据 `auth.token` 切换 |
| 搜索框回车 | `handleSearch()` 跳转到 `/games?keyword=...` |
| 移动端抽屉 | `isNavOpen` 控制蒙层 + 侧栏，点击蒙层或链接关闭 |

---

## 5. 组合函数（composables/）

### 5.1 `useGalgame.ts`

| 函数 | 说明 | API 端点 |
|---|---|---|
| `useGalgameList(query, options?)` | 游戏列表（SSR 友好，`useAsyncData`），query 变化自动重拉 | `GET /api/v1/galgame/` |
| `useGalgameDetail(id)` | 游戏详情（SSR 缓存），带 `watch: [id]` | `GET /api/v1/galgame/{id}` |
| `addGalgame(payload)` | 发布游戏（需登录） | `POST /api/v1/galgame/add` |
| `editGalgame(id, payload)` | 编辑游戏（仅作者） | `PUT /api/v1/galgame/edit?id=...` |
| `deleteGalgame(id)` | 删除游戏（仅作者） | `DELETE /api/v1/galgame/delete?id=...` |

### 5.2 `useComment.ts`

| 函数 | 说明 | API 端点 |
|---|---|---|
| `useCommentList(targetId, page?, size?, type?)` | 评论列表（SSR 友好），`type` 支持 `'galgame'`（默认）`\| 'article'` | `GET /api/v1/comment/{target_id}?type=...` |
| `useUserCommentList(query, options?)` | 用户自己的评论列表（仅客户端） | `GET /api/v1/comment/user/{user_id}` |
| `addComment(targetId, content, type?)` | 发表评论（需登录），`type` 决定 `receive_type` | `POST /api/v1/comment/add?game_id=...&type=...` |
| `editComment(commentId, content)` | 编辑评论（仅作者） | `PUT /api/v1/comment/edit?comment_id=...` |
| `deleteComment(commentId)` | 删除评论（仅作者） | `DELETE /api/v1/comment/delete?comment_id=...` |

### 5.3 `useLink.ts`

| 函数 | 说明 | API 端点 |
|---|---|---|
| `useLinkList(gameId, page?, size?)` | 游戏链接列表（SSR 友好） | `GET /api/v1/link/{game_id}` |
| `useUserLinkList(query, options?)` | 用户自己的链接列表（仅客户端） | `GET /api/v1/link/user/{user_id}` |
| `addLink(gameId, payload)` | 添加链接（需登录） | `POST /api/v1/link/add?game_id=...` |
| `reviewLink(linkId, payload)` | 编辑链接（仅作者） | `PUT /api/v1/link/review?link_id=...` |
| `deleteLink(linkId)` | 删除链接（仅作者） | `DELETE /api/v1/link/delete?link_id=...` |

### 5.4 `useAuth.ts`

| 函数 | 说明 | API 端点 |
|---|---|---|
| `useEmail().sendCode(email)` | 发送邮箱验证码 | `POST /api/v1/email/send?email=...` |
| `login(username, password)` | 登录，成功后调用 `authStore.setAuth()` 持久化 | `POST /api/v1/user/login` |
| `register(payload, code)` | 注册（需验证码） | `POST /api/v1/user/register?code=...` |
| `fetchProfile(id?)` | 获取用户信息；不传 id 用 token 定位自身 | `GET /api/v1/user/` |
| `updateProfile(payload)` | 更新个人资料 | `PUT /api/v1/user/update` |
| `deleteAccount()` | 删除账号（自动登出） | `DELETE /api/v1/user/delete` |
| `logout(redirect?)` | 调用 `authStore.logout()` 清理状态 | — |

### 5.5 `useFavorite.ts`

| 函数 | 说明 | API 端点 |
|---|---|---|
| `addFavorite(galId)` | 收藏游戏 | `POST /api/v1/favorite/add?gal_id=...` |
| `removeFavorite(galId)` | 取消收藏 | `DELETE /api/v1/favorite/remove?gal_id=...` |
| `useFavoriteList(query)` | 收藏列表（仅客户端，需登录态） | `GET /api/v1/favorite/list` |

### 5.6 `useArticle.ts`

| 函数 | 说明 | API 端点 |
|---|---|---|
| `useArticleList(page, size?, category?)` | 公开文章列表（SSR 友好，`useAsyncData`），page/size/category 变化自动重拉 | `GET /api/v1/article/` |
| `useArticleDetail(id)` | 文章详情（SSR 缓存），带 `watch: [id]` | `GET /api/v1/article/{id}` |
| `useArticleManage(page, size?)` | 个人文章管理列表（仅客户端，`server: false`） | `GET /api/v1/article/manage` |
| `publishArticle(data)` | 发布文章（需登录） | `POST /api/v1/article/add` |
| `editArticle(id, data)` | 编辑文章（仅作者） | `PUT /api/v1/article/edit?id=...` |
| `deleteArticle(id)` | 删除文章（仅作者） | `DELETE /api/v1/article/delete?id=...` |

### 5.7 `useColorMode.ts`

| 函数 | 说明 |
|---|---|
| `isDark` | 响应式 ref，始终为 `true`（项目仅保留深色模式） |
| `setMode(dark)` | 始终设置 `<html>` 的 `dark` class（无浅色模式） |
| `toggle()` | 无操作（已移除模式切换功能） |
| **SSR 策略** | nuxt.config.ts 中 `<script>` 在 paint 前默认加 dark class |

---

## 6. 类型定义（types/）

### 文件结构

```
types/
├── index.ts      # 统一导出：export * from './user' / galgame / link / comment
├── user.ts       # 用户模块
├── galgame.ts    # galgame 模块（含枚举常量和收藏类型）
├── link.ts       # 链接模块
└── comment.ts    # 评论模块
```

### 6.1 `types/user.ts`

| 类型/接口 | 说明 | 对齐后端 |
|---|---|---|
| `LoginRequest` | 登录请求体（username, password） | `schemas/user.py LoginRequest` |
| `LoginResponse` | 登录响应（msg, id, username, is_admin, access_token） | `schemas/user.py LoginResponse` |
| `RegisterRequest` | 注册请求体（username, password, email, avatar?, bio?） | `schemas/user.py RegisterRequest` |
| `RegisterResponse` | 注册响应（msg, id, username, email, bio, avatar） | `schemas/user.py RegisterResponse` |
| `UserProfile` | 用户详情响应（msg, username, avatar, bio, email） | `schemas/user.py UserInfo` |
| `AccountUpdate` | 更新用户信息请求体（全部可选） | `schemas/user.py AccountUpdate` |

### 6.2 `types/galgame.ts`

| 类型/接口 | 说明 |
|---|---|
| `PlatformValue` | 平台枚举：`'电脑端' \| '安卓端' \| 'Other'`（中文值传输） |
| `PLATFORM_OPTIONS` | 平台选项数组（含 label/value） |
| `CategoryValue` | 作品分类枚举：10 种中文值（剧情向/治愈系/日常系/恋爱模拟/文字冒险/RPG/经营模拟/拔作/全年龄/其他） |
| `CATEGORY_OPTIONS` | 分类选项数组（含 label/value） |
| `GalItem` | 游戏列表项（id, name, cover, views, author, avatar, author_id?） |
| `GalList` | 游戏列表响应（total, items） |
| `GalgameListQuery` | 列表查询参数（category?, platform?, author_id?, keyword?, sort?, searchType?, page?, size?） |
| `GalgameDetail` | 游戏详情响应（完整的 20+ 字段） |
| `AddGal` | 发布游戏请求体 | 
| `EditGal` | 编辑游戏请求体（全部可选） |
| `FavoriteItem` | 收藏列表项（id, name, cover） |
| `FavoriteList` | 收藏列表响应（total, items） |

### 6.3 `types/link.ts`

| 类型/接口 | 说明 |
|---|---|
| `SizeUnit` | 大小单位：`'KB' \| 'MB' \| 'GB'` |
| `LinkItem` | 链接列表项（id, url, content?, code?, category?, size?, size_unit?, status, game_id） |
| `LinkItems` | 链接包装项（item + account: {username, avatar}） |
| `LinkList` | 链接列表响应（total, items） |
| `AddLink` | 添加链接请求体 |
| `EditLink` | 编辑链接请求体（全部可选） |

### 6.4 `types/comment.ts`

| 类型/接口 | 说明 |
|---|---|
| `CommentItem` | 评论项（id, content?, receive_id） |
| `CommentItems` | 评论包装项（item + account: {username, avatar}） |
| `CommentList` | 评论列表响应（total, items） |
| `AddComment` | 发表评论请求体 |
| `EditComment` | 编辑评论请求体 |

---

## 7. 工具函数（utils/）

### `utils/request.ts`

| 函数 | 说明 |
|---|---|
| `cleanParams(params)` | 清除查询参数中的 undefined / null / '' / 空数组，避免后端 422 或误匹配 |
| `api(request, opts)` | 统一请求封装：惰性创建 `$fetch` 实例，自动附带 `Authorization: Bearer <token>`、401 时自动清理登录态并跳转登录页（登录接口自身的 401 除外） |
| `getErrDetail(e, fallback?)` | 从异常中提取可读错误信息：Pydantic 422 数组 detail 归一为字符串拼接 |

### `utils/file.ts`

| 函数 | 说明 |
|---|---|
| `fileToBase64(file)` | File 对象 → base64 data URL |
| `readImageAsBase64(file, maxBytes?)` | 读取图片并校验大小（与后端单图 ≤5MB 对齐），超限 reject 中文错误提示 |
| `MAX_IMAGE_BYTES` | 5MB 常量，与后端 `utils/webp.py` 保持一致 |

### `utils/link.ts`

| 函数 | 说明 |
|---|---|
| `isSafeLink(url)` | URL 协议白名单校验（https/http/magnet/ed2k/ftp/thunder/bt），防止 `javascript:` 等可执行协议 XSS |

### `utils/color.ts`

| 函数 | 说明 |
|---|---|
| `extractCoverAccent(src)` | 从封面图提取平均主色（Canvas 32px 采样），过暗时向紫蓝品牌色提亮；仅客户端执行，失败返回 null |

### `utils/format.ts`

| 函数 | 说明 |
|---|---|
| `formatLinkSize(size, sizeUnit?)` | 格式化链接大小展示（新数据直接拼接、旧数据字节 fallback） |
| `formatBytes(bytes)` | 字节数 → 可读文本（<1MB 显示 KB，≥1MB 显示 MB） |
| `bytesToSizeUnit(bytes)` | 旧数据字节 → { size, size_unit } 用于编辑表单回显 |

---

## 8. 插件（plugins/）

### `plugins/auth.client.ts`

| 属性 | 说明 |
|---|---|
| **类型** | 客户端插件（`.client` 后缀，仅浏览器执行） |
| **用途** | Nuxt 应用启动时从 localStorage 恢复登录态 |
| **实现** | 调用 `useAuthStore().initFromStorage()`，读取 `fishmo_token` / `fishmo_username` / `fishmo_user_id` / `fishmo_avatar` / `gal_is_admin` 五个 key |
| **时机** | 早于任何页面渲染，确保页面加载时 store 已初始化 |

### `plugins/element-plus.ts`

| 属性 | 说明 |
|---|---|
| **类型** | Nuxt 插件（服务端 + 客户端） |
| **用途** | Element Plus 全局注册 + 中文语言包 + 图标库全量注册 + SSR 兼容注入 |
| **图标注册** | 遍历 `@element-plus/icons-vue` 全部组件并全局注册（模板中可直接使用 `<el-icon><View /></el-icon>` 等） |
| **SSR 兼容** | 注入 `ID_INJECTION_KEY` 和 `ZINDEX_INJECTION_KEY` provider，避免服务端渲染警告与降级 |

---

## 9. 样式主题（assets/css/theme.css）

### 设计系统令牌

`fishmo` 项目遵循《fishmo 视觉定位》Dark 深色游戏门户设计系统。

| 名称 | 深色值 | 浅色值 | 说明 |
|---|---|---|---|
| `--fish-accent` | `#8f8ef5` | `#7c7bf2` | 柔和紫蓝品牌主色 |
| `--fish-accent-strong` | `#a6a5f7` | `#6a69e6` | hover/按下 |
| `--fish-accent-soft` | `rgba(143,142,245,0.14)` | `rgba(124,123,242,0.14)` | 半透明背景 |
| `--fish-bg` | `#0b0b0f` | `#f6f6f8` | 页面背景 |
| `--fish-bg-2` | `#111116` | `#ffffff` | 卡片/表单背景 |
| `--fish-text-1` | `rgba(255,255,255,0.92)` | `#18181b` | 主文字 |
| `--fish-radius` | `12px` | `12px` | 基础圆角 |
| `--fish-shadow` | 深色阴影 | 浅色阴影 | 克制阴影 |

### 用户可调 CSS 变量（设置面板控制）

| 名称 | 默认值 | 说明 | 控制方式 |
|---|---|---|---|
| `--fish-brightness` | `1` | 页面亮度，作用到 `<html>` 的 `filter` | 亮度增强开关（1 或 1.5） |
| `--fish-alpha` | `0.3` | 顶栏背景透明度 | 透明度滑块 0–100% |
| `--fish-shadow-intensity` | `1` | 阴影强度系数 | 阴影滑块 0–200%，运行时重算 `--fish-shadow` |
| `--fish-bg-image` | `none` | 背景图片 URL | 背景选择网格，持久化 localStorage |

### Element Plus 变量覆盖

完整覆盖了 `--el-color-*`、`--el-bg-color-*`、`--el-text-color-*`、`--el-border-color-*`、`--el-fill-color-*`、`--el-border-radius-base` 等系列变量，使 Element Plus 组件与设计系统统一。

### 全局样式

- 页面切换过渡仅淡入淡出 200ms（`page-fade`），无位移
- 自定义滚动条配色（紫蓝调）
- 选区配色（紫蓝半透明）
- 过渡曲线统一使用 `cubic-bezier(0.16, 1, 0.3, 1)`
- `prefers-reduced-motion: reduce` 支持

---

## 10. 配置详解（nuxt.config.ts）

| 配置项 | 值 | 说明 |
|---|---|---|
| `components` | `[{ path: '~/components', pathPrefix: false }]` | 禁用目录前缀，组件名直接使用文件名 |
| `modules` | `['@pinia/nuxt']` | Pinia 状态管理 |
| `css` | 先 EP 默认样式 → 再 EP 深色 css-vars → 最后自定义 theme.css | 覆盖优先级 |
| `runtimeConfig.public.apiBase` | `NUXT_PUBLIC_API_BASE \|\| ''` | API 基础路径，默认同源 |
| `routeRules['/api/**']` | 代理到 `NUXT_API_BASE \|\| 'http://localhost:8000'` | 开发与生产均通过 Nitro 代理转发，规避 CORS |
| `typescript.strict` | `true` | 严格模式 |
| `typescript.typeCheck` | `true` | 构建时 `vue-tsc` 类型检查 |
| `app.pageTransition` | `{ name: 'page-fade', mode: 'out-in' }` | 页面切换淡入淡出 |
| `app.head.script` | 内联脚本 paint 前默认加 dark class | 防止深色模式闪烁 |
| `app.head.link` | Google Fonts（Inter / Noto Sans SC / Noto Sans JP） | 运行时加载 |

---

## 11. API 请求与代理机制

```
浏览器                    Nuxt Nitro                     FastAPI 后端
 ┌───┐                   ┌────────┐                     ┌───────────┐
 │   │  /api/v1/galgame/  │        │  proxy to           │           │
 │   │ ──────────────────►│        │ ──────────────────► │ :8000/api │
 │   │                    │ route  │                     │           │
 │   │ ◄───────────────── │ rules  │ ◄────────────────── │           │
 │   │                    │        │                     │           │
 └───┘                   └────────┘                     └───────────┘
```

- `baseURL` 默认为空字符串，请求路径如 `/api/v1/galgame/` 发到 Nuxt 自身
- Nuxt Nitro 通过 `routeRules` 将 `/api/**` 代理转发到 FastAPI 后端（默认 `http://localhost:8000`）
- 此机制完全规避浏览器跨域 CORS 问题
- 401 响应时自动清理登录态并跳转登录页（登录接口自身的 401 除外）

---

## 12. SSR 适配策略汇总

| 场景 | 策略 | 涉及文件 |
|---|---|---|
| 登录态恢复 | `.client` 插件从 localStorage 恢复 | `plugins/auth.client.ts` |
| 导航栏登录态 | `isMounted` 布尔门控，挂载前统一"未登录" | `layouts/default.vue` |
| 详情页作者操作 | `showOwnerActions` 通过 `isMounted` 门控 | `pages/galgame/[id].vue` |
| 管理页作者校验 | 整块作者区域等 `onMounted` 后再渲染 | `pages/manage/[id].vue` |
| 评论作者操作 | `isMounted` 控制编辑/删除按钮显示 | `components/comment/CommentList.vue` |
| 深色模式 | 内联脚本 paint 前加 dark class → 客户端 `onMounted` 同步 | `nuxt.config.ts` script + `composables/useColorMode.ts` |
| 封面主色提取 | 仅在客户端 `onMounted` 执行 Canvas 采样 | `pages/galgame/[id].vue` |
| 用户管理列表 | `server: false` 避免 SSR 阶段无 userId 拉取全量数据 | `components/manage/MyGames.vue`、`MyComments.vue`、`MyLinks.vue`、`composables/useComment.ts`、`composables/useLink.ts` |
| 收藏列表 | `server: false`（需登录态） | `composables/useFavorite.ts` |
| Element Plus SSR | 注入 `ID_INJECTION_KEY` / `ZINDEX_INJECTION_KEY` provider | `plugins/element-plus.ts` |

---

## 13. 组件复用关系图

```
layouts/default.vue
├── pages/index.vue ────────────────────── GameCard
├── pages/games/index.vue ──────────────── GameCard
├── pages/galgame/[id].vue ──────┬──────── LinkList
│                                ├──────── LinkAddDialog
│                                └──────── CommentList
├── pages/user/index.vue ────────┬──────── LoginForm
│                                └──────── RegisterForm
├── pages/user/profile.vue ──────┬──────── MyGames
│                                ├──────── MyComments
│                                ├──────── MyLinks
│                                ├──────── MyFavorites
│                                └──────── ProfileForm
├── pages/publish/index.vue ────────────── GalgameForm(mode="add")
├── pages/manage/index.vue ──────┬──────── MyGames
│                                ├──────── MyComments
│                                └──────── MyLinks
├── pages/manage/[id].vue ───────┬──────── GalgameForm(mode="edit")
│                                └──────── LinkManage
└── pages/admin/index.vue ─────────────── [直接调用 API]
```

---

## 15. 新增功能一览（2026-09-19）

### 设置面板与背景系统

- **设置面板**：顶栏齿轮图标 → 居中弹出 `el-dialog`（左右结构），外观 Tab（主题切换/亮度增强/透明度/阴影强度）+ 背景 Tab（`public/background/` 图片网格选择）
- **CSS 变量**：`--fish-brightness`（亮度，html filter）、`--fish-alpha`（顶栏透明度）、`--fish-shadow-intensity`（阴影强度系数）、`--fish-bg-image`（背景图片 URL）
- **持久化**：所有设置保存到 localStorage，`onMounted` 时恢复

### 随机游戏

- 导航栏和移动端抽屉新增"随机"入口
- 调用 `GET /api/v1/galgame/rvisit` 获取随机公开游戏 id

### 卡片背景透明化

- GameCard、个人主页卡片、管理页面卡片均设为透明背景
- Games 页标签也透明，露出 body 背景图片

### 状态插图

- 错误/加载失败：统一使用 `/status/1.png`（240px 宽，圆角 12px，opacity 0.85）
- 空数据（无评论/链接/收藏）：使用 `/status/2.png`
- 统一的 `.empty-img` CSS：flex column 居中，240px 图片，12px 圆角

### 精选 Hero 增强

- 底部渐变遮罩 `linear-gradient(to top, rgba(0,0,0,0.85) → transparent)`
- 玻璃拟态标签 `backdrop-filter: blur(8px)` + `rgba(143,142,245,0.15)` 背景
- 深色模式 `box-shadow: 0 0 0 1px rgba(143,142,245,0.08)` 微光边框
- hover 时 `translateY(-3px)` 轻微上浮

### 后端目录重命名

- `backend/app/api/v1/` 整体重命名为 `backend/app/api/service/`
- `main.py` import 同步更新：`from api.v1` → `from api.service`

---

## 16. 附录：文档版本记录

| 日期 | 更新内容 |
| --- | --- |
| 2026-09-19 | 新增设置面板/背景系统/随机游戏/卡片透明化/状态插图/Hero 增强/后端目录重命名 |
| 2026-09-17 | 初始文档编制，基于代码逐文件核对 |

---

## 14. 数据流总结

### 认证流程

```
登录页 (LoginForm)
  → useAuth().login(username, password)
    → POST /api/v1/user/login
    → authStore.setAuth(token, id, username, isAdmin)
      → 写入 Pinia + localStorage（5 个 key）
  → 跳转 redirect 回推或首页

auth.client.ts 插件
  → authStore.initFromStorage()
    → 读取 localStorage 恢复登录态

auth 中间件
  → authStore.token 为空 → 跳转 /user?redirect=...

api() 请求
  → onRequest 自动设置 Authorization: Bearer <token>
  → onResponseError 401 → 清理登录态 → 跳转登录页
```

### 游戏发布流程

```
发布页 (GalgameForm mode="add")
  → 步骤 1：名称/分类/标签/平台
  → 步骤 2：简介
  → 步骤 3：封面上传 (readImageAsBase64 + base64) + 截图上传 + 实时卡片预览
  → 提交: handleSubmit → emit('submit', AddGal)
    → pages/publish: addGalgame(payload)
      → POST /api/v1/galgame/add
        → 后端: status=False（待审核），Redis 版本更新
      → navigateTo(/galgame/${res.id})
```

### 游戏详情展示流程

```
详情页 /galgame/[id]
  → useGalgameDetail(gameId) → GET /api/v1/galgame/{id}
  → 渲染 Hero（封面/标题/元数据）
  → LinkList(gameId) → GET /api/v1/link/{game_id}
  → CommentList(gameId) → GET /api/v1/comment/{game_id}
  → ViewCounter.incr(id) → Redis 浏览量递增（后端视角）
  → onMounted: extractCoverAccent(cover) → 设置 --cover-accent CSS 变量
```

### 管理审核流程

```
管理员登录 → /admin
  → fetchPendingGames()
    → GET /api/admin/control/BrowseGal?page=...&size=...
    → fetchGameDetails(ids) [批量并行]
      → GET /api/v1/galgame/{id} x N
  → 通过: approveGame(id)
    → PUT /api/admin/control/UpdateStatus?gal_id=...&status=true
  → 拒绝: rejectGame(id)
    → PUT /api/admin/control/UpdateStatus?gal_id=...&status=false
  → 删除: deleteGame(id)
    → DELETE /api/admin/control/DeleteGal?gal_id=...
```