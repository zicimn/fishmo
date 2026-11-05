/**
 * 后端 API 的 baseURL。
 *
 * - 本地：浏览器与 SSR 都直连 http://127.0.0.1:8000；
 * - 生产：浏览器走 nginx 同源的 /api，SSR 仍直连后端。
 *
 * 服务端必须用绝对地址：Nitro 的本地 fetch 会把 `/api` 当作 Nuxt 自己的
 * 路由，请求不会经过 nginx。apiBaseServer 是私有 runtimeConfig，
 * 不会下发到浏览器。
 */
const LOOPBACK_HOSTS = new Set(['localhost', '127.0.0.1', '0.0.0.0', '::1'])

function isLoopback(hostname: string): boolean {
  return LOOPBACK_HOSTS.has(hostname.replace(/^\[|\]$/g, ''))
}

export function useApiBase(): string {
  const config = useRuntimeConfig()
  if (import.meta.server) {
    return config.apiBaseServer || config.public.apiBase
  }

  const base = config.public.apiBase

  // 防呆：生产构建若把回环地址打进 public 配置，访客浏览器会去连他自己的
  // 机器。页面不在回环地址上时，这种地址一定不可用，直接退回同源 /api。
  try {
    const parsed = new URL(base, window.location.origin)
    const pageHost = window.location.hostname
    if (
      parsed.origin !== window.location.origin &&
      isLoopback(parsed.hostname) &&
      !isLoopback(pageHost)
    ) {
      console.error(
        `[api] public.apiBase="${base}" 指向本机回环地址，线上不可用，已退回同源 /api。`,
      )
      return '/api'
    }
  } catch {
    // base 不是合法 URL（例如本来就配置成 /api），按原值使用
  }

  return base
}

/** 仅用于界面文案（如“请确认后端已启动”），两端取值一致。 */
export function useApiBaseLabel(): string {
  return useRuntimeConfig().public.apiBase
}