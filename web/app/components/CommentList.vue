<script setup lang="ts">
import type { CommentItem, PageData } from '~/types'
import type { CommentType, ReplyTarget } from '~/types/comment'
import { describeError } from '~/utils/api'
import { formatDateTime } from '~/utils/date'

const props = defineProps<{
  targetId: number
  type: CommentType
}>()

const api = useApi()
const toast = useToast()
const confirm = useConfirm()
const { user, isLoggedIn } = useAuth()

const page = ref(1)
const size = 10
const replyTo = ref<ReplyTarget | null>(null)
const editingId = ref<number | null>(null)
const editingText = ref('')
const savingEdit = ref(false)

const mounted = ref(false)
onMounted(() => {
  mounted.value = true
})

const { data, pending, error, refresh } = await useAsyncData<PageData<CommentItem>>(
  () => `comments-${props.type}-${props.targetId}-${page.value}`,
  () =>
    api.get<PageData<CommentItem>>(`/api/v1/comment/${props.targetId}`, {
      type: props.type,
      page: page.value,
      size,
    }),
  {
    watch: [page, () => props.targetId, () => props.type],
    default: () => ({ total: 0, items: [] }),
  },
)

const items = computed(() => data.value?.items ?? [])
const total = computed(() => data.value?.total ?? 0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / size)))
const showSkeleton = computed(() => pending.value && items.value.length === 0)

watch(
  () => [props.targetId, props.type],
  () => {
    page.value = 1
    replyTo.value = null
    editingId.value = null
  },
)

function initial(name: string): string {
  return name.trim().charAt(0) || '访'
}

function canManage(comment: CommentItem): boolean {
  if (!mounted.value || !user.value) return false
  return user.value.id === comment.author_id || user.value.is_admin
}

function startReplyTop(comment: CommentItem) {
  replyTo.value = {
    parentId: comment.id,
    replyToId: null,
    name: comment.author.username,
  }
  scrollToComposer()
}

function startReplyNested(top: CommentItem, reply: CommentItem) {
  replyTo.value = {
    parentId: top.id,
    replyToId: reply.id,
    name: reply.author.username,
  }
  scrollToComposer()
}

function scrollToComposer() {
  if (!import.meta.client) return
  const el = document.getElementById('comment-composer')
  el?.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

function onSubmitted(isReply: boolean) {
  replyTo.value = null
  if (!isReply && page.value !== 1) {
    page.value = 1
    return
  }
  refresh()
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
  if (savingEdit.value) return
  savingEdit.value = true
  try {
    await api.put('/api/v1/comment/edit', { content }, { comment_id: comment.id })
    toast.success('评论已更新')
    cancelEdit()
    refresh()
  } catch (err) {
    toast.error(describeError(err))
  } finally {
    savingEdit.value = false
  }
}

async function removeComment(comment: CommentItem) {
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
    refresh()
  } catch (err) {
    toast.error(describeError(err))
  }
}
</script>

