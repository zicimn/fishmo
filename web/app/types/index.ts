// 与后端 schemas/ 严格对齐的 TypeScript 类型。
// 枚举在网络上传输中文值（"电脑端"、"剧情向"），这里直接用字符串字面量。

export interface Envelope<T> {
  msg: string
  code: number
  data: T
}

export interface PageData<T> {
  total: number
  items: T[]
}

// ---------------------------------------------------------------------------
// 用户
// ---------------------------------------------------------------------------
export interface AuthUser {
  id: number
  username: string
  email?: string
  avatar?: string | null
  bio?: string | null
  is_admin: boolean
  created_at?: string
}

export interface AuthData {
  access_token: string
  token_type: string
  expires_in: number
  user: AuthUser
}

export interface UserPublic {
  id: number
  username: string
  avatar?: string | null
  bio?: string | null
  gal_cnt: number
  article_cnt: number
  is_self: boolean
  email?: string
  created_at?: string
}

// ---------------------------------------------------------------------------
// Galgame
// ---------------------------------------------------------------------------
export const PLATFORM_OPTIONS = ['电脑端', '安卓端', 'Other'] as const
export type PlatformValue = (typeof PLATFORM_OPTIONS)[number]

export const CATEGORY_OPTIONS = [
  '剧情向',
  '治愈系',
  '日常系',
  '恋爱模拟',
  '文字冒险',
  'RPG',
  '经营模拟',
  '拔作',
  '全年龄',
  '其他',
] as const
export type CategoryValue = (typeof CATEGORY_OPTIONS)[number]

export const SEARCH_OPTIONS = [
  { value: 'name', label: '名称' },
  { value: 'tag', label: '标签' },
  { value: 'company', label: '公司' },
] as const
export type SearchTypeValue = (typeof SEARCH_OPTIONS)[number]['value']

export const ARTICLE_CATEGORY_OPTIONS = ['攻略', '资讯', '公告', '教程', '其他'] as const
export const SIZE_UNIT_OPTIONS = ['KB', 'MB', 'GB'] as const
export type SizeUnitValue = (typeof SIZE_UNIT_OPTIONS)[number]

export interface GalItem {
  id: number
  name: string
  cover: string
  views: number
  category: string | null
  status: boolean
  author_id: number
  author: string
  avatar: string | null
  updated_at: string | null
}

export interface GalDetail {
  id: number
  name: string
  cn_name: string
  jp_name: string
  en_name: string
  content: string | null
  company: string[]
  category: string | null
  cover: string
  images: string[]
  tag: string[]
  views: number
  likes: number
  favorite: number
  is_favorited: boolean
  platfrom: string[]
  status: boolean
  author_id: number
  author_name: string
  author_avatar: string | null
  created_at: string
  updated_at: string
}

export interface GalListQuery {
  page?: number
  size?: number
  category?: string
  platform?: string
  author_id?: number
  keyword?: string
  sort?: 'updated_at' | 'views'
  search_type?: SearchTypeValue
}

export interface AddGalPayload {
  name?: string
  cn_name?: string
  jp_name?: string
  en_name?: string
  content?: string
  company?: string[]
  category?: string
  cover: string
  images?: string[]
  tag?: string[]
  platfrom?: string[]
}

// ---------------------------------------------------------------------------
// 文章
// ---------------------------------------------------------------------------
export interface ArticlePreview {
  id: number
  title: string
  cover: string
  category: string[]
  views: number
  comcnt: number
  created_at: string
  time: string
  author_id: number
  author: string
  avatar: string | null
}

export interface ArticleDetail {
  id: number
  title: string
  content: string
  cover: string
  tag: string[]
  category: string[]
  images: string[]
  views: number
  status: boolean
  author_id: number
  author_name: string
  author_avatar: string | null
  comment_count: number
  created_at: string
  updated_at: string
}

export interface ArticleManageItem {
  id: number
  title: string
  cover: string
  category: string[]
  views: number
  status: boolean
  created_at: string
  updated_at: string
}

export interface ArticlePayload {
  title: string
  content: string
  cover?: string
  tag?: string[]
  category?: string
  images?: string[]
}

// ---------------------------------------------------------------------------
// 评论（2 层嵌套）
// ---------------------------------------------------------------------------
export interface CommentAuthor {
  id: number
  username: string
  avatar: string | null
}

export interface CommentItem {
  id: number
  content: string
  receive_id: number
  receive_type: number
  parent_id: number | null
  reply_to_id: number | null
  reply_to_username: string | null
  author_id: number
  author: CommentAuthor
  created_at: string
  updated_at: string
  replies?: CommentItem[]
  reply_count?: number
}

// ---------------------------------------------------------------------------
// 链接 / 收藏
// ---------------------------------------------------------------------------
export interface LinkItem {
  id: number
  url: string
  content: string | null
  code: string | null
  category: string | null
  size: number | null
  size_unit: SizeUnitValue | null
  status: boolean
  game_id: number
  author_id: number
  author: CommentAuthor
  created_at: string
  updated_at: string
}

export interface LinkPayload {
  url?: string
  content?: string | null
  code?: string | null
  category?: string | null
  size?: number | null
  size_unit?: SizeUnitValue | null
}

export interface FavoriteItem {
  id: number
  name: string
  cover: string
  views: number
  category: string | null
  favorited_at: string
}

export interface FavoriteStatus {
  gal_id: number
  favorited: boolean
  favorite_id: number | null
  count: number
}