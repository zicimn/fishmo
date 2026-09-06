/**
 * 深色/浅色模式（SSR 安全）。
 * - 默认深色（《fishmo 视觉定位》Dark 游戏门户），深色通过 <html class="dark"> 控制（Element Plus dark 选择器）。
 * - SSR 首帧不带 dark，与客户端首帧一致避免水合不匹配；nuxt.config.ts 中 app.head 的内联脚本
 *   在 paint 前默认加 dark（仅 localStorage 显式存 'light' 时才保持浅色），避免闪烁。
 * - 偏好持久化在 localStorage（key: fishmo-color-mode）。
 */
const COLOR_MODE_KEY = 'fishmo-color-mode'

export function useColorMode() {
  // 默认深色：SSR 首帧的图标态与内联脚本施加的 dark 一致，避免客户端切换闪烁
  const isDark = ref(true)

  function applyClass(dark: boolean) {
    if (import.meta.client) {
      document.documentElement.classList.toggle('dark', dark)
    }
  }

  function setMode(dark: boolean) {
    isDark.value = dark
    applyClass(dark)
    if (import.meta.client) {
      try {
        localStorage.setItem(COLOR_MODE_KEY, dark ? 'dark' : 'light')
        // 同步浏览器主题色（移动端地址栏），随模式切换（深黑灰 / 浅灰）
        const meta = document.querySelector<HTMLMetaElement>('meta[name="theme-color"]')
        if (meta) meta.content = dark ? '#0b0b0f' : '#f6f6f8'
      } catch {
        /* localStorage 不可用（隐私模式等）时静默忽略 */
      }
    }
  }

  function toggle() {
    setMode(!isDark.value)
  }

  // 客户端挂载后同步实际状态（内联脚本可能已在 paint 前添加了 dark class）。
  // 放在 onMounted 里读取，SSR 与客户端首帧一致，避免水合不匹配。
  onMounted(() => {
    isDark.value = !!document.documentElement.classList.contains('dark')
  })

  return { isDark, setMode, toggle }
}
