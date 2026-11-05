<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    open: boolean
    images: string[]
    index?: number
  }>(),
  { index: 0 },
)

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'update:index', value: number): void
}>()

const current = computed(() => props.images[props.index] ?? '')

function go(step: number) {
  const total = props.images.length
  if (total <= 1) return
  emit('update:index', (props.index + step + total) % total)
}

function onKeydown(event: KeyboardEvent) {
  if (!props.open) return
  if (event.key === 'Escape') emit('close')
  if (event.key === 'ArrowLeft') go(-1)
  if (event.key === 'ArrowRight') go(1)
}

watch(
  () => props.open,
  (open) => {
    if (!import.meta.client) return
    document.body.style.overflow = open ? 'hidden' : ''
    if (open) window.addEventListener('keydown', onKeydown)
    else window.removeEventListener('keydown', onKeydown)
  },
)

onBeforeUnmount(() => {
  if (!import.meta.client) return
  document.body.style.overflow = ''
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition duration-200"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition duration-150"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="open && current"
        class="fixed inset-0 z-[80] flex flex-col bg-slate-950/92 backdrop-blur-xl"
        role="dialog"
        aria-modal="true"
        aria-label="图片预览"
        @click.self="emit('close')"
      >
        <div class="flex items-center justify-between px-5 py-4">
          <p class="text-[11px] tabular-nums text-white/40">
            {{ index + 1 }} / {{ images.length }}
          </p>
          <button
            type="button"
            class="grid h-9 w-9 place-items-center rounded-full border border-white/10 bg-white/[0.06] text-lg text-white/60 transition hover:bg-white/[0.12] hover:text-white"
            aria-label="关闭预览"
            @click="emit('close')"
          >
            ×
          </button>
        </div>

        <div class="relative flex min-h-0 flex-1 items-center justify-center px-4 pb-5 sm:px-16">
          <button
            v-if="images.length > 1"
            type="button"
            class="absolute left-3 z-10 grid h-10 w-10 place-items-center rounded-full border border-white/10 bg-white/[0.06] text-white/60 backdrop-blur-md transition hover:bg-white/[0.14] hover:text-white sm:left-6"
            aria-label="上一张"
            @click="go(-1)"
          >
            ‹
          </button>

          <img
            :src="current"
            alt=""
            class="max-h-full max-w-full rounded-2xl border border-white/10 object-contain shadow-2xl"
            @click.stop
          />

          <button
            v-if="images.length > 1"
            type="button"
            class="absolute right-3 z-10 grid h-10 w-10 place-items-center rounded-full border border-white/10 bg-white/[0.06] text-white/60 backdrop-blur-md transition hover:bg-white/[0.14] hover:text-white sm:right-6"
            aria-label="下一张"
            @click="go(1)"
          >
            ›
          </button>
        </div>

        <div v-if="images.length > 1" class="flex justify-center gap-2 overflow-x-auto px-4 pb-5 no-scrollbar">
          <button
            v-for="(image, i) in images"
            :key="`${image}-${i}`"
            type="button"
            class="h-12 w-16 shrink-0 overflow-hidden rounded-lg border transition"
            :class="i === index ? 'border-sky-300/60 opacity-100' : 'border-white/10 opacity-50 hover:opacity-80'"
            @click="emit('update:index', i)"
          >
            <img :src="image" alt="" class="h-full w-full object-cover" loading="lazy" />
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>