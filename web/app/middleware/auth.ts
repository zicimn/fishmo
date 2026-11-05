/**
 * 登录守卫：前台没有服务端会话，只能在客户端判断。
 * 未登录时打开全局登录弹窗并回到首页，登录后可通过 ?redirect 回到原页面。
 */
export default defineNuxtRouteMiddleware((to) => {
  if (import.meta.server) return

  const { isLoggedIn, ready, init } = useAuth()
  init()
  if (!ready.value || isLoggedIn.value) return

  const { openAuth } = useAuthDialog()
  const toast = useToast()
  openAuth('login')
  toast.info('请先登录后再继续')
  return navigateTo({
    path: '/',
    query: to.fullPath === '/' ? undefined : { redirect: to.fullPath },
  })
})