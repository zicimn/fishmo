<script setup lang="ts">
import type { AuthUser } from '~/types'
import { describeError } from '~/utils/api'

definePageMeta({ middleware: 'auth' })

const api = useApi()
const toast = useToast()
const confirm = useConfirm()
const { user, ready, clear: clearAuth, applyProfile } = useAuth()

const mounted = ref(false)
onMounted(() => {
  mounted.value = true
})

const form = reactive({
  username: '',
  email: '',
  bio: '',
  avatar: '',
  password: '',
  re_password: '',
})

let populatedFor: number | null = null
watch(
  () => user.value?.id,
  (id) => {
    if (!id || !user.value || populatedFor === id) return
    populatedFor = id
    form.username = user.value.username
    form.email = user.value.email ?? ''
    form.bio = user.value.bio ?? ''
    form.avatar = user.value.avatar ?? ''
    form.password = ''
    form.re_password = ''
  },
  { immediate: true },
)

const errorMsg = ref('')
const submitting = ref(false)
const deleting = ref(false)

useHead({ title: '编辑资料 · Fishmo' })

function validate(): string {
  if (form.username.trim().length < 2 || form.username.trim().length > 20) {
    return '用户名长度需在 2 到 20 个字符之间'
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
    return '请输入有效的邮箱地址'
  }
  if (form.bio.length > 500) return '简介最多 500 个字符'
  if (form.password || form.re_password) {
    if (form.password.length < 6 || form.password.length > 64) {
      return '密码长度需在 6 到 64 个字符之间'
    }
    if (form.password !== form.re_password) return '两次输入的密码不一致'
  }
  return ''
}

async function save() {
  const problem = validate()
  if (problem) {
    errorMsg.value = problem
    return
  }
  if (submitting.value) return
  errorMsg.value = ''
  submitting.value = true
  try {
    const payload: Record<string, unknown> = {
      username: form.username.trim(),
      email: form.email.trim(),
      bio: form.bio.trim(),
      avatar: form.avatar || null,
    }
    if (form.password) payload.password = form.password

    const data = await api.put<{ user: AuthUser }>('/api/v1/user/update', payload)
    applyProfile(data.user)
    form.password = ''
    form.re_password = ''
    toast.success('资料已更新')
  } catch (err) {
    errorMsg.value = describeError(err)
  } finally {
    submitting.value = false
  }
}

async function deleteAccount() {
  const ok = await confirm.confirm({
    title: '注销账号',
    message: '账号注销后将无法登录，并且不可恢复。若账号下仍有游戏或文章，需要先删除作品。',
    confirmText: '确认注销',
    danger: true,
  })
  if (!ok) return
  deleting.value = true
  try {
    await api.del('/api/v1/user/delete')
    clearAuth()
    toast.success('账号已注销')
    await navigateTo('/')
  } catch (err) {
    toast.error(describeError(err))
  } finally {
    deleting.value = false
  }
}
</script>

<template>
  <div class="mx-auto max-w-3xl px-4 pb-20 pt-10 sm:px-6">
    <nav class="flex items-center gap-2 text-[11px] text-white/30" aria-label="面包屑">
      <NuxtLink to="/manage" class="transition hover:text-white/70">个人中心</NuxtLink>
      <span>/</span>
      <span class="text-white/50">编辑资料</span>
    </nav>

    <header class="mt-4">
      <p class="section-kicker">PROFILE</p>
      <h1 class="mt-2 text-2xl font-semibold text-white">编辑个人资料</h1>
      <p class="mt-2 text-xs text-white/35">用户名与头像会展示在游戏、文章和评论旁边。</p>
    </header>

    <form
      v-if="mounted && ready && user"
      class="glass-card mt-6 p-6 sm:p-8"
      @submit.prevent="save"
    >
      <ImageUploader
        v-model="form.avatar"
        label="头像"
        hint="建议使用正方形图片，长边会被压缩到 1600px 以内"
        ratio="square"
      />

      <div class="mt-6 grid gap-5 sm:grid-cols-2">
        <label class="block">
          <span class="label-base">用户名</span>
          <input
            v-model="form.username"
            maxlength="20"
            autocomplete="username"
            class="input-base mt-1.5"
          />
          <span class="mt-1 block text-[10px] text-white/20">2–20 个字符，修改后需要重新登录其他设备。</span>
        </label>

        <label class="block">
          <span class="label-base">邮箱</span>
          <input
            v-model="form.email"
            type="email"
            autocomplete="email"
            class="input-base mt-1.5"
          />
        </label>

        <label class="block sm:col-span-2">
          <span class="flex items-center justify-between">
            <span class="label-base">个人简介</span>
            <span class="text-[10px] tabular-nums text-white/25">{{ form.bio.length }} / 500</span>
          </span>
          <textarea
            v-model="form.bio"
            rows="3"
            maxlength="500"
            placeholder="介绍一下自己，或者写一句喜欢的话…"
            class="input-base mt-1.5 resize-y leading-relaxed"
          />
        </label>
      </div>

      <div class="mt-8 border-t border-white/5 pt-6">
        <p class="text-xs font-medium text-white/60">修改密码</p>
        <p class="mt-1 text-[10px] text-white/25">不修改密码时请留空。</p>
        <div class="mt-4 grid gap-4 sm:grid-cols-2">
          <label class="block">
            <span class="label-base">新密码</span>
            <input
              v-model="form.password"
              type="password"
              autocomplete="new-password"
              placeholder="至少 6 位"
              class="input-base mt-1.5"
            />
          </label>
          <label class="block">
            <span class="label-base">确认新密码</span>
            <input
              v-model="form.re_password"
              type="password"
              autocomplete="new-password"
              class="input-base mt-1.5"
            />
          </label>
        </div>
      </div>

      <p
        v-if="errorMsg"
        class="mt-5 rounded-xl border border-rose-400/25 bg-rose-500/10 px-3 py-2 text-xs leading-relaxed text-rose-200"
        role="alert"
      >
        {{ errorMsg }}
      </p>

      <div class="mt-6 flex flex-wrap justify-end gap-3">
        <NuxtLink to="/manage" class="btn-ghost">返回个人中心</NuxtLink>
        <button type="submit" class="btn-primary px-6" :disabled="submitting">
          {{ submitting ? '保存中…' : '保存修改' }}
        </button>
      </div>
    </form>

    <section
      v-if="mounted && ready && user"
      class="mt-8 rounded-2xl border border-rose-400/15 bg-rose-500/[0.04] px-5 py-4"
    >
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p class="text-xs font-medium text-rose-100/80">注销账号</p>
          <p class="mt-1 text-[10px] leading-relaxed text-white/25">
            此操作不可恢复。若账号下仍有作品，请先在个人中心删除。
          </p>
        </div>
        <button type="button" class="btn-danger" :disabled="deleting" @click="deleteAccount">
          {{ deleting ? '处理中…' : '注销账号' }}
        </button>
      </div>
    </section>
  </div>
</template>