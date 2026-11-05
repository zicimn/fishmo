import type { Envelope } from '~/types'
import { ApiError, describeError, errorStatus } from '~/utils/api'

type Query = Record<string, string | number | boolean | null | undefined>

/**
 * 带管理员令牌的请求封装：拆开 {msg, code, data} 信封。
 * 401 时清空登录态并回到登录页。
 */
export function useAdminApi() {
  const config = useRuntimeConfig()
  const { token, clear } = useAdminAuth()

  const baseURL = computed(() => config.public.apiBase || 'http://127.0.0.1:8000')

  async function request<T>(
    path: string,
    options: {
      method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
      query?: Query
      body?: unknown
    } = {},
  ): Promise<T> {
    const headers: Record<string, string> = {}
    if (token.value) headers.Authorization = `Bearer ${token.value}`

    try {
      const res = await $fetch<Envelope<T>>(path, {
        baseURL: baseURL.value,
        method: options.method ?? 'GET',
        query: options.query,
        body: options.body as Record<string, unknown> | undefined,
        headers,
      })
      return res.data
    } catch (err) {
      const status = errorStatus(err)
      if (status === 401) {
        clear()
        navigateTo('/login')
      }
      throw new ApiError(describeError(err), status, (err as { data?: unknown })?.data)
    }
  }

  return {
    request,
    get: <T>(path: string, query?: Query) => request<T>(path, { query }),
    put: <T>(path: string, body?: unknown, query?: Query) =>
      request<T>(path, { method: 'PUT', body, query }),
    del: <T>(path: string, query?: Query) => request<T>(path, { method: 'DELETE', query }),
  }
}