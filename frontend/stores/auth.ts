import { defineStore } from 'pinia'

const TOKEN_KEY = 'fishmo_token'
const USERNAME_KEY = 'fishmo_username'
const USER_ID_KEY = 'fishmo_user_id'
const AVATAR_KEY = 'fishmo_avatar'

/**
 * 认证状态（Pinia）：
 * token 持久化到 localStorage；SSR 阶段不会访问 localStorage（由 plugins/auth.client.ts 在客户端恢复）。
 */
export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(null)
  const userId = ref<number | null>(null)
  const username = ref<string | null>(null)
  const avatar = ref<string | null>(null)

  function isLoggedIn() {
    return !!token.value
  }

  function setAuth(t: string, id?: number, name?: string) {
    token.value = t
    if (id !== undefined) userId.value = id
    if (name !== undefined) username.value = name
    if (import.meta.client) {
      localStorage.setItem(TOKEN_KEY, t)
      if (id !== undefined) localStorage.setItem(USER_ID_KEY, String(id))
      if (name !== undefined) localStorage.setItem(USERNAME_KEY, name)
    }
  }

  function setUsername(name: string) {
    username.value = name
    if (import.meta.client) localStorage.setItem(USERNAME_KEY, name)
  }

  function setAvatar(url: string | null) {
    avatar.value = url
    if (import.meta.client) {
      if (url) localStorage.setItem(AVATAR_KEY, url)
      else localStorage.removeItem(AVATAR_KEY)
    }
  }

  function logout() {
    token.value = null
    userId.value = null
    username.value = null
    avatar.value = null
    if (import.meta.client) {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USERNAME_KEY)
      localStorage.removeItem(USER_ID_KEY)
      localStorage.removeItem(AVATAR_KEY)
    }
  }

  // 客户端启动时从 localStorage 恢复登录态
  function initFromStorage() {
    if (import.meta.client) {
      token.value = localStorage.getItem(TOKEN_KEY)
      const rawId = localStorage.getItem(USER_ID_KEY)
      userId.value = rawId ? Number(rawId) : null
      username.value = localStorage.getItem(USERNAME_KEY)
      avatar.value = localStorage.getItem(AVATAR_KEY)
    }
  }

  return { token, userId, username, avatar, isLoggedIn, setAuth, setUsername, setAvatar, logout, initFromStorage }
})
