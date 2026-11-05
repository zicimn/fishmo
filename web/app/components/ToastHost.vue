<script setup lang="ts">
const { items, remove } = useToast()

const styles: Record<string, string> = {
  success: 'border-emerald-400/25 bg-emerald-500/15 text-emerald-100',
  error: 'border-rose-400/25 bg-rose-500/15 text-rose-100',
  info: 'border-sky-400/25 bg-sky-500/15 text-sky-100',
}
</script>

<template>
  <Teleport to="body">
    <div
      class="pointer-events-none fixed inset-x-0 top-4 z-[120] flex flex-col items-center gap-2 px-4 sm:left-auto sm:right-4 sm:items-end"
      aria-live="polite"
    >
      <TransitionGroup name="toast">
        <div
          v-for="item in items"
          :key="item.id"
          class="pointer-events-auto flex w-full max-w-sm items-start gap-3 rounded-xl border px-4 py-3 text-xs leading-relaxed shadow-[0_18px_50px_-20px_rgba(2,6,23,0.95)] backdrop-blur-2xl"
          :class="styles[item.type]"
          role="status"
        >
          <span class="mt-0.5 h-1.5 w-1.5 shrink-0 rounded-full bg-current opacity-70" />
          <span class="min-w-0 flex-1">{{ item.message }}</span>
          <button
            type="button"
            class="shrink-0 text-current opacity-40 transition hover:opacity-90"
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

<style scoped>
.toast-enter-active,
.toast-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>