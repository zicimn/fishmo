import MarkdownIt from 'markdown-it'

// 文章正文是 Markdown：后端不存 HTML，前端渲染。
// html: false 会让 markdown-it 把原始 HTML 当作普通文本转义输出，
// 因此无需再引入 DOMPurify / jsdom，SSR 也能安全渲染。
const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  typographer: false,
})

// 外链统一新窗口打开，并加 noopener；站内相对链接保持原行为
const defaultLinkOpen = md.renderer.rules.link_open
md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  const token = tokens[idx]
  if (token) {
    const href = token.attrGet('href') ?? ''
    if (/^https?:\/\//i.test(href)) {
      token.attrSet('target', '_blank')
      token.attrSet('rel', 'noopener noreferrer nofollow')
    }
  }
  return defaultLinkOpen
    ? defaultLinkOpen(tokens, idx, options, env, self)
    : self.renderToken(tokens, idx, options)
}

export function renderMarkdown(source?: string | null): string {
  return md.render(source ?? '')
}

/** 粗略估算纯文本长度（用于“字数”展示） */
export function markdownPlainText(source?: string | null): string {
  return (source ?? '')
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/[#>*_`~-]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
}