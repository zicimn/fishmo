import type { AuthData, AuthUser, Envelope } from '~/types'

// 令牌与用户快照都存在 localStorage：前台没有服务端会话，令牌来自
// 登录响应体的 access_token。快照只用于界面展示，真正的身份与权限
// 由后端每次回库判定。
const TOKEN_KEY = 'fishmo_access_token'
const USER_KEY = 'fishmo_user'

export interface RegisterPayload {
  email: string
  code: string
  username: string
  password: string
  re_password: string
}

/**
 * 登录态的唯一出口。
 *
 * 用 useState 而不是 Pinia：前台只需要「令牌 + 用户」两个值。
 * SSR 时状态恒为空，客户端在 plugin 里回填，避免水合不一致。
 */
export function useAuth() {
  const apiBase = useApiBase()
  const token = useState<string>('auth-token', () => '')
  const user = useState<AuthUser | null>('auth-user', () => null)
  // ready 表示「已经尝试读过本地存储」，在那之前不要急着渲染「未登录」
  const ready = useState<boolean>('auth-ready', () => false)

  const isLoggedIn = computed(() => Boolean(token.value) && user.value !== null)
  const isAdmin = computed(() => Boolean(user.value?.is_admin))

  function persist(data: AuthData) {
    const nextUser: AuthUser = {
      id: Number(data.user.id),
      username: data.user.username,
      email: data.user.email ?? '',
      avatar: typeof data.user.avatar === 'string' ? data.user.avatar : '',
      bio: typeof data.user.bio === 'string' ? data.user.bio : '',
      is_admin: Boolean(data.user.is_admin),
      created_at: data.user.created_at,
    }
    token.value = data.access_token
    user.value = nextUser
    if (import.meta.client) {
      try {
        localStorage.setItem(TOKEN_KEY, data.access_token)
        localStorage.setItem(USER_KEY, JSON.stringify(nextUser))
      } catch {
        // 隐私模式 / 配额满：写不进去也不影响本次会话
      }
    }
  }

  function applyProfile(data: Partial<AuthUser>) {
    if (!user.value) return
    const nextUser: AuthUser = {
      ...user.value,
      ...data,
      avatar: data.avatar ?? user.value.avatar ?? '',
      bio: data.bio ?? user.value.bio ?? '',
    }
    user.value = nextUser
    if (import.meta.client) {
      try {
        localStorage.setItem(USER_KEY, JSON.stringify(nextUser))
      } catch {
        // 与 persist 一致
      }
    }
  }

  function clear() {
    token.value = ''
    user.value = null
    if (!import.meta.client) return
    try {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    } catch {
      // localStorage 被禁用时内存态已清空
    }
  }

  /** 只在客户端、且只跑一次：从 localStorage 恢复登录态。 */
  function init() {
    if (!import.meta.client || ready.value) return
    ready.value = true
    try {
      const savedToken = localStorage.getItem(TOKEN_KEY) ?? ''
      const rawUser = localStorage.getItem(USER_KEY)
      if (!savedToken || !rawUser) {
        if (savedToken || rawUser) clear()
        return
      }
      const parsed = JSON.parse(rawUser) as Partial<AuthUser> | null
      if (
        !parsed ||
        typeof parsed.id !== 'number' ||
        typeof parsed.username !== 'string' ||
        !parsed.username
      ) {
        clear()
        return
      }
      token.value = savedToken
      user.value = {
        id: parsed.id,
        username: parsed.username,
        email: typeof parsed.email === 'string' ? parsed.email : '',
        avatar: typeof parsed.avatar === 'string' ? parsed.avatar : '',
        bio: typeof parsed.bio === 'string' ? parsed.bio : '',
        is_admin: Boolean(parsed.is_admin),
        created_at: parsed.created_at,
      }
    } catch {
      clear()
    }
  }

  async function login(username: string, password: string) {
    const res = await $fetch<Envelope<AuthData>>('/api/v1/user/login', {
      baseURL: apiBase,
      method: 'POST',
      body: { username, password },
    })
    persist(res.data)
    return res.data
  }

  async function register(payload: RegisterPayload) {
    const res = await $fetch<Envelope<AuthData>>('/api/v1/user/register', {
      baseURL: apiBase,
      method: 'POST',
      query: { code: payload.code },
      body: {
        username: payload.username,
        email: payload.email,
        password: payload.password,
        // 后端 Account 没有 re_password 字段；两次一致性由前端校验
      },
    })
    persist(res.data)
    return res.data
  }

  /** 发送注册验证码；返回后端给的过期秒数（用于提示，不用于倒计时）。 */
  async function sendCode(email: string, purpose: 'register' | 'reset' = 'register') {
    const res = await $fetch<Envelope<{ expires_in: number }>>('/api/v1/email/send', {
      baseURL: apiBase,
      method: 'POST',
      query: { email, purpose },
    })
    return res.data
  }

  /**
   * 登出：先清本地、再尽力通知后端拉黑令牌。
   * 后端 Redis 故障时登出会失败关闭，但本地仍应退出。
   */
  async function logout() {
    const current = token.value
    clear()
    if (!current) return
    try {
      await $fetch('/api/v1/user/logout', {
        baseURL: apiBase,
        method: 'POST',
        headers: { Authorization: `Bearer ${current}` },
      })
    } catch {
      // 网络 / 后端故障：本地已经退出，不再向用户报错
    }
  }

  return {
    token,
    user,
    ready,
    isLoggedIn,
    isAdmin,
    init,
    login,
    register,
    sendCode,
    logout,
    clear,
    applyProfile,
  }
}