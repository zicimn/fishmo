// 管理端时间展示：固定东八区，避免不同浏览器时区产生歧义。

const DATE_FORMATTER = new Intl.DateTimeFormat('zh-CN', {
  timeZone: 'Asia/Shanghai',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
})

const DATETIME_FORMATTER = new Intl.DateTimeFormat('zh-CN', {
  timeZone: 'Asia/Shanghai',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
})

function parse(value?: string | null): Date | null {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

/** 2026-10-31 */
export function formatDate(value?: string | null): string {
  const date = parse(value)
  return date ? DATE_FORMATTER.format(date) : '—'
}

/** 2026-10-31 14:05 */
export function formatDateTime(value?: string | null): string {
  const date = parse(value)
  return date ? DATETIME_FORMATTER.format(date) : '—'
}