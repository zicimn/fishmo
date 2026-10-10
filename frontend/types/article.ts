// ===== article 模块类型（与 backend schemas/article.py 对齐）=====

/** 公开文章列表项 */
export interface ArticleItem {
  id: number
  title: string
  cover: string
  comcnt: number
  views: number
  time: string
  category?: string
}

/** 公开文章列表响应 */
export interface ArticleList {
  total: number
  items: ArticleItem[]
}

/** 发布/编辑文章请求体 */
export interface ArticlePublish {
  title: string
  content: string
  cover?: string
  tag?: string[]
  category: string[]
  images?: string[]
}

/** 文章详情响应 */
export interface ArticleDetail {
  id: number
  title: string
  content: string
  cover?: string
  tag?: string[]
  category: string[]
  images?: string[]
  views: number
  author_id: number
  author_name: string
  author_avatar?: string
  comment_count: number
  created_at: string
  updated_at: string
}

/** 个人文章管理列表项 */
export interface ArticleManageItem {
  id: number
  title: string
  cover: string
}

/** 个人文章管理列表响应 */
export interface ArticleManageList {
  total: number
  items: ArticleManageItem[]
}