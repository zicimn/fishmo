/**
 * 管理端全局守卫：所有页面都要求管理员登录，登录页除外。
 * SSR 已关闭，这里总是运行在浏览器。
 */
export default defineNuxtRouteMiddleware((to) => {
  const { ready, isLoggedIn, init } = useAdminAuth()
  init()

  if (to.path === '/login') {
    if (ready.value && isLoggedIn.value) return navigateTo('/')
    return
  }

  if (!isLoggedIn.value) {
    return navigateTo({ path: '/login', query: to.fullPath === '/' ? undefined : { redirect: to.fullPath } })
  }
})