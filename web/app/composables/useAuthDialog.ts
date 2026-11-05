export type AuthMode = 'login' | 'register'

/** 全站共享的登录弹窗状态：Header / 评论区 / 发布页都能打开它。 */
export function useAuthDialog() {
  const open = useState<boolean>('auth-dialog-open', () => false)
  const mode = useState<AuthMode>('auth-dialog-mode', () => 'login')

  function openAuth(next: AuthMode = 'login') {
    mode.value = next
    open.value = true
  }

  function closeAuth() {
    open.value = false
  }

  return { open, mode, openAuth, closeAuth }
}