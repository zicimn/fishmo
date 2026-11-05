<script setup lang="ts">
import type { ArticleDetail, ArticlePayload } from '~/types'
import { ARTICLE_CATEGORY_OPTIONS } from '~/types'
import { renderMarkdown } from '~/utils/markdown'

const props = withDefaults(
  defineProps<{
    mode?: 'add' | 'edit'
    initial?: Partial<ArticleDetail> | null
    submitting?: boolean
  }>(),
  { mode: 'add', initial: null, submitting: false },
)

const emit = defineEmits<{
  (e: 'submit', payload: ArticlePayload): void
  (e: 'cancel'): void
}>()

const DRAFT_KEY = 'fishmo_article_draft_v1'

const form = reactive({
  title: '',
  content: '',
  categories: [] as string[],
  tag: [] as string[],
  cover: '',
  images: [] as string[],
})

const errorMsg = ref('')
const showPreview = ref(false)
const textarea = ref<HTMLTextAreaElement | null>(null)
const draftAvailable = ref(false)
let draftTimer: ReturnType<typeof setTimeout> | null = null

function populate() {
  const source = props.initial
  form.title = source?.title ?? ''
  form.content = source?.content ?? ''
  form.categories = [...(source?.category ?? [])]
  form.tag = [...(source?.tag ?? [])]
  form.cover = source?.cover ?? ''
  form.images = [...(source?.images ?? [])]
  errorMsg.value = ''
}

watch(() => props.initial, populate, { immediate: true })

onMounted(() => {
  if (props.mode !== 'add' || !import.meta.client) return
  try {
    if (localStorage.getItem(DRAFT_KEY)) draftAvailable.value = true
  } catch {
    // 忽略隐私模式
  }
})

watch(
  () => [form.title, form.content, form.categories.join(','), form.tag.join(',')],
  () => {
    if (props.mode !== 'add' || !import.meta.client) return
    if (!form.title.trim() && !form.content.trim()) return
    if (draftTimer) clearTimeout(draftTimer)
    draftTimer = setTimeout(() => {
      try {
        localStorage.setItem(
          DRAFT_KEY,
          JSON.stringify({
            title: form.title,
            content: form.content,
            categories: form.categories,
            tag: form.tag,
          }),
        )
      } catch {
        // 草稿不是关键路径，写入失败直接忽略
      }
    }, 1500)
  },
)

onBeforeUnmount(() => {
  if (draftTimer) clearTimeout(draftTimer)
})

function restoreDraft() {
  if (!import.meta.client) return
  try {
    const raw = localStorage.getItem(DRAFT_KEY)
    if (!raw) return
    const parsed = JSON.parse(raw) as {
      title?: string
      content?: string
      categories?: string[]
      tag?: string[]
    }
    form.title = parsed.title ?? ''
    form.content = parsed.content ?? ''
    form.categories = Array.isArray(parsed.categories) ? parsed.categories : []
    form.tag = Array.isArray(parsed.tag) ? parsed.tag : []
    draftAvailable.value = false
  } catch {
    clearDraft()
  }
}

function clearDraft() {
  draftAvailable.value = false
  if (!import.meta.client) return
  try {
    localStorage.removeItem(DRAFT_KEY)
  } catch {
    // 忽略
  }
}

defineExpose({ clearDraft })

function toggleCategory(value: string) {
  form.categories = form.categories.includes(value)
    ? form.categories.filter((item) => item !== value)
    : [...form.categories, value]
}

function insert(before: string, after = '', placeholder = '') {
  const el = textarea.value
  if (!el) return
  const start = el.selectionStart
  const end = el.selectionEnd
  const selected = form.content.slice(start, end) || placeholder
  form.content =
    form.content.slice(0, start) + before + selected + after + form.content.slice(end)
  nextTick(() => {
    el.focus()
    el.setSelectionRange(start + before.length, start + before.length + selected.length)
  })
}

const toolbar = [
  { label: 'H2', before: '\n## ', after: '\n', placeholder: '小标题' },
  { label: 'B', before: '**', after: '**', placeholder: '加粗文字' },
  { label: 'I', before: '*', after: '*', placeholder: '斜体文字' },
  { label: '引用', before: '\n> ', after: '\n', placeholder: '引用内容' },
  { label: '代码', before: '`', after: '`', placeholder: 'code' },
  { label: '链接', before: '[', after: '](https://)', placeholder: '链接文字' },
  { label: '列表', before: '\n- ', after: '', placeholder: '列表项' },
]

