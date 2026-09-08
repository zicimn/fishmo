// ===== link 模块类型（与 backend schemas/link.py 对齐）=====

/** 链接文件大小单位枚举（与后端 SizeUnitEnum 对齐） */
export type SizeUnit = 'KB' | 'MB' | 'GB'

export interface LinkItem {
  id: number
  url: string
  content: string | null
  code: string | null
  category: string | null
  /** 链接大小数值（浮点），配合 size_unit 使用；旧数据 size_unit 为 null 时按字节处理 */
  size: number | null
  /** 大小单位：KB / MB / GB，旧数据可能为 null */
  size_unit: SizeUnit | null
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
  size_unit?: SizeUnit | null
}

/** PUT /api/v1/link/review 请求体（全部可选） */
export interface EditLink {
  content?: string | null
  code?: string | null
  category?: string | null
  size?: number | null
  size_unit?: SizeUnit | null
}
