/**
 * 从封面图提取平均主色（仅客户端运行），用于详情页辅助色 --cover-accent。
 * - 图片跨域 / CORS 未放行、解码失败或不可读时返回 null，调用方需判空兜底（不破坏视觉）。
 * - 仅在客户端 setProperty，SSR 首帧使用默认 Accent（见 theme.css 的 --el-color-primary），
 *   避免水合不匹配。
 */
export async function extractCoverAccent(src: string): Promise<string | null> {
  if (!import.meta.client) return null
  try {
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.src = src
    await img.decode()
    if (!img.naturalWidth || !img.naturalHeight) return null

    // 缩小采样（32 宽等比），既快又稳
    const w = 32
    const h = Math.max(1, Math.round((img.naturalHeight / img.naturalWidth) * w))
    const canvas = document.createElement('canvas')
    canvas.width = w
    canvas.height = h
    const ctx = canvas.getContext('2d', { willReadFrequently: true })
    if (!ctx) return null
    ctx.drawImage(img, 0, 0, w, h)
    const { data } = ctx.getImageData(0, 0, w, h)

    let r = 0
    let g = 0
    let b = 0
    let count = 0
    for (let i = 0; i < data.length; i += 4) {
      if (data[i + 3] < 128) continue // 跳过近透明像素
      r += data[i]
      g += data[i + 1]
      b += data[i + 2]
      count++
    }
    if (!count) return null
    r = Math.round(r / count)
    g = Math.round(g / count)
    b = Math.round(b / count)

    // 平均色过暗时向柔和的紫蓝（品牌色系 rgb(124,123,242)）提亮，保证作为辅助色仍可辨
    const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    if (lum < 110) {
      const t = 1 - lum / 160
      r = Math.round(r + (124 - r) * t)
      g = Math.round(g + (123 - g) * t)
      b = Math.round(b + (242 - b) * t)
    }

    return `rgb(${r}, ${g}, ${b})`
  } catch {
    return null
  }
}
