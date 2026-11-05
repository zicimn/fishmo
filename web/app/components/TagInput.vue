<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    modelValue: string[]
    placeholder?: string
    max?: number
    maxLength?: number
  }>(),
  {
    placeholder: '输入后按回车添加',
    max: 20,
    maxLength: 40,
  },
)

const emit = defineEmits<{ (e: 'update:modelValue', value: string[]): void }>()

const draft = ref('')

function commit() {
  const raw = draft.value
  const candidates = raw
    .split(/[,，\n]/)
    .map((item) => item.trim().slice(0, props.maxLength))
    .filter(Boolean)

  if (!candidates.length) {
    draft.value = ''
    return
  }

  const next = [...props.modelValue]
  for (const item of candidates) {
    if (next.length >= props.max) break
    if (!next.includes(item)) next.push(item)
  }
  emit('update:modelValue', next)
  draft.value = ''
}

function remove(index: number) {
  emit(
    'update:modelValue',
    props.modelValue.filter((_, i) => i !== index),
  )
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' || event.key === ',' || event.key === '，') {
    event.preventDefault()
    commit()
    return
  }
  if (event.key === 'Backspace' && !draft.value && props.modelValue.length) {
    remove(props.modelValue.length - 1)
  }
}

function onBlur() {
  if (draft.value.trim()) commit()
}
</script>

<template>
  <div class="rounded-xl border border-white/10 bg-slate-950/50 px-3 py-2.5 transition focus-within:border-sky-300/40 focus-within:ring-2 focus-within:ring-sky-400/20">
    <div v-if="modelValue.length" class="mb-2 flex flex-wrap gap-1.5">
      <span
        v-for="(tag, index) in modelValue"
        :key="`${tag}-${index}`"
        class="inline-flex items-center gap-1 rounded-full border border-white/10 bg-white/[0.06] px-2.5 py-1 text-[11px] text-white/65"
      >
        {{ tag }}
        <button
          type="button"
          class="text-white/30 transition hover:text-rose-200"
          :aria-label="`移除 ${tag}`"
          @click="remove(index)"
        >
          ×
        </button>
      </span>
    </div>
    <input
      v-model="draft"
      :placeholder="modelValue.length >= max ? '已达到数量上限' : placeholder"
      :disabled="modelValue.length >= max"
      maxlength="120"
      class="w-full bg-transparent text-sm text-white outline-none placeholder:text-white/20 disabled:cursor-not-allowed"
      @keydown="onKeydown"
      @blur="onBlur"
    />
  </div>
</template>