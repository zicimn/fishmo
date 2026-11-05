<script setup lang="ts">
import type { CommentItem, PageData } from '~/types'
import { describeError } from '~/utils/api'
import { formatDateTime } from '~/utils/date'

const api = useApi()
const toast = useToast()
const confirm = useConfirm()
const { user } = useAuth()

const page = ref(1)
const size = 10

const { data, pending, error, refresh } = await useAsyncData<PageData<CommentItem>>(
  () => `manage-comments-${user.value?.id ?? 0}-${page.value}`,
  () =>
    api.get<PageData<CommentItem>>(`/api/v1/comment/user/${user.value?.id}`, {
      page: page.value,
      size,
    }),
  {
    server: false,
    watch: [page, () => user.value?.id],
    default: () => ({ total: 0, items: [] }),
  },
)

const comments = computed(() => data.value?.items ?? [])
const total = computed(() => data.value?.total ?? 0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / size)))

const editingId = ref<number | null>(null)
const editingText = ref('')
const saving = ref(false)

function targetLink(comment: CommentItem): string {
  return comment.receive_type === 0
    ? `/article/${comment.receive_id}`
    : `/galgame/${comment.receive_id}`
}

function targetLabel(comment: CommentItem): string {
  return comment.receive_type === 0 ? '文章' : '游戏'
}

function startEdit(comment: CommentItem) {
  editingId.value = comment.id
  editingText.value = stripHtml(comment.content)
}

function stripHtml(html: string): string {
  if (!import.meta.client) return html
  const div = document.createElement('div')
  div.innerHTML = html
  return div.textContent ?? ''
}

function cancelEdit() {
  editingId.value = null
  editingText.value = ''
}

async function saveEdit(comment: CommentItem) {
  const content = editingText.value.trim()
  if (!content) {
    toast.error('评论内容不能为空')
    return
  }
  if (saving.value) return
  saving.value = true
  try {
    await api.put('/api/v1/comment/edit', { content }, { comment_id: comment.id })
    toast.success('评论已更新')
    cancelEdit()
    refresh()
  } catch (err) {
    toast.error(describeError(err))
  } finally {
    saving.value = false
  }
}

async function remove(comment: CommentItem) {
  const ok = await confirm.confirm({
    title: '删除评论',
    message: '删除后不可恢复，楼层下的回复也会一并删除。',
    confirmText: '确认删除',
    danger: true,
  })
  if (!ok) return
  try {
    await api.del('/api/v1/comment/delete', { comment_id: comment.id })
    toast.success('评论已删除')
    if (comments.value.length === 1 && page.value > 1) page.value -= 1
    else refresh()
  } catch (err) {
    toast.error(describeError(err))
  }
}
</script>

<template>
  <section>
    <div class="flex flex-wrap items-center justify-between gap-3">
      <p class="text-[11px] text-white/35">
        共 <span class="tabular-nums text-white/60">{{ total }}</span> 条评论
      </p>
      <p class="text-[10px] text-white/25">删除评论不可恢复，请谨慎操作。</p>
    </div>

    <div v-if="pending && comments.length === 0" class="mt-5 space-y-2">
      <div
        v-for="n in 4"
        :key="n"
        class="h-20 animate-pulse rounded-2xl border border-white/10 bg-white/[0.05]"
      />
    </div>

    <div v-else-if="error && comments.length === 0" class="glass-panel mt-5 px-5 py-10 text-center">
      <p class="text-xs text-white/45">评论列表加载失败</p>
      <button type="button" class="btn-ghost mt-4 px-4 py-1.5" @click="refresh()">重试</button>
    </div>

    <div v-else-if="comments.length === 0" class="glass-panel mt-5 px-5 py-12 text-center">
      <p class="text-xs text-white/40">你还没有发表过评论。</p>
    </div>

    <ul v-else class="mt-5 space-y-2">
      <li v-for="comment in comments" :key="comment.id" class="glass-panel p-4">
        <div class="flex flex-wrap items-center gap-2 text-[10px] text-white/30">
          <NuxtLink :to="targetLink(comment)" class="text-sky-200/60 transition hover:text-sky-100">
            {{ targetLabel(comment) }} #{{ comment.receive_id }}
          </NuxtLink>
          <span v-if="comment.parent_id" class="text-white/20">· 回复</span>
          <time class="ml-auto" :datetime="comment.updated_at">
            {{ formatDateTime(comment.updated_at) }}
          </time>
        </div>

        <div v-if="editingId === comment.id" class="mt-2.5 space-y-2">
          <textarea
            v-model="editingText"
            rows="3"
            maxlength="2000"
            class="block w-full resize-y rounded-xl border border-white/10 bg-slate-950/50 px-3 py-2 text-xs leading-relaxed text-white/80 outline-none focus:border-sky-300/30"
          />
          <div class="flex justify-end gap-2">
            <button type="button" class="btn-ghost px-3 py-1.5" @click="cancelEdit">取消</button>
            <button
              type="button"
              class="btn-primary px-4 py-1.5"
              :disabled="saving"
              @click="saveEdit(comment)"
            >
              {{ saving ? '保存中…' : '保存' }}
            </button>
          </div>
        </div>
        <div v-else class="comment-content mt-2 text-xs leading-relaxed text-white/60" v-html="comment.content" />

        <div class="mt-2 flex justify-end gap-1.5">
          <NuxtLink
            :to="targetLink(comment)"
            class="rounded-full px-2.5 py-1 text-[10px] text-white/30 transition hover:text-sky-200"
          >
            查看原帖
          </NuxtLink>
          <button
            type="button"
            class="rounded-full px-2.5 py-1 text-[10px] text-white/30 transition hover:text-white/75"
            @click="startEdit(comment)"
          >
            编辑
          </button>
          <button
            type="button"
            class="rounded-full px-2.5 py-1 text-[10px] text-white/30 transition hover:text-rose-200"
            @click="remove(comment)"
          >
            删除
          </button>
        </div>
      </li>
    </ul>

    <PaginationBar v-model:page="page" :total-pages="totalPages" />
  </section>
</template>