export default defineNuxtPlugin(() => {
  // 只在客户端恢复登录态；SSR 阶段不读 localStorage
  useAuth().init()
})