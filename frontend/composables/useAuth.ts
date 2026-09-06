import type {
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
  UserProfile,
  AccountUpdate,
} from '~/types'
import { useAuthStore } from '~/stores/auth'
import { api, cleanParams } from '~/utils/request'

/** 邮箱验证码（email 是 query 参数，非请求体） */
export function useEmail() {
  async function sendCode(email: string) {
    return api<{ message: string }>('/api/v1/email/send', {
      method: 'POST',
      query: { email },
    })
  }
  return { sendCode }
}

/** 认证相关：登录 / 注册 / 资料查看与编辑 / 登出 */
export function useAuth() {
  const auth = useAuthStore()

  async function login(username: string, password: string) {
    const res = await api<LoginResponse>('/api/v1/user/login', {
      method: 'POST',
      body: { username, password },
    })
    auth.setAuth(res.access_token, res.id, res.username)
    return res
  }

  async function register(payload: RegisterRequest, code: string) {
    return api<RegisterResponse>('/api/v1/user/register', {
      method: 'POST',
      query: { code },
      body: payload,
    })
  }

  /** 查看用户信息：不传 id 时后端用 token 定位自身 */
  async function fetchProfile(id?: number) {
    const res = await api<UserProfile>('/api/v1/user/', {
      query: cleanParams({ id }),
    })
    if (!id) auth.setAvatar(res.avatar)
    return res
  }

  async function updateProfile(payload: AccountUpdate) {
    const res = await api<UserProfile>('/api/v1/user/update', {
      method: 'PUT',
      body: payload,
    })
    if (res.username) auth.setUsername(res.username)
    auth.setAvatar(res.avatar)
    return res
  }

  async function deleteAccount() {
    await api('/api/v1/user/delete', { method: 'DELETE' })
    auth.logout()
  }

  function logout(redirect = true) {
    auth.logout()
    if (redirect && import.meta.client) {
      navigateTo('/')
    }
  }

  return {
    token: auth.token,
    userId: auth.userId,
    username: auth.username,
    avatar: auth.avatar,
    isLoggedIn: computed(() => !!auth.token),
    login,
    register,
    fetchProfile,
    updateProfile,
    deleteAccount,
    logout,
  }
}