<template>
  <section class="mt-10" aria-labelledby="comments-heading">
    <div class="mb-4 flex items-baseline justify-between">
      <h2 id="comments-heading" class="text-sm font-medium tracking-wide text-white/70">
        评论
        <span v-if="total" class="ml-1 text-[11px] text-white/30">{{ total }}</span>
      </h2>
      <span class="text-[11px] text-white/25">
        {{ totalPages > 1 ? `第 ${page} / ${totalPages} 页` : '全部评论' }}
      </span>
    </div>

    <div id="comment-composer">
      <CommentComposer
        :target-id="targetId"
        :type="type"
        :reply-to="replyTo"
        @submitted="onSubmitted"
        @cancel-reply="replyTo = null"
      />
    </div>

    <div v-if="showSkeleton" class="mt-4 space-y-3" aria-hidden="true">
      <div
        v-for="n in 3"
        :key="n"
        class="animate-pulse rounded-2xl border border-white/10 bg-white/[0.05] p-5 backdrop-blur-2xl"
      >
        <div class="flex items-center gap-3">
          <div class="h-9 w-9 rounded-full bg-white/10" />
          <div class="space-y-2">
            <div class="h-3 w-24 rounded bg-white/10" />
            <div class="h-2.5 w-16 rounded bg-white/5" />
          </div>
        </div>
        <div class="mt-4 h-3 w-full rounded bg-white/5" />
        <div class="mt-2 h-3 w-2/3 rounded bg-white/5" />
      </div>
    </div>

    <div
      v-else-if="error && items.length === 0"
      class="mt-4 rounded-2xl border border-white/10 bg-white/[0.05] px-5 py-10 text-center backdrop-blur-2xl"
    >
      <p class="text-xs text-white/50">评论暂时加载失败</p>
      <button type="button" class="btn-ghost mt-4 px-4 py-1.5" @click="refresh()">重试</button>
    </div>

    <div
      v-else-if="items.length === 0"
      class="mt-4 rounded-2xl border border-white/10 bg-white/[0.05] px-5 py-10 text-center backdrop-blur-2xl"
    >
      <p class="text-xs text-white/40">还没有评论，来抢沙发吧。</p>
    </div>

    <ul v-else class="mt-4 space-y-3">
      <li
        v-for="comment in items"
        :key="comment.id"
        class="rounded-2xl border border-white/10 bg-white/[0.05] p-5 backdrop-blur-2xl"
      >
        <div class="flex items-center gap-3">
          <img
            v-if="comment.author.avatar"
            :src="comment.author.avatar"
            :alt="comment.author.username"
            class="h-9 w-9 rounded-full object-cover ring-1 ring-white/15"
            loading="lazy"
          />
          <span
            v-else
            class="grid h-9 w-9 place-items-center rounded-full bg-gradient-to-br from-sky-500/30 to-fuchsia-500/30 text-xs font-medium text-white/80 ring-1 ring-white/10"
            aria-hidden="true"
          >
            {{ initial(comment.author.username) }}
          </span>
          <div class="min-w-0">
            <p class="truncate text-xs font-medium text-white/80">
              {{ comment.author.username }}
            </p>
            <time class="text-[11px] text-white/30" :datetime="comment.created_at">
              {{ formatDateTime(comment.created_at) }}
            </time>
          </div>
        </div>

        <div v-if="editingId === comment.id" class="mt-3 space-y-2">
          <textarea
            v-model="editingText"
            rows="3"
            maxlength="2000"
            class="block w-full resize-y rounded-xl border border-white/10 bg-slate-950/40 px-3 py-2 text-sm text-white/85 outline-none focus:border-sky-300/30"
          />
          <div class="flex justify-end gap-2">
            <button type="button" class="btn-ghost px-3 py-1.5" @click="cancelEdit">取消</button>
            <button
              type="button"
              class="btn-primary px-4 py-1.5"
              :disabled="savingEdit"
              @click="saveEdit(comment)"
            >
              {{ savingEdit ? '保存中…' : '保存' }}
            </button>
          </div>
        </div>
        <div
          v-else
          class="comment-content mt-3 text-sm leading-relaxed text-white/70"
          v-html="comment.content"
        />

        <div class="mt-2 flex flex-wrap items-center justify-end gap-1">
          <button
            v-if="mounted && isLoggedIn"
            type="button"
            class="rounded-full px-2.5 py-1 text-[11px] text-white/35 transition hover:bg-white/[0.06] hover:text-sky-200"
            @click="startReplyTop(comment)"
          >
            回复
          </button>
          <template v-if="canManage(comment)">
            <button
              type="button"
              class="rounded-full px-2.5 py-1 text-[11px] text-white/35 transition hover:bg-white/[0.06] hover:text-white/75"
              @click="startEdit(comment)"
            >
              编辑
            </button>
            <button
              type="button"
              class="rounded-full px-2.5 py-1 text-[11px] text-white/35 transition hover:bg-rose-500/10 hover:text-rose-200"
              @click="removeComment(comment)"
            >
              删除
            </button>
          </template>
        </div>

        <div
          v-if="comment.replies?.length"
          class="mt-4 space-y-2 border-l border-white/10 pl-4"
        >
          <div
            v-for="reply in comment.replies"
            :key="reply.id"
            class="rounded-xl bg-white/[0.04] px-3 py-2.5"
          >
            <div class="flex flex-wrap items-center gap-x-2 gap-y-0.5 text-[11px]">
              <span class="font-medium text-white/70">{{ reply.author.username }}</span>
              <span v-if="reply.reply_to_username" class="text-white/30">
                回复 {{ reply.reply_to_username }}
              </span>
              <time class="ml-auto text-white/25" :datetime="reply.created_at">
                {{ formatDateTime(reply.created_at) }}
              </time>
            </div>

            <div v-if="editingId === reply.id" class="mt-2 space-y-2">
              <textarea
                v-model="editingText"
                rows="2"
                maxlength="2000"
                class="block w-full resize-y rounded-lg border border-white/10 bg-slate-950/40 px-2.5 py-1.5 text-xs text-white/85 outline-none focus:border-sky-300/30"
              />
              <div class="flex justify-end gap-2">
                <button type="button" class="btn-ghost px-2.5 py-1" @click="cancelEdit">取消</button>
                <button
                  type="button"
                  class="btn-primary px-3 py-1"
                  :disabled="savingEdit"
                  @click="saveEdit(reply)"
                >
                  保存
                </button>
              </div>
            </div>
            <div
              v-else
              class="comment-content mt-1.5 text-xs leading-relaxed text-white/60"
              v-html="reply.content"
            />

            <div class="mt-1 flex items-center justify-end gap-1">
              <button
                v-if="mounted && isLoggedIn"
                type="button"
                class="rounded-full px-2 py-0.5 text-[10px] text-white/30 transition hover:bg-white/[0.06] hover:text-sky-200"
                @click="startReplyNested(comment, reply)"
              >
                回复
              </button>
              <template v-if="canManage(reply)">
                <button
                  type="button"
                  class="rounded-full px-2 py-0.5 text-[10px] text-white/30 transition hover:text-white/70"
                  @click="startEdit(reply)"
                >
                  编辑
                </button>
                <button
                  type="button"
                  class="rounded-full px-2 py-0.5 text-[10px] text-white/30 transition hover:text-rose-200"
                  @click="removeComment(reply)"
                >
                  删除
                </button>
              </template>
            </div>
          </div>
        </div>
      </li>
    </ul>

    <PaginationBar v-model:page="page" :total-pages="totalPages" />
  </section>
</template>