// 后端错误有两种形态：
//   1. 业务错误 → 全局 AppError handler 转成 {"detail": "中文提示"}；
//   2. 入参校验 → FastAPI/Pydantic 的 detail 是数组 [{ loc, msg, type }, ...]。
// 前端只展示一条可读信息，不把数组或 ofetch 的英文原文直接抛给用户。

const STATUS_FALLBACK: Record<number, string> = {
  400: '请求有误，请检查后重试',
  401: '登录已失效，请重新登录',
  403: '没有权限进行该操作',
  404: '内容不存在',
  409: '数据冲突，请稍后重试',
  413: '文件过大，请压缩后重试',
  422: '提交的内容不符合要求',
  429: '操作过于频繁，请稍后再试',
  500: '服务器开小差了，请稍后重试',
  502: '服务暂时不可用，请稍后重试',
  503: '服务暂时不可用，请稍后重试',
}

export class ApiError extends Error {
  status: number | null
  payload: unknown

  constructor(message: string, status: number | null = null, payload: unknown = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

export function errorStatus(err: unknown): number | null {
  if (!err || typeof err !== 'object') return null
  const candidate = err as {
    status?: unknown
    statusCode?: unknown
    response?: { status?: unknown }
  }
  for (const value of [
    candidate.status,
    candidate.statusCode,
    candidate.response?.status,
  ]) {
    if (typeof value === 'number' && value >= 100) return value
  }
  return null
}

function errorDetail(err: unknown): unknown {
  if (!err || typeof err !== 'object' || !('data' in err)) return undefined
  const data = (err as { data?: unknown }).data
  if (!data || typeof data !== 'object' || !('detail' in data)) return undefined
  return (data as { detail?: unknown }).detail
}

function messageOf(item: unknown): string {
  if (typeof item === 'string') return item
  if (item && typeof item === 'object' && 'msg' in item) {
    const msg = (item as { msg?: unknown }).msg
    if (typeof msg === 'string') return msg
  }
  return ''
}

const HAS_CHINESE = /[一-鿿]/

/**
 * 把任意请求异常翻成一句中文。
 *
 * Pydantic 内置约束的 msg 是英文（"String should have at least 1 character"），
 * 对访客没有意义，所以只采纳带中文的条目（自定义 validator 抛的
 * "Value error, 评论内容不能为空" 会命中），其余落到状态码兜底文案。
 */
export function describeError(err: unknown): string {
  if (err instanceof ApiError) return err.message

  const detail = errorDetail(err)

  if (typeof detail === 'string' && detail.trim()) return detail.trim()

  if (Array.isArray(detail)) {
    for (const item of detail) {
      const msg = messageOf(item).replace(/^Value error,\s*/, '').trim()
      if (msg && HAS_CHINESE.test(msg)) return msg
    }
  }

  const status = errorStatus(err)
  if (status) return STATUS_FALLBACK[status] ?? `请求失败（${status}）`

  // 本地抛出的中文 Error（如图片处理失败）直接展示
  if (err instanceof Error && HAS_CHINESE.test(err.message)) return err.message

  return '网络连接失败，请检查网络后重试'
}