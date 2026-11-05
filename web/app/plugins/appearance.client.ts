export default defineNuxtPlugin(() => {
  // 恢复背景/亮度设置并写入 CSS 变量
  useAppearance().init()
})