const previewHtml = computed(() => renderMarkdown(form.content))

function validate(): string {
  if (!form.title.trim()) return '请填写文章标题'
  if (form.title.trim().length > 255) return '标题最多 255 个字符'
  if (!form.content.trim()) return '文章内容不能为空'
  return ''
}

function onSubmit() {
  const problem = validate()
  if (problem) {
    errorMsg.value = problem
    return
  }
  errorMsg.value = ''

  const payload: ArticlePayload = {
    title: form.title.trim(),
    content: form.content,
    category: form.categories.join(','),
    tag: form.tag,
    cover: form.cover || undefined,
    images: form.images.length ? form.images : undefined,
  }
  emit('submit', payload)
}
</script>

<template>
  <form class="glass-card p-5 sm:p-7" @submit.prevent="onSubmit">
    <div class="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
      <aside class="space-y-5">
        <ImageUploader
          v-model="form.cover"
          label="封面图"
          hint="建议 16:10；不填则使用第一张插图"
          ratio="wide"
        />

        <div>
          <span class="label-base">分类</span>
          <div class="mt-1.5 flex flex-wrap gap-2">
            <button
              v-for="item in ARTICLE_CATEGORY_OPTIONS"
              :key="item"
              type="button"
              class="chip"
              :class="{ 'chip-active': form.categories.includes(item) }"
              @click="toggleCategory(item)"
            >
              {{ item }}
            </button>
          </div>
        </div>

        <div>
          <span class="label-base">标签</span>
          <div class="mt-1.5">
            <TagInput v-model="form.tag" placeholder="标签，回车添加" />
          </div>
        </div>

        <ImageUploader
          v-model="form.images"
          multiple
          label="插图"
          hint="最多 10 张，文章底部展示"
          :max="10"
          ratio="square"
        />
      </aside>

      <div class="min-w-0 space-y-4">
        <label class="block">
          <span class="label-base">标题</span>
          <input
            v-model="form.title"
            maxlength="255"
            placeholder="给这篇文章一个标题"
            class="input-base mt-1.5 text-base"
          />
        </label>

        <div>
          <div class="flex flex-wrap items-center justify-between gap-2">
            <span class="label-base">正文（Markdown）</span>
            <div class="flex items-center gap-2">
              <button
                v-if="draftAvailable && mode === 'add'"
                type="button"
                class="text-[11px] text-sky-200/60 transition hover:text-white"
                @click="restoreDraft"
              >
                恢复草稿
              </button>
              <button
                type="button"
                class="rounded-full border border-white/10 px-3 py-1 text-[11px] transition"
                :class="
                  showPreview
                    ? 'bg-white/[0.12] text-white'
                    : 'text-white/40 hover:text-white/70'
                "
                @click="showPreview = !showPreview"
              >
                {{ showPreview ? '继续编辑' : '预览' }}
              </button>
            </div>
          </div>

          <div v-if="!showPreview" class="mt-1.5 overflow-hidden rounded-xl border border-white/10 bg-slate-950/50">
            <div class="flex flex-wrap items-center gap-1 border-b border-white/5 px-2 py-1.5">
              <button
                v-for="item in toolbar"
                :key="item.label"
                type="button"
                class="rounded-md px-2 py-1 text-[11px] text-white/45 transition hover:bg-white/[0.08] hover:text-white"
                @click="insert(item.before, item.after, item.placeholder)"
              >
                {{ item.label }}
              </button>
            </div>
            <textarea
              ref="textarea"
              v-model="form.content"
              rows="18"
              placeholder="支持 Markdown：# 标题、**加粗**、[链接](https://…)、- 列表…"
              class="block w-full resize-y bg-transparent px-3.5 py-3 font-mono text-sm leading-relaxed text-white/85 outline-none placeholder:text-white/20"
            />
          </div>

          <div
            v-else
            class="article-content mt-1.5 max-h-[42rem] overflow-y-auto rounded-xl border border-white/10 bg-slate-950/40 px-4 py-4"
          >
            <div v-if="form.content.trim()" v-html="previewHtml" />
            <p v-else class="text-xs text-white/25">还没有内容可预览。</p>
          </div>
        </div>

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
            {{ submitting ? '提交中…' : mode === 'add' ? '发布文章' : '保存修改' }}
          </button>
        </div>
      </div>
    </div>
  </form>
</template>