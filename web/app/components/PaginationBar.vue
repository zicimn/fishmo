<script setup lang="ts">
const props = defineProps<{
  page: number
  totalPages: number
}>()

const emit = defineEmits<{ (e: 'update:page', value: number): void }>()

const pages = computed<(number | '…')[]>(() => {
  const total = props.totalPages
  const current = props.page
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)

  const result: (number | '…')[] = [1]
  const start = Math.max(2, current - 1)
  const end = Math.min(total - 1, current + 1)

  if (start > 2) result.push('…')
  for (let i = start; i <= end; i += 1) result.push(i)
  if (end < total - 1) result.push('…')
  result.push(total)
  return result
})

function goTo(target: number) {
  if (target < 1 || target > props.totalPages || target === props.page) return
  emit('update:page', target)
  if (import.meta.client) window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<template>
  <nav v-if="totalPages > 1" class="mt-12 flex flex-wrap items-center justify-center gap-1.5" aria-label="分页">
    <button
      type="button"
      class="rounded-full border border-white/10 bg-white/[0.06] px-4 py-2 text-xs text-white/60 backdrop-blur-xl transition hover:bg-white/[0.12] hover:text-white disabled:cursor-not-allowed disabled:opacity-30"
      :disabled="page <= 1"
      @click="goTo(page - 1)"
    >
      上一页
    </button>

    <template v-for="(item, index) in pages" :key="`${item}-${index}`">
      <span v-if="item === '…'" class="px-1.5 text-xs text-white/25">…</span>
      <button
        v-else
        type="button"
        class="min-w-9 rounded-full border px-3 py-2 text-xs tabular-nums transition"
        :class="
          item === page
            ? 'border-sky-300/40 bg-sky-400/15 text-sky-100'
            : 'border-white/10 bg-white/[0.04] text-white/50 hover:bg-white/[0.1] hover:text-white'
        "
        :aria-current="item === page ? 'page' : undefined"
        @click="goTo(item as number)"
      >
        {{ item }}
      </button>
    </template>

    <button
      type="button"
      class="rounded-full border border-white/10 bg-white/[0.06] px-4 py-2 text-xs text-white/60 backdrop-blur-xl transition hover:bg-white/[0.12] hover:text-white disabled:cursor-not-allowed disabled:opacity-30"
      :disabled="page >= totalPages"
      @click="goTo(page + 1)"
    >
      下一页
    </button>
  </nav>
</template>