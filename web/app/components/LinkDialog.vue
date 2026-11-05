<script setup lang="ts">
import type { LinkItem, LinkPayload, SizeUnitValue } from '~/types'
import { SIZE_UNIT_OPTIONS } from '~/types'
import { describeError } from '~/utils/api'
import { isSafeHttpUrl } from '~/utils/link'

const props = withDefaults(
  defineProps<{
    open: boolean
    gameId: number
    link?: LinkItem | null
  }>(),
  { link: null },
)

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'saved'): void
}>()

const api = useApi()
const toast = useToast()
const submitting = ref(false)
const errorMsg = ref('')

const form = reactive({
  url: '',
  content: '',
  code: '',
  category: '',
  size: '',
  size_unit: 'GB' as SizeUnitValue,
})

const isEdit = computed(() => Boolean(props.link))
const title = computed(() => (isEdit.value ? '编辑资源链接' : '添加资源链接'))

watch(
  () => props.open,
  (open) => {
    if (!open) return
    const link = props.link
    form.url = link?.url ?? ''
    form.content = link?.content ?? ''
    form.code = link?.code ?? ''
    form.category = link?.category ?? ''
    form.size = link?.size != null ? String(link.size) : ''
    form.size_unit = link?.size_unit ?? 'GB'
    errorMsg.value = ''
    submitting.value = false
  },
)

function close() {
  if (submitting.value) return
  emit('close')
}

function toNullable(value: string): string | null {
  const text = value.trim()
  return text || null
}

async function submit() {
  if (submitting.value) return
  errorMsg.value = ''

  if (!isEdit.value) {
    const url = form.url.trim()
    if (!url) {
      errorMsg.value = '请填写链接地址'
      return
    }
    if (!isSafeHttpUrl(url)) {
      errorMsg.value = '链接必须以 http:// 或 https:// 开头'
      return
    }
  }

  let size: number | null = null
  if (form.size.trim()) {
    size = Number(form.size)
    if (!Number.isFinite(size) || size < 0) {
      errorMsg.value = '文件大小必须是不小于 0 的数字'
      return
    }
  }

  const payload: LinkPayload = {
    content: toNullable(form.content),
    code: toNullable(form.code),
    category: toNullable(form.category),
    size,
    size_unit: size != null ? form.size_unit : null,
  }

  submitting.value = true
  try {
    if (isEdit.value && props.link) {
      await api.put('/api/v1/link/review', payload, { link_id: props.link.id })
      toast.success('链接已更新')
    } else {
      await api.post(
        '/api/v1/link/add',
        { ...payload, url: form.url.trim() },
        { game_id: props.gameId },
      )
      toast.success('链接已添加')
    }
    emit('saved')
    emit('close')
  } catch (err) {
    errorMsg.value = describeError(err)
  } finally {
    submitting.value = false
  }
}
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
        v-if="open"
        class="fixed inset-0 z-[70] flex items-end justify-center bg-slate-950/75 p-0 backdrop-blur-sm sm:items-center sm:p-6"
        role="dialog"
        aria-modal="true"
        :aria-label="title"
        @click.self="close"
        @keydown.esc="close"
      >
        <form
          class="max-h-[92vh] w-full max-w-lg overflow-y-auto rounded-t-3xl border border-white/10 bg-slate-950/95 p-6 shadow-2xl backdrop-blur-3xl sm:rounded-3xl"
          @submit.prevent="submit"
        >
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="section-kicker">RESOURCE LINK</p>
              <h2 class="mt-1 text-base font-semibold text-white">{{ title }}</h2>
            </div>
            <button
              type="button"
              class="grid h-8 w-8 place-items-center rounded-full text-white/40 transition hover:bg-white/10 hover:text-white"
              aria-label="关闭"
              @click="close"
            >
              ×
            </button>
          </div>

          <div class="mt-5 space-y-4">
            <label v-if="!isEdit" class="block">
              <span class="label-base">链接地址（必填）</span>
              <input
                v-model="form.url"
                type="url"
                maxlength="255"
                placeholder="https://pan.example.com/..."
                class="input-base mt-1.5"
              />
            </label>
            <div v-else class="rounded-xl border border-white/10 bg-white/[0.04] px-3.5 py-2.5">
              <p class="text-[11px] text-white/35">链接地址</p>
              <p class="mt-0.5 truncate text-xs text-white/60">{{ link?.url }}</p>
            </div>

            <div class="grid gap-3 sm:grid-cols-2">
              <label class="block">
                <span class="label-base">网盘 / 来源</span>
                <input
                  v-model="form.category"
                  maxlength="255"
                  placeholder="如：百度网盘"
                  class="input-base mt-1.5"
                />
              </label>
              <label class="block">
                <span class="label-base">提取码</span>
                <input
                  v-model="form.code"
                  maxlength="255"
                  placeholder="如：abcd"
                  class="input-base mt-1.5"
                />
              </label>
            </div>

            <div class="grid grid-cols-[minmax(0,1fr)_104px] gap-3">
              <label class="block">
                <span class="label-base">文件大小</span>
                <input
                  v-model="form.size"
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="如：2.5"
                  class="input-base mt-1.5"
                />
              </label>
              <label class="block">
                <span class="label-base">单位</span>
                <select v-model="form.size_unit" class="input-base mt-1.5">
                  <option v-for="unit in SIZE_UNIT_OPTIONS" :key="unit" :value="unit">
                    {{ unit }}
                  </option>
                </select>
              </label>
            </div>

            <label class="block">
              <span class="label-base">备注</span>
              <textarea
                v-model="form.content"
                rows="3"
                maxlength="255"
                placeholder="解压密码、版本说明等"
                class="input-base mt-1.5 resize-y"
              />
            </label>
          </div>

          <p
            v-if="errorMsg"
            class="mt-3 rounded-xl border border-rose-400/25 bg-rose-500/10 px-3 py-2 text-xs leading-relaxed text-rose-200"
            role="alert"
          >
            {{ errorMsg }}
          </p>

          <div class="mt-5 flex justify-end gap-3">
            <button type="button" class="btn-ghost" :disabled="submitting" @click="close">
              取消
            </button>
            <button type="submit" class="btn-primary px-6" :disabled="submitting">
              {{ submitting ? '保存中…' : isEdit ? '保存修改' : '添加链接' }}
            </button>
          </div>
        </form>
      </div>
    </Transition>
  </Teleport>
</template>