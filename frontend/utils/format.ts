// 大小格式化工具。
// 新数据：size 为浮点数值 + size_unit（KB/MB/GB）直接展示，无需换算。
// 旧数据（size_unit 为 null）：size 按字节处理，兼容历史数据。

import type { SizeUnit } from '~/types/link'

/**
 * 格式化链接大小展示文本。
 * - 有 size_unit 时直接拼接（如 "2.5 GB"）；
 * - 无 size_unit 时按旧数据字节处理（fallback 到 formatBytes）。
 */
export function formatLinkSize(size: number | null | undefined, sizeUnit?: SizeUnit | null): string {
  if (size == null || Number.isNaN(size) || size <= 0) return ''
  if (sizeUnit) {
    // 整数值不显示小数位，非整数保留 1 位
    const text = Number.isInteger(size) ? String(size) : size.toFixed(1)
    return `${text} ${sizeUnit}`
  }
  // 旧数据：size 为字节
  return formatBytes(size)
}

/**
 * 将字节数格式化为人类可读的大小展示文本（如 "1.2 MB" / "512 KB"）。
 * 小于 1MB 显示 KB，避免出现 0.01MB 这类不直观值；空值/非法值返回空串。
 * 仅用于兼容旧数据（size_unit 为 null 时 size 按字节存储）。
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

/**
 * 旧数据字节值 → { size, size_unit } 用于编辑表单回显。
 * 自动选择最合适的单位：≥1GB 用 GB，≥1MB 用 MB，否则用 KB。
 */
export function bytesToSizeUnit(bytes: number | null | undefined): { size: number | undefined; size_unit: SizeUnit } {
  if (bytes == null || Number.isNaN(bytes) || bytes <= 0) {
    return { size: undefined, size_unit: 'MB' }
  }
  const gb = bytes / 1024 / 1024 / 1024
  if (gb >= 1) {
    return { size: Math.round(gb * 100) / 100, size_unit: 'GB' }
  }
  const mb = bytes / 1024 / 1024
  if (mb >= 1) {
    return { size: Math.round(mb * 100) / 100, size_unit: 'MB' }
  }
  const kb = bytes / 1024
  return { size: Math.round(kb * 100) / 100, size_unit: 'KB' }
}
