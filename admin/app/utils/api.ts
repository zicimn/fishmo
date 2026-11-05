// 把各种 $fetch 错误整理成中文提示。

export class ApiError extends Error {
  status: number
  payload: unknown

  constructor(message: string, status: number, payload?: unknown) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

export function errorStatus(err: unknown): number {
  if (!err || typeof err !== 'object') return 0
  const value = err as {
    statusCode?: number
    status?: number
    response?: { status?: number }
  }
  return value.statusCode ?? value.response?.status ?? value.status ?? 0
}

function pickDetail(err: unknown): string {
  if (!err || typeof err !== 'object') return ''
  const data = (err as { data?: unknown }).data
  if (!data || typeof data !== 'object') return ''
  const detail = (data as { detail?: unknown }).detail

  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    // Pydantic 校验错误：只保留后端写好的中文 msg
    return detail
      .map((item) =>
        item && typeof item === 'object' && typeof (item as { msg?: unknown }).msg === 'string'
          ? (item as { msg: string }).msg
          : '',
      )
      .filter(Boolean)
      .join('；')
  }
  return ''
}

export function describeError(err: unknown): string {
  const detail = pickDetail(err)
  if (detail) return detail

  const status = errorStatus(err)
  if (status === 400) return '请求参数有误'
  if (status === 401) return '登录已失效，请重新登录'
  if (status === 403) return '没有权限执行该操作'
  if (status === 404) return '目标不存在或已被删除'
  if (status === 409) return '数据冲突，请刷新后重试'
  if (status === 429) return '操作过于频繁，请稍后再试'
  if (status >= 500) return '服务器出了点问题，请稍后重试'

  if (err instanceof Error) {
    if (err.message && /[一-龥]/.test(err.message)) return err.message
    if (err.message === 'Failed to fetch') return '无法连接后端服务'
  }
  return '网络连接失败'
}