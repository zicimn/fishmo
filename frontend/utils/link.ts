// 链接 URL 安全校验。
// 后端 AddLink.url 仅做长度校验，可存入 javascript: 等可执行协议（潜在 XSS）。
// Vue 不会转义 href 属性中的协议，故前端渲染前需做协议白名单校验。

// 允许的协议：站内安全的 http/https + 常见下载协议。
const ALLOWED_LINK_PROTOCOLS = ['https:', 'http:', 'magnet:', 'ed2k:', 'ftp:', 'thunder:', 'bt:']

/** 校验链接协议是否在允许白名单内（http/https/magnet/ed2k/ftp/thunder/bt）。 */
export function isSafeLink(url: string): boolean {
  if (!url || !url.trim()) return false
  const trimmed = url.trim()
  try {
    const parsed = new URL(trimmed)
    return ALLOWED_LINK_PROTOCOLS.includes(parsed.protocol.toLowerCase())
  } catch {
    // URL() 解析失败（如某些非标准但合法的下载协议）时用正则兜底。
    // 协议相对地址（//evil.com）与 javascript: 等均不匹配，返回 false。
    return /^(https?|magnet|ed2k|ftp|thunder|bt):/i.test(trimmed)
  }
}
