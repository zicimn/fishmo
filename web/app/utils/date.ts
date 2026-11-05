// 固定按东八区展示：SSR 与浏览器时区不同时，toLocaleString 会产生
// 不一致的文本，导致水合告警。
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

/** 刚刚 / 3 小时前 / 2 天前；超过 30 天回落到日期 */
export function relativeTime(value?: string | null): string {
  const date = parse(value)
  if (!date) return '—'
  const diff = Date.now() - date.getTime()
  if (diff < 0) return formatDate(value)
  const minute = 60_000
  const hour = 60 * minute
  const day = 24 * hour
  if (diff < minute) return '刚刚'
  if (diff < hour) return `${Math.floor(diff / minute)} 分钟前`
  if (diff < day) return `${Math.floor(diff / hour)} 小时前`
  if (diff < 30 * day) return `${Math.floor(diff / day)} 天前`
  return formatDate(value)
}