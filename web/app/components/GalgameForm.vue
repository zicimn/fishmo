<script setup lang="ts">
import type { AddGalPayload, CategoryValue, GalDetail } from '~/types'
import { CATEGORY_OPTIONS, PLATFORM_OPTIONS } from '~/types'

const props = withDefaults(
  defineProps<{
    mode?: 'add' | 'edit'
    initial?: Partial<GalDetail> | null
    submitting?: boolean
  }>(),
  { mode: 'add', initial: null, submitting: false },
)

const emit = defineEmits<{
  (e: 'submit', payload: AddGalPayload): void
  (e: 'cancel'): void
}>()

const form = reactive({
  name: '',
  cn_name: '',
  jp_name: '',
  en_name: '',
  content: '',
  category: '' as '' | CategoryValue,
  platfrom: [] as string[],
  company: [] as string[],
  tag: [] as string[],
  cover: '',
  images: [] as string[],
})

const errorMsg = ref('')

function populate() {
  const source = props.initial
  form.name = source?.name ?? ''
  form.cn_name = source?.cn_name ?? ''
  form.jp_name = source?.jp_name ?? ''
  form.en_name = source?.en_name ?? ''
  form.content = source?.content ?? ''
  form.category = (source?.category as CategoryValue | null) ?? ''
  form.platfrom = [...(source?.platfrom ?? [])]
  form.company = [...(source?.company ?? [])]
  form.tag = [...(source?.tag ?? [])]
  form.cover = source?.cover ?? ''
  form.images = [...(source?.images ?? [])]
  errorMsg.value = ''
}

watch(() => props.initial, populate, { immediate: true })

function togglePlatform(value: string) {
  form.platfrom = form.platfrom.includes(value)
    ? form.platfrom.filter((item) => item !== value)
    : [...form.platfrom, value]
}

function validate(): string {
  if (!form.name.trim() && !form.cn_name.trim() && !form.jp_name.trim() && !form.en_name.trim()) {
    return '请至少填写一个游戏名称'
  }
  for (const [label, value] of [
    ['主名称', form.name],
    ['中文名', form.cn_name],
    ['日文名', form.jp_name],
    ['英文名', form.en_name],
  ] as const) {
    if (value.trim().length > 50) return `${label}最多 50 个字符`
  }
  if (form.content.length > 20000) return '游戏简介最多 20000 个字符'
  if (!form.cover) return '请上传封面图或填写封面链接'
  return ''
}

function onSubmit() {
  const problem = validate()
  if (problem) {
    errorMsg.value = problem
    return
  }
  errorMsg.value = ''

  const payload: AddGalPayload = {
    name: form.name.trim() || form.cn_name.trim() || form.jp_name.trim() || form.en_name.trim(),
    cn_name: form.cn_name.trim(),
    jp_name: form.jp_name.trim(),
    en_name: form.en_name.trim(),
    content: form.content.trim() || undefined,
    company: form.company,
    category: form.category || undefined,
    cover: form.cover,
    images: form.images.length ? form.images : undefined,
    tag: form.tag,
    platfrom: form.platfrom,
  }
  emit('submit', payload)
}
</script>

<template>
  <form class="glass-card p-5 sm:p-7" @submit.prevent="onSubmit">
    <div class="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
      <!-- 左栏：封面与元信息 -->
      <aside class="space-y-5">
        <ImageUploader
          v-model="form.cover"
          label="封面图（必填）"
          hint="建议 2:3 竖图；支持 5MB 以内图片"
          ratio="cover"
        />

        <label class="block">
          <span class="label-base">分类</span>
          <select v-model="form.category" class="input-base mt-1.5">
            <option value="">未分类</option>
            <option v-for="item in CATEGORY_OPTIONS" :key="item" :value="item">
              {{ item }}
            </option>
          </select>
        </label>

        <div>
          <span class="label-base">平台</span>
          <div class="mt-1.5 flex flex-wrap gap-2">
            <button
              v-for="item in PLATFORM_OPTIONS"
              :key="item"
              type="button"
              class="chip"
              :class="{ 'chip-active': form.platfrom.includes(item) }"
              @click="togglePlatform(item)"
            >
              {{ item }}
            </button>
          </div>
        </div>

        <div>
          <span class="label-base">制作公司</span>
          <div class="mt-1.5">
            <TagInput v-model="form.company" placeholder="公司名，回车添加" />
          </div>
        </div>

        <div>
          <span class="label-base">标签</span>
          <div class="mt-1.5">
            <TagInput v-model="form.tag" placeholder="如：校园、悬疑、纯爱" />
          </div>
        </div>
      </aside>

      <!-- 右栏：名称与简介 -->
      <div class="min-w-0 space-y-5">
        <div class="grid gap-4 sm:grid-cols-2">
          <label class="block sm:col-span-2">
            <span class="label-base">主名称（卡片展示名）</span>
            <input
              v-model="form.name"
              maxlength="50"
              placeholder="例如：千恋＊万花"
              class="input-base mt-1.5"
            />
          </label>
          <label class="block">
            <span class="label-base">中文名</span>
            <input v-model="form.cn_name" maxlength="50" class="input-base mt-1.5" />
          </label>
          <label class="block">
            <span class="label-base">日文名</span>
            <input v-model="form.jp_name" maxlength="50" class="input-base mt-1.5" />
          </label>
          <label class="block sm:col-span-2">
            <span class="label-base">英文名</span>
            <input v-model="form.en_name" maxlength="50" class="input-base mt-1.5" />
          </label>
        </div>

        <label class="block">
          <span class="flex items-center justify-between">
            <span class="label-base">游戏简介</span>
            <span class="text-[10px] tabular-nums text-white/25">{{ form.content.length }} / 20000</span>
          </span>
          <textarea
            v-model="form.content"
            rows="10"
            maxlength="20000"
            placeholder="介绍故事背景、主要角色、玩法特色…"
            class="input-base mt-1.5 resize-y leading-relaxed"
          />
        </label>

        <ImageUploader
          v-model="form.images"
          multiple
          label="游戏截图"
          hint="最多 10 张，建议 16:10"
          :max="10"
          ratio="square"
        />

        <p
          v-if="errorMsg"
          class="rounded-xl border border-rose-400/25 bg-rose-500/10 px-3 py-2 text-xs leading-relaxed text-rose-200"
          role="alert"
        >
          {{ errorMsg }}
        </p>

        <div class="flex flex-wrap justify-end gap-3 border-t border-white/5 pt-5">
          <button type="button" class="btn-ghost" :disabled="submitting" @click="emit('cancel')">
            取消
          </button>
          <button type="submit" class="btn-primary px-6" :disabled="submitting">
            {{ submitting ? '提交中…' : mode === 'add' ? '发布游戏' : '保存修改' }}
          </button>
        </div>
      </div>
    </div>
  </form>
</template>