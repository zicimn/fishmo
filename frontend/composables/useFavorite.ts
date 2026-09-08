import type { Ref } from 'vue'
import type { FavoriteList } from '~/types'
import { api } from '~/utils/request'

/** 添加收藏 */
export async function addFavorite(galId: number) {
  return api<{ message: string; favorite_id: number }>(
    `/api/v1/favorite/add?gal_id=${galId}`,
    { method: 'POST' },
  )
}

/** 取消收藏 */
export async function removeFavorite(galId: number) {
  return api<{ message: string }>(
    `/api/v1/favorite/remove?gal_id=${galId}`,
    { method: 'DELETE' },
  )
}

/** 收藏列表（分页）：server: false —— 需登录态，SSR 阶段无 token */
export function useFavoriteList(query: Ref<{ page: number; size: number }>) {
  return useAsyncData(
    'favorite-list',
    () => api<FavoriteList>('/api/v1/favorite/list', { query: query.value }),
    { watch: [query], server: false },
  )
}
