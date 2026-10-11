// ===== comment 模块类型（与 backend schemas/comment.py 对齐，嵌套评论 2 层）=====

export interface CommentItem {
  id: number
  content: string | null
  receive_id: number
  parent_id: number | null
  reply_to_id: number | null
}

export interface CommentAccount {
  username: string
  avatar: string | null
}

/** 子评论（第 2 层）条目：包含被回复者信息 */
export interface ReplyItems {
  item: CommentItem
  account: CommentAccount
  reply_to_account: CommentAccount | null
}

/** 顶级评论（第 1 层）条目：包含子评论列表与回复计数 */
export interface NestedCommentItems {
  item: CommentItem
  account: CommentAccount
  replies: ReplyItems[]
  reply_count: number
}

/** GET /api/v1/comment/{target_id} 列表响应 */
export interface CommentList {
  total: number
  items: NestedCommentItems[]
}

/** POST /api/v1/comment/add 请求体（支持嵌套回复） */
export interface AddComment {
  content: string
  parent_id?: number | null
  reply_to_id?: number | null
}

/** PUT /api/v1/comment/edit 请求体 */
export interface EditComment {
  content: string
}
