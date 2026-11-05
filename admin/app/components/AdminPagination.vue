<script setup lang="ts">
const props = defineProps<{
  page: number
  totalPages: number
  total?: number
}>()

const emit = defineEmits<{ (e: 'update:page', value: number): void }>()

function goTo(target: number) {
  if (target < 1 || target > props.totalPages || target === props.page) return
  emit('update:page', target)
}
</script>

<template>
  <nav
    v-if="totalPages > 1"
    class="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-white/5 pt-4"
    aria-label="分页"
  >
    <p class="text-[11px] text-white/30">
      <span v-if="total != null" class="tabular-nums">{{ total }}</span> 条 ·
      第 <span class="tabular-nums text-white/50">{{ page }}</span> /
      <span class="tabular-nums">{{ totalPages }}</span> 页
    </p>
    <div class="flex items-center gap-1.5">
      <button
        type="button"
        class="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[11px] text-white/55 transition hover:bg-white/[0.1] hover:text-white disabled:opacity-30"
        :disabled="page <= 1"
        @click="goTo(page - 1)"
      >
        上一页
      </button>
      <button
        type="button"
        class="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[11px] text-white/55 transition hover:bg-white/[0.1] hover:text-white disabled:opacity-30"
        :disabled="page >= totalPages"
        @click="goTo(page + 1)"
      >
        下一页
      </button>
    </div>
  </nav>
</template>