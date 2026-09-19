import { useAuthStore } from '~/stores/auth'

/**
 * 管理员守卫：
 * SSR 阶段 isAdmin 尚未从 localStorage 恢复，只在客户端判断。
 * 非管理员跳转首页。
 */
export default defineNuxtRouteMiddleware((to) => {
  const auth = useAuthStore()
  if (import.meta.client && !auth.isAdmin) {
    return navigateTo('/')
  }
})
