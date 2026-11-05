// 管理端接口响应类型：与后端 schemas 对齐。

export interface Envelope<T> {
  msg: string
  code: number
  data: T
}

export interface PageData<T> {
  total: number
  items: T[]
}

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

export interface Stats {
  games: number
  pending_games: number
  users: number
  articles: number
  comments: number
  links: number
  favorites: number
}

export interface AdminGal {
  id: number
  name: string
  cn_name: string
  jp_name: string
  en_name: string
  cover: string
  category: string | null
  views: number
  status: boolean
  author_id: number
  author: string
  avatar: string | null
  created_at: string
  updated_at: string
}

export interface AdminArticle {
  id: number
  title: string
  cover: string
  category: string[]
  views: number
  status: boolean
  author_id: number
  author: string
  avatar: string | null
  created_at: string
  updated_at: string
}

export interface AdminUser {
  id: number
  username: string
  email: string
  avatar: string | null
  bio: string | null
  status: number
  is_admin: boolean
  gal_cnt: number
  article_cnt: number
  created_at: string
}