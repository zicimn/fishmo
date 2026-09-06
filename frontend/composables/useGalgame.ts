import type {
  GalgameListQuery,
  GalList,
  GalgameDetail,
  AddGal,
  EditGal,
} from '~/types'
import { api, cleanParams } from '~/utils/request'

/** 游戏列表：SSR 友好（useAsyncData），query 变化自动重新拉取 */
export function useGalgameList(
  query: Ref<GalgameListQuery>,
  options: { key?: string; server?: boolean } = {},
) {
  const key = options.key || 'galgame-list'
  return useAsyncData(
    key,
    () => api<GalList>('/api/v1/galgame/', { query: cleanParams(query.value) }),
    { watch: [query], server: options.server ?? true },
  )
}

/** 游戏详情：按 id 拉取（带 SSR 缓存） */
export function useGalgameDetail(id: Ref<number | string>) {
  return useAsyncData(
    `galgame-detail-${id.value}`,
    () => api<GalgameDetail>(`/api/v1/galgame/${id.value}`),
    { watch: [id] },
  )
}

/** 发布游戏（需登录） */
export async function addGalgame(payload: AddGal) {
  return api<{ msg: string; id: number }>('/api/v1/galgame/add', {
    method: 'POST',
    body: payload,
  })
}

/** 编辑游戏（仅作者，query 传 id） */
export async function editGalgame(id: number, payload: EditGal) {
  return api<{ msg: string; id: number; user_id: number }>('/api/v1/galgame/edit', {
    method: 'PUT',
    query: { id },
    body: payload,
  })
}

/** 删除游戏（仅作者，query 传 id） */
export async function deleteGalgame(id: number) {
  return api<{ msg: string; id: number; user_id: number }>('/api/v1/galgame/delete', {
    method: 'DELETE',
    query: { id },
  })
}
