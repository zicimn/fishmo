// 外观设置：背景图 + 亮度 + 遮罩浓度。
// 状态在 SSR 使用默认值；客户端插件读 localStorage 后再覆盖，
// 因此不会产生水合不一致。

export const BACKGROUNDS = [
  '/background/0.jpg',
  '/background/1.jpg',
  '/background/2.jpg',
  '/background/3.jpg',
  '/background/4.jpg',
  '/background/5.jpg',
] as const

const STORAGE_KEY = 'fishmo_appearance'

export function useAppearance() {
  const background = useState<string>('appearance-background', () => '/background/2.jpg')
  const brightness = useState<number>('appearance-brightness', () => 1)
  const alpha = useState<number>('appearance-alpha', () => 0.6)

  function apply() {
    if (!import.meta.client) return
    const root = document.documentElement
    root.style.setProperty('--fish-brightness', String(brightness.value))
    root.style.setProperty('--fish-alpha', String(alpha.value))
  }

  function persist() {
    if (!import.meta.client) return
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          background: background.value,
          brightness: brightness.value,
          alpha: alpha.value,
        }),
      )
    } catch {
      // 忽略隐私模式写入失败
    }
  }

  function init() {
    if (!import.meta.client) return
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw) as Partial<{
          background: string
          brightness: number
          alpha: number
        }>
        if (typeof parsed.background === 'string' && parsed.background) {
          background.value = parsed.background
        }
        if (typeof parsed.brightness === 'number') {
          brightness.value = Math.min(1.2, Math.max(0.4, parsed.brightness))
        }
        if (typeof parsed.alpha === 'number') {
          alpha.value = Math.min(0.85, Math.max(0.2, parsed.alpha))
        }
      }
    } catch {
      // 本地存储损坏时使用默认值
    }
    apply()
  }

  function setBackground(value: string) {
    background.value = value
    persist()
  }

  function setBrightness(value: number) {
    brightness.value = value
    apply()
    persist()
  }

  function setAlpha(value: number) {
    alpha.value = value
    apply()
    persist()
  }

  function reset() {
    background.value = '/background/2.jpg'
    brightness.value = 1
    alpha.value = 0.6
    apply()
    persist()
  }

  return {
    background,
    brightness,
    alpha,
    init,
    apply,
    setBackground,
    setBrightness,
    setAlpha,
    reset,
  }
}