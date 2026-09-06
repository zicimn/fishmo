import type { LinkList, AddLink, EditLink } from '~/types'
import { api, cleanParams } from '~/utils/request'

/** 链接列表（SSR 友好） */
export function useLinkList(gameId: number, page = 1, size = 20) {
  return useAsyncData(
    `link-list-${gameId}`,
    () => api<LinkList>(`/api/v1/link/${gameId}`, { query: { page, size } }),
  )
}

/**
 * 按用户获取其发布的链接列表（仅客户端拉取，userId 来自 localStorage 恢复的登录态）。
 * query 变化自动重新拉取；未登录（userId 为空）时返回 null。
 */
export function useUserLinkList(
  query: Ref<{ userId?: number; page?: number; size?: number }>,
  options: { key?: string } = {},
) {
  const key = options.key || 'user-link-list'
  return useAsyncData(
    key,
    () => {
      const q = query.value
      if (!q.userId) return Promise.resolve(null)
      return api<LinkList>(`/api/v1/link/user/${q.userId}`, {
        query: cleanParams({ page: q.page, size: q.size }),
      })
    },
    { watch: [query], server: false },
  )
}

/** 添加链接（需登录，game_id 走 query） */
export async function addLink(gameId: number, payload: AddLink) {
  return api<{ msg: string; id: number }>('/api/v1/link/add', {
    method: 'POST',
    query: { game_id: gameId },
    body: payload,
  })
}

/** 编辑链接（仅作者，link_id 走 query） */
export async function reviewLink(linkId: number, payload: EditLink) {
  return api<{ msg: string; id: number; user_id: number }>('/api/v1/link/review', {
    method: 'PUT',
    query: { link_id: linkId },
    body: payload,
  })
}

/** 删除链接（仅作者，link_id 走 query） */
export async function deleteLink(linkId: number) {
  return api<{ msg: string; id: number; user_id: number }>('/api/v1/link/delete', {
    method: 'DELETE',
    query: { link_id: linkId },
  })
}
