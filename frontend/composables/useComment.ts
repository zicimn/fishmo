import type { CommentList } from '~/types'
import { api, cleanParams } from '~/utils/request'

/** 评论列表（SSR 友好），type 支持 "galgame" | "article" */
export function useCommentList(targetId: number, page = 1, size = 20, type = 'galgame') {
  return useAsyncData(
    `comment-list-${targetId}-${type}`,
    () =>
      api<CommentList>(`/api/v1/comment/${targetId}`, {
        query: cleanParams({ page, size, type }),
      }),
  )
}

/**
 * 按用户获取其发表的评论列表（仅客户端拉取，userId 来自 localStorage 恢复的登录态）。
 * query 变化自动重新拉取；未登录（userId 为空）时返回 null。
 */
export function useUserCommentList(
  query: Ref<{ userId?: number; page?: number; size?: number }>,
  options: { key?: string } = {},
) {
  const key = options.key || 'user-comment-list'
  return useAsyncData(
    key,
    () => {
      const q = query.value
      if (!q.userId) return Promise.resolve(null)
      return api<CommentList>(`/api/v1/comment/user/${q.userId}`, {
        query: cleanParams({ page: q.page, size: q.size }),
      })
    },
    { watch: [query], server: false },
  )
}

/** 发表评论（需登录，game_id 走 query），type 支持 "galgame" | "article" */
export async function addComment(targetId: number, content: string, type = 'galgame') {
  return api<{ msg: string; id: number }>('/api/v1/comment/add', {
    method: 'POST',
    query: cleanParams({ game_id: targetId, type }),
    body: { content },
  })
}

/** 编辑评论（仅作者，comment_id 走 query） */
export async function editComment(commentId: number, content: string) {
  return api<{ msg: string; id: number; user_id: number }>('/api/v1/comment/edit', {
    method: 'PUT',
    query: { comment_id: commentId },
    body: { content },
  })
}

/** 删除评论（仅作者，comment_id 走 query） */
export async function deleteComment(commentId: number) {
  return api<{ msg: string; id: number; user_id: number }>('/api/v1/comment/delete', {
    method: 'DELETE',
    query: { comment_id: commentId },
  })
}
