// ===== galgame 模块类型（与 backend schemas/galgame.py / model/enums.py 对齐）=====

/**
 * 平台枚举：后端 model/enums.py 的 PlatformEnum(str, PyEnum)
 * 接口实际传输的是中文值（"电脑端"/"安卓端"/"Other"）。
 * 注意：后端字段拼写为 platfrom，非 platform，勿改动。
 */
export type PlatformValue = '电脑端' | '安卓端' | 'Other'

export const PLATFORM_OPTIONS: { label: string; value: PlatformValue }[] = [
  { label: '电脑端', value: '电脑端' },
  { label: '安卓端', value: '安卓端' },
  { label: 'Other', value: 'Other' },
]

/**
 * 作品（分类）枚举：后端 model/enums.py 的 CategoryEnum(str, PyEnum)
 * 接口实际传输的是中文值（"剧情向"/"治愈系"…）。
 */
export type CategoryValue =
  | '剧情向'
  | '治愈系'
  | '日常系'
  | '恋爱模拟'
  | '文字冒险'
  | 'RPG'
  | '经营模拟'
  | '拔作'
  | '全年龄'
  | '其他'

export const CATEGORY_OPTIONS: { label: string; value: CategoryValue }[] = [
  { label: '剧情向', value: '剧情向' },
  { label: '治愈系', value: '治愈系' },
  { label: '日常系', value: '日常系' },
  { label: '恋爱模拟', value: '恋爱模拟' },
  { label: '文字冒险', value: '文字冒险' },
  { label: 'RPG', value: 'RPG' },
  { label: '经营模拟', value: '经营模拟' },
  { label: '拔作', value: '拔作' },
  { label: '全年龄', value: '全年龄' },
  { label: '其他', value: '其他' },
]

/** GET /api/v1/galgame/ 列表项（后端已返回游戏 id，可直接用于跳转/管理） */
export interface GalItem {
  id: number
  name: string
  cover: string
  views: number
  author: string
  avatar: string | null
  /** 作者 id：按作者过滤列表后，前端直接用于作者校验/管理入口判断 */
  author_id?: number | null
}

/** GET /api/v1/galgame/ 列表响应 */
export interface GalList {
  total: number
  items: GalItem[]
}

/** GET /api/v1/galgame/ 查询参数 */
export interface GalgameListQuery {
  category?: string
  platform?: string
  /** 按作者 id 过滤（我的游戏 / 个人主页列表） */
  author_id?: number
  page?: number
  size?: number
}

/** GET /api/v1/galgame/{id} 详情响应 */
export interface GalgameDetail {
  msg: string
  id: number
  cn_name: string
  jp_name: string
  en_name: string
  author_id: number
  name: string
  content: string | null
  company: string[] | null
  category: string | null
  cover: string
  images: string[] | null
  tag: string[] | null
  views: number
  likes: number
  favorite: number
  platfrom: string[] | null
  update_at: string
  author_name: string
  author_avatar: string | null
}

/** POST /api/v1/galgame/add 请求体（cover 必填，三名称至少一个非空） */
export interface AddGal {
  cn_name: string | null
  jp_name: string | null
  en_name: string | null
  content?: string | null
  company?: string[] | null
  category?: CategoryValue | null
  cover: string
  images?: string[] | null
  tag?: string[] | null
  platfrom?: PlatformValue[] | null
}

/** PUT /api/v1/galgame/edit 请求体（全部可选） */
export interface EditGal {
  cn_name?: string | null
  jp_name?: string | null
  en_name?: string | null
  content?: string | null
  company?: string[] | null
  category?: CategoryValue | null
  cover?: string | null
  images?: string[] | null
  tag?: string[] | null
  platfrom?: PlatformValue[] | null
}
