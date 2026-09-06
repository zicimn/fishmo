// ===== 用户模块类型（与 backend schemas/user.py 对齐）=====

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponse {
  msg: string
  id: number
  username: string
  access_token: string
}

export interface RegisterRequest {
  username: string
  password: string
  email: string
  avatar?: string | null
  bio?: string | null
}

export interface RegisterResponse {
  msg: string
  id: number
  username: string
  email: string
  bio: string | null
  avatar: string | null
}

/** GET /api/v1/user/ 响应（UserInfo 基础上带 msg） */
export interface UserProfile {
  msg: string
  username: string
  avatar: string | null
  bio: string | null
  email: string
}

/** PUT /api/v1/user/update 请求体（全部可选） */
export interface AccountUpdate {
  username?: string
  password?: string
  email?: string
  avatar?: string | null
  bio?: string | null
}
