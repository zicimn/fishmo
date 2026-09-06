// ===== link 模块类型（与 backend schemas/link.py 对齐）=====

export interface LinkItem {
  id: number
  url: string
  content: string | null
  code: string | null
  category: string | null
  /** 链接大小（字节），与后端 schemas/link.py 一致。前端展示/输入以 MB 为单位，提交前需 *1024*1024 换算。 */
  size: number | null
  status: boolean
  /** 所属游戏 id：按用户过滤的链接列表据此跳转对应游戏/管理页 */
  game_id: number
}

export interface LinkItems {
  item: LinkItem
  account: {
    username: string
    avatar: string | null
  }
}

/** GET /api/v1/link/{game_id} 列表响应 */
export interface LinkList {
  total: number
  items: LinkItems[]
}

/** POST /api/v1/link/add 请求体 */
export interface AddLink {
  url: string
  content?: string | null
  code?: string | null
  category?: string | null
  size?: number | null
}

/** PUT /api/v1/link/review 请求体（全部可选） */
export interface EditLink {
  content?: string | null
  code?: string | null
  category?: string | null
  size?: number | null
}
