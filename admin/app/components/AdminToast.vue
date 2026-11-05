<script setup lang="ts">
const { items, remove } = useToast()

const styles: Record<string, string> = {
  success: 'border-emerald-400/25 bg-emerald-500/10 text-emerald-100',
  error: 'border-rose-400/25 bg-rose-500/10 text-rose-100',
  info: 'border-sky-400/25 bg-sky-500/10 text-sky-100',
}
</script>

<template>
  <Teleport to="body">
    <div class="pointer-events-none fixed right-4 top-4 z-[120] flex w-[calc(100%-2rem)] max-w-sm flex-col gap-2">
      <TransitionGroup
        enter-active-class="transition duration-200"
        enter-from-class="translate-y-2 opacity-0"
        enter-to-class="translate-y-0 opacity-100"
        leave-active-class="transition duration-150"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div
          v-for="item in items"
          :key="item.id"
          class="pointer-events-auto flex items-start gap-2 rounded-xl border px-3.5 py-2.5 text-xs leading-relaxed shadow-lg backdrop-blur-xl"
          :class="styles[item.type]"
          role="status"
        >
          <span class="flex-1">{{ item.message }}</span>
          <button
            type="button"
            class="shrink-0 opacity-50 transition hover:opacity-100"
            aria-label="关闭提示"
            @click="remove(item.id)"
          >
            ×
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>