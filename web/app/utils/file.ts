// 图片上传前的客户端处理：
// 后端接受 base64 data URL，并会校验解码后 ≤5MB、像素 ≤50MP。
// 在浏览器端先把长边压到 1600、转 WebP，既省流量也避免直接撞上限。

export const MAX_UPLOAD_BYTES = 5 * 1024 * 1024
const MAX_RAW_BYTES = 20 * 1024 * 1024
const DEFAULT_MAX_EDGE = 1600

export function isImageFile(file: File): boolean {
  return file.type.startsWith('image/')
}

function readAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.onerror = () => reject(new Error('读取文件失败'))
    reader.readAsDataURL(file)
  })
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error('图片解析失败'))
    image.src = src
  })
}

/**
 * 把用户选择的图片转成后端可接收的 base64。
 * 动图会变成静态首帧；这在上传头像/封面/截图的场景里可以接受。
 */
export async function fileToDataUrl(
  file: File,
  maxEdge = DEFAULT_MAX_EDGE,
): Promise<string> {
  if (!isImageFile(file)) throw new Error('请选择图片文件')
  if (file.size > MAX_RAW_BYTES) throw new Error('原图不能超过 20MB')

  const source = await readAsDataUrl(file)

  // SVG 无法稳定经过 canvas 重编码，直接交给后端（后端只接受位图解码，会拒绝）
  if (file.type === 'image/svg+xml') {
    throw new Error('暂不支持 SVG，请使用 PNG / JPG / WebP')
  }

  const image = await loadImage(source)
  const longest = Math.max(image.naturalWidth, image.naturalHeight)
  if (!longest) throw new Error('图片尺寸无效')

  const scale = Math.min(1, maxEdge / longest)
  const width = Math.max(1, Math.round(image.naturalWidth * scale))
  const height = Math.max(1, Math.round(image.naturalHeight * scale))

  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const context = canvas.getContext('2d')
  if (!context) throw new Error('浏览器不支持图片处理')
  context.drawImage(image, 0, 0, width, height)

  const encoded = canvas.toDataURL('image/webp', 0.85)
  // canvas 不可用时 toDataURL 会退回 png；两种都是合法 data URL
  if (!encoded.startsWith('data:image/')) throw new Error('图片转换失败')
  return encoded
}