import type { ArticleList, ArticlePublish, ArticleDetail, ArticleManageList } from '~/types/article'
import { api, cleanParams } from '~/utils/request'

/** 公开文章列表 — 传入 page/size/category 的 ref 以支持响应式刷新 */
export function useArticleList(page: Ref<number> = ref(1), size: Ref<number> = ref(10), category: Ref<string | undefined> = ref(undefined)) {
  const key = computed(() => `article-list-${category.value || 'all'}`)
  return useAsyncData(
    key,
    () => api<ArticleList>('/api/v1/article/', {
      query: cleanParams({
        page: page.value,
        size: size.value,
        category: category.value || undefined,
      }),
    }),
    { watch: [page, size, category] },
  )
}

/** 文章详情（SSR 友好） */
export function useArticleDetail(id: Ref<string | number>) {
  return useAsyncData(
    `article-detail-${id.value}`,
    () => api<ArticleDetail>(`/api/v1/article/${id.value}`),
    { watch: [id] },
  )
}

/** 个人文章管理列表（需登录） — 传入 page/size 的 ref 以支持响应式刷新 */
export function useArticleManage(page: Ref<number> = ref(1), size: Ref<number> = ref(10)) {
  return useAsyncData(
    'article-manage',
    () => api<ArticleManageList>('/api/v1/article/manage', { query: cleanParams({ page: page.value, size: size.value }) }),
    { watch: [page, size], server: false },
  )
}

/** 发布文章（需登录） */
export async function publishArticle(data: ArticlePublish) {
  return api<{ msg: string; id: number }>('/api/v1/article/add', {
    method: 'POST',
    body: data,
  })
}

/** 编辑文章（需登录） */
export async function editArticle(id: number, data: ArticlePublish) {
  return api<{ msg: string; id: number; user_id: number }>('/api/v1/article/edit', {
    method: 'PUT',
    query: { id },
    body: data,
  })
}

/** 删除文章（需登录） */
export async function deleteArticle(id: number) {
  return api<{ msg: string; id: number; user_id: number }>('/api/v1/article/delete', {
    method: 'DELETE',
    query: { id },
  })
}