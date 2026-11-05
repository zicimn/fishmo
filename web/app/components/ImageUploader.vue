<script setup lang="ts">
import { fileToDataUrl } from '~/utils/file'
import { isSafeHttpUrl } from '~/utils/link'
import { describeError } from '~/utils/api'

const props = withDefaults(
  defineProps<{
    modelValue: string | string[]
    multiple?: boolean
    label?: string
    hint?: string
    max?: number
    ratio?: 'cover' | 'wide' | 'square'
  }>(),
  {
    multiple: false,
    label: '',
    hint: '',
    max: 10,
    ratio: 'cover',
  },
)

const emit = defineEmits<{ (e: 'update:modelValue', value: string | string[]): void }>()

const toast = useToast()
const fileInput = ref<HTMLInputElement | null>(null)
const urlDraft = ref('')
const busy = ref(false)

const items = computed<string[]>(() =>
  Array.isArray(props.modelValue)
    ? props.modelValue
    : props.modelValue
      ? [props.modelValue]
      : [],
)

const ratioClass = computed(() => {
  if (props.ratio === 'wide') return 'aspect-[16/10]'
  if (props.ratio === 'square') return 'aspect-square'
  return 'aspect-[2/3]'
})

function isDataUrl(value: string) {
  return value.startsWith('data:')
}

function emitValue(next: string[]) {
  emit('update:modelValue', props.multiple ? next : (next[0] ?? ''))
}

async function onFiles(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files ?? [])
  input.value = ''
  if (!files.length) return

  busy.value = true
  try {
    const encoded: string[] = []
    for (const file of files) {
      encoded.push(await fileToDataUrl(file))
      if (!props.multiple || encoded.length + items.value.length >= props.max) break
    }
    if (props.multiple) {
      emitValue([...items.value, ...encoded].slice(0, props.max))
    } else {
      emitValue([encoded[0]!])
    }
  } catch (err) {
    toast.error(describeError(err))
  } finally {
    busy.value = false
  }
}

function addUrl() {
  const url = urlDraft.value.trim()
  if (!url) return
  if (!isSafeHttpUrl(url)) {
    toast.error('图片链接必须是 http(s) 地址')
    return
  }
  if (props.multiple) {
    if (items.value.length >= props.max) return
    emitValue([...items.value, url])
  } else {
    emitValue([url])
  }
  urlDraft.value = ''
}

function remove(index: number) {
  emitValue(items.value.filter((_, i) => i !== index))
}
</script>

<template>
  <div>
    <div class="flex items-center justify-between gap-3">
      <span v-if="label" class="label-base">{{ label }}</span>
      <span v-if="multiple" class="text-[10px] tabular-nums text-white/25">
        {{ items.length }} / {{ max }}
      </span>
    </div>

    <div v-if="multiple" class="mt-1.5 grid grid-cols-3 gap-2 sm:grid-cols-4">
      <div
        v-for="(item, index) in items"
        :key="`${item.slice(0, 24)}-${index}`"
        class="group relative aspect-square overflow-hidden rounded-xl border border-white/10 bg-slate-950/40"
      >
        <img :src="item" alt="" class="h-full w-full object-cover" />
        <button
          type="button"
          class="absolute right-1.5 top-1.5 grid h-6 w-6 place-items-center rounded-full bg-slate-950/75 text-xs text-white/70 opacity-0 backdrop-blur transition hover:text-rose-200 group-hover:opacity-100"
          aria-label="移除图片"
          @click="remove(index)"
        >
          ×
        </button>
      </div>

      <button
        v-if="items.length < max"
        type="button"
        :disabled="busy"
        class="grid aspect-square place-items-center rounded-xl border border-dashed border-white/15 bg-white/[0.03] text-xs text-white/35 transition hover:border-sky-300/30 hover:text-white/70 disabled:opacity-50"
        @click="fileInput?.click()"
      >
        {{ busy ? '处理中…' : '+ 上传' }}
      </button>
    </div>

    <div v-else class="mt-1.5 flex items-start gap-3">
      <div
        :class="ratioClass"
        class="relative w-24 shrink-0 overflow-hidden rounded-xl border border-white/10 bg-slate-950/40"
      >
        <img
          v-if="items[0]"
          :src="items[0]"
          alt=""
          class="absolute inset-0 h-full w-full object-cover"
        />
        <div
          v-else
          class="grid h-full place-items-center text-[10px] text-white/25"
        >
          无图片
        </div>
      </div>

      <div class="min-w-0 flex-1 space-y-2">
        <div class="flex flex-wrap gap-2">
          <button type="button" class="btn-ghost px-3 py-1.5" :disabled="busy" @click="fileInput?.click()">
            {{ busy ? '处理中…' : items[0] ? '更换图片' : '选择图片' }}
          </button>
          <button
            v-if="items[0]"
            type="button"
            class="rounded-lg px-2 py-1.5 text-[11px] text-white/30 transition hover:text-rose-200"
            @click="remove(0)"
          >
            移除
          </button>
        </div>

        <div class="flex gap-2">
          <input
            v-model="urlDraft"
            placeholder="或粘贴图片链接"
            class="input-base min-w-0 flex-1 py-1.5 text-xs"
            @keydown.enter.prevent="addUrl"
          />
          <button type="button" class="btn-ghost shrink-0 px-3 py-1.5" @click="addUrl">
            使用
          </button>
        </div>

        <p v-if="items[0] && isDataUrl(items[0])" class="text-[10px] text-emerald-200/50">
          已选择本地图片，提交时自动上传。
        </p>
        <p v-else-if="hint" class="text-[10px] text-white/25">{{ hint }}</p>
      </div>
    </div>

    <input
      ref="fileInput"
      type="file"
      accept="image/png,image/jpeg,image/webp,image/gif"
      :multiple="multiple"
      class="hidden"
      @change="onFiles"
    />
  </div>
</template>