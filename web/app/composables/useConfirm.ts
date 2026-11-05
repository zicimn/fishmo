export interface ConfirmOptions {
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  danger?: boolean
}

interface ConfirmState extends ConfirmOptions {
  resolve: (value: boolean) => void
}

/**
 * Promise 化的确认框：await confirm({...}) 返回 true / false。
 * 状态放在 useState 里，ConfirmHost 挂载一次即可服务全站。
 */
export function useConfirm() {
  const state = useState<ConfirmState | null>('confirm-state', () => null)

  function confirm(options: ConfirmOptions): Promise<boolean> {
    return new Promise((resolve) => {
      state.value = { ...options, resolve }
    })
  }

  function settle(value: boolean) {
    const current = state.value
    state.value = null
    current?.resolve(value)
  }

  return { state, confirm, settle }
}