<script setup lang="ts">
const { state, settle } = useConfirm()

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && state.value) settle(false)
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-150"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-100"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="state"
        class="fixed inset-0 z-[110] flex items-center justify-center bg-slate-950/75 px-4 backdrop-blur-sm"
        @click.self="settle(false)"
      >
        <div
          role="alertdialog"
          aria-modal="true"
          class="w-full max-w-sm rounded-2xl border border-white/10 bg-slate-900/95 p-6 shadow-2xl backdrop-blur-2xl"
        >
          <h2 class="text-sm font-semibold text-white">{{ state.title ?? '请确认' }}</h2>
          <p class="mt-2 text-xs leading-relaxed text-white/45">{{ state.message }}</p>
          <div class="mt-6 flex justify-end gap-2">
            <button type="button" class="btn-ghost px-4 py-2" @click="settle(false)">
              {{ state.cancelText ?? '取消' }}
            </button>
            <button
              type="button"
              class="px-4 py-2"
              :class="state.danger ? 'btn-danger' : 'btn-primary'"
              @click="settle(true)"
            >
              {{ state.confirmText ?? '确认' }}
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>