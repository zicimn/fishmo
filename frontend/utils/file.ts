// 将 File 对象读取为 base64 data URL。
// 后端 utils/webp.py 的 convert_image_to_webp 支持 "data:image/xxx;base64," 前缀，可直接传入。
export function fileToBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(new Error('读取文件失败'))
    reader.readAsDataURL(file)
  })
}

// 图片大小上限，与后端 utils/webp.py 的 MAX_IMAGE_BYTES（5MB）保持一致。
// 前端预检可避免超大图膨胀为巨大 JSON body 发送到后端。
export const MAX_IMAGE_BYTES = 5 * 1024 * 1024

/**
 * 读取图片并校验大小（与后端单图 ≤5MB 限制对齐）。
 * 超限或读取失败会 reject（中文错误信息），调用方捕获后：
 * - 用 ElMessage.error 提示用户；
 * - 不将该图加入预览/上传列表。
 */
export function readImageAsBase64(file: File, maxBytes: number = MAX_IMAGE_BYTES): Promise<string> {
  return new Promise((resolve, reject) => {
    if (file.size > maxBytes) {
      reject(new Error(`图片不能超过 ${(maxBytes / 1024 / 1024).toFixed(0)}MB`))
      return
    }
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(new Error('读取图片失败'))
    reader.readAsDataURL(file)
  })
}
