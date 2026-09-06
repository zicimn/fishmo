// ===== comment 模块类型（与 backend schemas/comment.py 对齐）=====

export interface CommentItem {
  id: number
  content: string | null
  receive_id: number
}

export interface CommentItems {
  item: CommentItem
  account: {
    username: string
    avatar: string | null
  }
}

/** GET /api/v1/comment/{game_id} 列表响应 */
export interface CommentList {
  total: number
  items: CommentItems[]
}

/** POST /api/v1/comment/add 请求体 */
export interface AddComment {
  content: string
}

/** PUT /api/v1/comment/edit 请求体 */
export interface EditComment {
  content: string
}
