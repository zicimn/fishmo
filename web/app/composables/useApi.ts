import type { Envelope } from '~/types'
import { ApiError, describeError, errorStatus } from '~/utils/api'

type Query = Record<string, string | number | boolean | null | undefined>

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH'
  query?: Query
  body?: unknown
  headers?: Record<string, string>
  /** 不让 401 清理本地登录态（例如主动探测接口） */
  keepAuthOn401?: boolean
}

/**
 * 统一 API 客户端：自动注入 Bearer token，拆开 {msg, code, data} 信封，
 * 把后端错误转成带状态码的 ApiError。
 */
export function useApi() {
  const baseURL = useApiBase()
  const { token, clear } = useAuth()

  async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const headers: Record<string, string> = { ...(options.headers ?? {}) }
    if (token.value) headers.Authorization = `Bearer ${token.value}`

    try {
      const res = await $fetch<Envelope<T>>(path, {
        baseURL,
        method: options.method ?? 'GET',
        query: options.query,
        body: options.body as Record<string, unknown> | undefined,
        headers,
      })
      return res.data
    } catch (err) {
      const status = errorStatus(err)
      if (status === 401 && !options.keepAuthOn401 && import.meta.client) {
        clear()
      }
      throw new ApiError(describeError(err), status, (err as { data?: unknown })?.data)
    }
  }

  return {
    request,
    get: <T>(path: string, query?: Query) => request<T>(path, { query }),
    post: <T>(path: string, body?: unknown, query?: Query) =>
      request<T>(path, { method: 'POST', body, query }),
    put: <T>(path: string, body?: unknown, query?: Query) =>
      request<T>(path, { method: 'PUT', body, query }),
    del: <T>(path: string, query?: Query) => request<T>(path, { method: 'DELETE', query }),
  }
}