// 大小格式化工具。
// 后端 schemas/link.py 的 size 语义为「字节」，前端展示/输入以 MB 为单位，提交前需换算回字节。

/**
 * 将字节数格式化为人类可读的大小展示文本（如 "1.2 MB" / "512 KB"）。
 * 小于 1MB 显示 KB，避免出现 0.01MB 这类不直观值；空值/非法值返回空串。
 */
export function formatBytes(bytes: number | null | undefined): string {
  if (bytes == null || Number.isNaN(bytes) || bytes < 0) return ''
  if (bytes === 0) return '0 MB'
  const mb = bytes / 1024 / 1024
  if (mb < 1) {
    const kb = bytes / 1024
    return `${Math.max(1, Math.round(kb))} KB`
  }
  return `${mb.toFixed(1)} MB`
}

/** 字节 → MB（回显/编辑表单时把后端字节值换算为 MB，保留两位小数）。 */
export function bytesToMb(bytes: number | null | undefined): number | undefined {
  if (bytes == null || Number.isNaN(bytes) || bytes < 0) return undefined
  return Math.round((bytes / 1024 / 1024) * 100) / 100
}

/** MB（表单输入值）→ 字节（后端存储单位），空值/非法值返回 null。 */
export function mbToBytes(mb: number | null | undefined): number | null {
  if (mb == null || Number.isNaN(mb) || mb < 0) return null
  return Math.round(mb * 1024 * 1024)
}
