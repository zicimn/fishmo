<script setup lang="ts">
const { state, settle } = useConfirm()

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && state.value) settle(false)
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

watch(
  () => state.value,
  (value) => {
    if (!import.meta.client) return
    document.body.style.overflow = value ? 'hidden' : ''
  },
)

onBeforeUnmount(() => {
  if (import.meta.client) document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <div
      v-if="state"
      class="fixed inset-0 z-[110] grid place-items-center bg-slate-950/70 px-4 backdrop-blur-sm"
      @click.self="settle(false)"
    >
      <div
        role="alertdialog"
        aria-modal="true"
        class="w-full max-w-sm rounded-3xl border border-white/10 bg-slate-900/90 p-6 shadow-[0_24px_80px_-24px_rgba(2,6,23,0.95)] backdrop-blur-2xl"
      >
        <h2 class="text-base font-semibold text-white">
          {{ state.title || '请确认' }}
        </h2>
        <p class="mt-2.5 text-xs leading-relaxed text-white/50">
          {{ state.message }}
        </p>
        <div class="mt-6 flex justify-end gap-3">
          <button type="button" class="btn-ghost" @click="settle(false)">
            {{ state.cancelText || '取消' }}
          </button>
          <button
            type="button"
            :class="state.danger ? 'btn-danger' : 'btn-primary'"
            @click="settle(true)"
          >
            {{ state.confirmText || '确认' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>