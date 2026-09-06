import { useAuthStore } from '~/stores/auth'

/**
 * 登录守卫：
 * SSR 阶段 token 尚未从 localStorage 恢复，只在客户端判断。
 * 未登录则跳转登录页，并携带 redirect 参数便于登录后回跳。
 */
export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore()
  if (import.meta.client && !auth.token) {
    return navigateTo(`/user?redirect=${encodeURIComponent(to.fullPath)}`)
  }
})
