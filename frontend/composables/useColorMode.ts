/**
 * 深色模式（固定深色，不提供亮色切换）。
 * - 《fishmo 视觉定位》Dark 游戏门户，始终为深色。
 * - 深色通过 <html class="dark"> 控制（Element Plus dark 选择器）。
 * - nuxt.config.ts 内联脚本在 paint 前添加 dark class，避免闪烁。
 * - 保留最小兼容导出，供依赖该 composable 的组件使用。
 */
export function useColorMode() {
  const isDark = ref(true)

  function setMode() {
    /* 始终深色，亮色模式已移除 */
  }

  function toggle() {
    /* 始终深色，亮色模式已移除 */
  }

  onMounted(() => {
    // 确保 dark class 始终存在
    if (import.meta.client) {
      document.documentElement.classList.add('dark')
    }
  })

  return { isDark, setMode, toggle }
}
