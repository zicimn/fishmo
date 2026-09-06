// 客户端插件：从 localStorage 恢复登录态（.client 后缀保证只在浏览器执行，SSR 不触碰 localStorage）
export default defineNuxtPlugin(() => {
  const auth = useAuthStore()
  auth.initFromStorage()
})
