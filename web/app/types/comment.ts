// 评论组件共用的类型与转换（后端传的是纯文本输入、HTML 输出）
export type CommentType = 'galgame' | 'article'

export interface ReplyTarget {
  parentId: number
  replyToId: number | null
  name: string
}