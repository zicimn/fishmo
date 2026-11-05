import type { AuthData, AuthUser, Envelope } from '~/types'

const TOKEN_KEY = 'fishmo_admin_token'
const USER_KEY = 'fishmo_admin_user'

/**
 * 管理端登录态：与前台共用 /api/v1/user/login，但只有 is_admin 的账号能进入。
 * 令牌保存在 localStorage，SSR 已关闭，不存在水合问题。
 */
export function useAdminAuth() {
  const config = useRuntimeConfig()
  const token = useState<string>('admin-token', () => '')
  const user = useState<AuthUser | null>('admin-user', () => null)
  const ready = useState<boolean>('admin-ready', () => false)

  const isLoggedIn = computed(() => Boolean(token.value) && user.value !== null)

  function apiBase(): string {
    return config.public.apiBase || 'http://127.0.0.1:8000'
  }

  function persist(data: AuthData) {
    const nextUser: AuthUser = {
      id: Number(data.user.id),
      username: data.user.username,
      email: data.user.email ?? '',
      avatar: data.user.avatar ?? '',
      is_admin: Boolean(data.user.is_admin),
      created_at: data.user.created_at,
    }
    token.value = data.access_token
    user.value = nextUser
    try {
      localStorage.setItem(TOKEN_KEY, data.access_token)
      localStorage.setItem(USER_KEY, JSON.stringify(nextUser))
    } catch {
      // 隐私模式下写不进去，本次会话仍然有效
    }
  }

  function clear() {
    token.value = ''
    user.value = null
    try {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    } catch {
      // 忽略
    }
  }

  function init() {
    if (ready.value) return
    ready.value = true
    try {
      const savedToken = localStorage.getItem(TOKEN_KEY) ?? ''
      const rawUser = localStorage.getItem(USER_KEY)
      if (!savedToken || !rawUser) {
        if (savedToken || rawUser) clear()
        return
      }
      const parsed = JSON.parse(rawUser) as Partial<AuthUser> | null
      if (!parsed || parsed.is_admin !== true || typeof parsed.id !== 'number') {
        clear()
        return
      }
      token.value = savedToken
      user.value = {
        id: parsed.id,
        username: typeof parsed.username === 'string' ? parsed.username : '',
        email: typeof parsed.email === 'string' ? parsed.email : '',
        avatar: typeof parsed.avatar === 'string' ? parsed.avatar : '',
        is_admin: true,
        created_at: parsed.created_at,
      }
    } catch {
      clear()
    }
  }

  async function login(username: string, password: string) {
    const res = await $fetch<Envelope<AuthData>>('/api/v1/user/login', {
      baseURL: apiBase(),
      method: 'POST',
      body: { username, password },
    })
    if (!res.data.user.is_admin) {
      throw new Error('该账号没有管理员权限')
    }
    persist(res.data)
    return res.data
  }

  async function logout() {
    const current = token.value
    clear()
    if (!current) return
    try {
      await $fetch('/api/v1/user/logout', {
        baseURL: apiBase(),
        method: 'POST',
        headers: { Authorization: `Bearer ${current}` },
      })
    } catch {
      // 后端不可用时本地退出即可
    }
  }

  return { token, user, ready, isLoggedIn, init, login, logout, clear }
}