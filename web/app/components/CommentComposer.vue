<script setup lang="ts">
import type { CommentType, ReplyTarget } from '~/types/comment'
import { describeError } from '~/utils/api'

const props = withDefaults(
  defineProps<{
    targetId: number
    type: CommentType
    replyTo?: ReplyTarget | null
  }>(),
  { replyTo: null },
)

const emit = defineEmits<{
  (e: 'submitted', isReply: boolean): void
  (e: 'cancel-reply'): void
}>()

const api = useApi()
const toast = useToast()
const { user, ready, isLoggedIn, logout } = useAuth()
const { openAuth } = useAuthDialog()

const mounted = ref(false)
onMounted(() => {
  mounted.value = true
})

const text = ref('')
const submitting = ref(false)
const errorMsg = ref('')

const MAX_LENGTH = 2000
const textLength = computed(() => text.value.length)
const canSubmit = computed(
  () => !submitting.value && text.value.trim().length > 0 && textLength.value <= MAX_LENGTH,
)

const initial = computed(() => user.value?.username.trim().charAt(0) || '访')

watch(
  () => props.type,
  () => {
    text.value = ''
    errorMsg.value = ''
  },
)

watch(
  () => props.targetId,
  () => {
    text.value = ''
    errorMsg.value = ''
  },
)

async function submit() {
  if (submitting.value) return
  if (!isLoggedIn.value) {
    openAuth('login')
    return
  }
  const content = text.value.trim()
  if (!content) {
    errorMsg.value = '评论内容不能为空'
    return
  }
  if (content.length > MAX_LENGTH) {
    errorMsg.value = `评论最多 ${MAX_LENGTH} 字`
    return
  }

  submitting.value = true
  errorMsg.value = ''
  try {
    const body: Record<string, unknown> = { content }
    if (props.replyTo) {
      body.parent_id = props.replyTo.parentId
      if (props.replyTo.replyToId) body.reply_to_id = props.replyTo.replyToId
    }
    await api.post('/api/v1/comment/add', body, {
      game_id: props.targetId,
      type: props.type,
    })
    const wasReply = props.replyTo !== null
    text.value = ''
    toast.success(wasReply ? '回复已发布' : '评论已发布')
    emit('submitted', wasReply)
  } catch (err) {
    errorMsg.value = describeError(err)
  } finally {
    submitting.value = false
  }
}

async function onLogout() {
  await logout()
  text.value = ''
  emit('cancel-reply')
  toast.success('已退出登录')
}
</script>

<template>
  <section class="glass-panel p-5" aria-label="发表评论">
    <div v-if="!mounted || !ready" class="flex animate-pulse items-center gap-3" aria-hidden="true">
      <div class="h-9 w-9 rounded-full bg-white/10" />
      <div class="space-y-2">
        <div class="h-3 w-28 rounded bg-white/10" />
        <div class="h-2.5 w-20 rounded bg-white/5" />
      </div>
    </div>

    <div
      v-else-if="!isLoggedIn"
      class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
    >
      <div class="flex items-center gap-3">
        <span
          class="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-white/[0.06] text-xs text-white/40 ring-1 ring-white/10"
          aria-hidden="true"
        >
          ?
        </span>
        <div class="min-w-0">
          <p class="text-xs font-medium text-white/70">登录后参与评论</p>
          <p class="mt-0.5 text-[11px] text-white/35">评论会以账号昵称展示。</p>
        </div>
      </div>
      <button type="button" class="btn-primary shrink-0 px-5" @click="openAuth('login')">
        登录 / 注册
      </button>
    </div>

    <form v-else class="space-y-3" @submit.prevent="submit">
      <div class="flex flex-wrap items-center gap-2.5">
        <img
          v-if="user?.avatar"
          :src="user.avatar"
          :alt="user.username"
          class="h-9 w-9 rounded-full object-cover ring-1 ring-white/15"
        />
        <span
          v-else
          class="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gradient-to-br from-sky-500/30 to-fuchsia-500/30 text-xs font-medium text-white/80 ring-1 ring-white/10"
          aria-hidden="true"
        >
          {{ initial }}
        </span>
        <div class="min-w-0">
          <p class="truncate text-xs font-medium text-white/80">{{ user?.username }}</p>
          <p class="truncate text-[11px] text-white/30">{{ user?.email }}</p>
        </div>
        <button
          type="button"
          class="ml-auto text-[11px] text-white/35 transition hover:text-white/70"
          @click="onLogout"
        >
          退出
        </button>
      </div>

      <div
        v-if="replyTo"
        class="flex items-center gap-2 rounded-lg border border-sky-300/20 bg-sky-400/10 px-3 py-1.5 text-[11px] text-sky-100/80"
      >
        <span>回复 {{ replyTo.name }}</span>
        <button
          type="button"
          class="ml-auto text-sky-100/50 transition hover:text-white"
          @click="emit('cancel-reply')"
        >
          取消
        </button>
      </div>

      <textarea
        v-model="text"
        rows="4"
        :maxlength="MAX_LENGTH"
        placeholder="写下你的想法…（Ctrl + Enter 发表）"
        class="block w-full resize-y rounded-xl border border-white/10 bg-slate-950/40 px-3.5 py-3 text-sm leading-relaxed text-white/85 outline-none transition placeholder:text-white/20 focus:border-sky-300/30 focus:ring-2 focus:ring-sky-400/15"
        @keydown.ctrl.enter.prevent="submit"
        @keydown.meta.enter.prevent="submit"
      />

      <div class="flex flex-wrap items-center justify-between gap-3">
        <p class="text-[11px] tabular-nums text-white/30">{{ textLength }} / {{ MAX_LENGTH }}</p>
        <button type="submit" class="btn-primary px-5" :disabled="!canSubmit">
          {{ submitting ? '发表中…' : replyTo ? '发表回复' : '发表评论' }}
        </button>
      </div>
    </form>

    <p
      v-if="errorMsg"
      class="mt-3 rounded-xl border border-rose-400/25 bg-rose-500/10 px-3 py-2 text-xs leading-relaxed text-rose-200"
      role="alert"
    >
      {{ errorMsg }}
    </p>
  </section>
</template>