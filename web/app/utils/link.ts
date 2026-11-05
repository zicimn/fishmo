/** 只允许 http(s) 外链，避免 javascript: / data: 之类的危险协议。 */
export function isSafeHttpUrl(value: string): boolean {
  try {
    const url = new URL(value)
    return (
      (url.protocol === 'http:' || url.protocol === 'https:') &&
      Boolean(url.hostname)
    )
  } catch {
    return false
  }
}