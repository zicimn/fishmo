import type { NitroFetchOptions, NitroFetchRequest } from 'nitropack/types'
import { useAuthStore } from '~/stores/auth'

/**
 * 清理查询参数：
 * 后端 Optional 字段传空字符串/空数组可能导致 422（如 platform 为空串）或误匹配，
 * 统一剔除 undefined / null / '' / 空数组。
 */
export function cleanParams(params: object): Record<string, unknown> {
  const out: Record<string, unknown> = {}
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === '') continue
    if (Array.isArray(v) && v.length === 0) continue
    out[k] = v
  }
  return out
}

/** 构建带拦截器的 $fetch 实例（惰性创建，避免模块加载期访问 Nuxt 上下文） */
function createApi() {
  const config = useRuntimeConfig()
  return $fetch.create({
    // 默认 baseURL 为空 → 同源请求 /api，由 Nuxt Nitro 代理转发到后端，避免浏览器跨域。
    // 仅当显式配置 NUXT_PUBLIC_API_BASE 时才直连后端（会重新引入 CORS，需后端配合）。
    baseURL: (config.public.apiBase as string) || '',
    onRequest({ options }) {
      const auth = useAuthStore()
      if (auth.token) {
        const headers = new Headers(options.headers)
        headers.set('Authorization', `Bearer ${auth.token}`)
        options.headers = headers
      }
    },
    onResponseError({ response }) {
      // 仅客户端处理 401 跳转；服务端 SSR 请求遇到 401 只透出错误
      if (response.status === 401 && import.meta.client) {
        const url = (response.url || '') as string
        // 登录失败本身返回 401（用户名或密码不正确），不应触发登出与跳转
        if (url.includes('/user/login')) return
        const auth = useAuthStore()
        auth.logout()
        const route = useRoute()
        if (route.path !== '/user' && route.path !== '/user/profile') {
          navigateTo('/user')
        }
      }
    },
  })
}

let _api: ReturnType<typeof createApi> | null = null

/**
 * 统一请求封装：
 * - baseURL 默认同源（空串）→ /api 由 Nuxt Nitro 代理转发到后端，规避 CORS
 * - 自动附带 Authorization: Bearer <token>
 * - 401 时清理登录态并跳转登录页（登录接口自身的 401 除外）
 */
export function api<T = unknown>(
  request: string,
  opts: NitroFetchOptions<NitroFetchRequest> = {},
): Promise<T> {
  if (!_api) {
    _api = createApi()
  }
  return (_api as ReturnType<typeof createApi>)(request, opts) as Promise<T>
}

/**
 * 从请求异常中提取可读错误信息，用于 ElMessage.error 展示。
 * 后端 Pydantic 422 校验失败时 detail 是数组 [{loc, msg, type}]，直接显示会变成 "[object Object]"，
 * 这里归一为字符串：数组取各元素 msg（带 loc 提示）拼接，字符串原样返回，缺省给兜底文案。
 */
export function getErrDetail(e: unknown, fallback = '操作失败'): string {
  const detail = (e as { data?: { detail?: unknown } } | null | undefined)?.data?.detail
  if (Array.isArray(detail)) {
    const msgs = detail
      .map((d) => {
        if (!d || typeof d !== 'object') return String(d ?? '')
        const item = d as { msg?: unknown; loc?: unknown }
        if (typeof item.msg === 'string') {
          const loc = Array.isArray(item.loc) && item.loc.length ? item.loc.join('.') : ''
          return loc ? `${item.msg}（${loc}）` : item.msg
        }
        return String(item.msg ?? '')
      })
      .filter(Boolean)
    if (msgs.length) return msgs.join('；')
  }
  if (typeof detail === 'string' && detail.trim()) return detail
  if (detail != null) return String(detail)
  return fallback
}
