export type ToastType = 'success' | 'error' | 'info'

export interface ToastItem {
  id: number
  message: string
  type: ToastType
}

let seed = 0

/** 轻量全局提示。ToastHost 负责渲染，任意组件调用 useToast().success(...)。 */
export function useToast() {
  const items = useState<ToastItem[]>('toast-items', () => [])

  function remove(id: number) {
    items.value = items.value.filter((item) => item.id !== id)
  }

  function push(message: string, type: ToastType = 'info', duration = 3200) {
    const id = ++seed
    items.value = [...items.value, { id, message, type }]
    if (import.meta.client) {
      setTimeout(() => remove(id), duration)
    }
  }

  return {
    items,
    remove,
    push,
    success: (message: string) => push(message, 'success'),
    error: (message: string) => push(message, 'error', 4200),
    info: (message: string) => push(message, 'info'),
  }
}