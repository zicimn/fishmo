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

export function useConfirm() {
  const state = useState<ConfirmState | null>('admin-confirm', () => null)

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