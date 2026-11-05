export interface ToastItem {
  id: number
  type: 'success' | 'error' | 'info'
  message: string
}

let seed = 0

export function useToast() {
  const items = useState<ToastItem[]>('admin-toasts', () => [])

  function remove(id: number) {
    items.value = items.value.filter((item) => item.id !== id)
  }

  function push(type: ToastItem['type'], message: string) {
    const id = ++seed
    items.value = [...items.value, { id, type, message }]
    if (import.meta.client) {
      window.setTimeout(() => remove(id), type === 'error' ? 4200 : 3000)
    }
  }

  return {
    items,
    remove,
    success: (message: string) => push('success', message),
    error: (message: string) => push('error', message),
    info: (message: string) => push('info', message),
  }
}