<script setup lang="ts">
import type { AuthMode } from '~/composables/useAuthDialog'
import { describeError } from '~/utils/api'

const props = withDefaults(
  defineProps<{
    mode: AuthMode
  }>(),
  {},
)

const emit = defineEmits<{
  (e: 'update:mode', value: AuthMode): void
  (e: 'success'): void
}>()

const { login, register, sendCode } = useAuth()
const toast = useToast()

const loading = ref(false)
const errorMsg = ref('')
const hintMsg = ref('')

const loginForm = reactive({ username: '', password: '' })
const regForm = reactive({
  email: '',
  code: '',
  username: '',
  password: '',
  re_password: '',
})

const sendingCode = ref(false)
const countdown = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const emailInput = ref<HTMLInputElement | null>(null)
const usernameInput = ref<HTMLInputElement | null>(null)

function stopTimer() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

function startCountdown(seconds = 60) {
  stopTimer()
  countdown.value = Math.max(1, seconds)
  timer = setInterval(() => {
    countdown.value -= 1
    if (countdown.value <= 0) stopTimer()
  }, 1000)
}

onBeforeUnmount(stopTimer)

watch(
  () => props.mode,
  async (mode) => {
    errorMsg.value = ''
    hintMsg.value = ''
    await nextTick()
    if (mode === 'login') usernameInput.value?.focus()
    else emailInput.value?.focus()
  },
)

function switchMode(next: AuthMode) {
  if (props.mode === next) return
  errorMsg.value = ''
  hintMsg.value = ''
  emit('update:mode', next)
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

async function onLogin() {
  if (loading.value) return
  errorMsg.value = ''
  hintMsg.value = ''

  const username = loginForm.username.trim()
  if (username.length < 2) {
    errorMsg.value = '用户名至少 2 个字符'
    return
  }
  if (!loginForm.password) {
    errorMsg.value = '请填写密码'
    return
  }

  loading.value = true
  try {
    await login(username, loginForm.password)
    loginForm.password = ''
    toast.success('登录成功')
    emit('success')
  } catch (err) {
    errorMsg.value = describeError(err)
  } finally {
    loading.value = false
  }
}

// 与后端 Account 的约束保持一致；提前拦一遍，用户才能看到中文原因
function validateRegister(): string {
  const email = regForm.email.trim()
  const username = regForm.username.trim()

  if (!EMAIL_RE.test(email)) return '请填写正确的邮箱地址'
  if (!/^\d{6}$/.test(regForm.code.trim())) return '验证码是 6 位数字'
  if (username.length < 2) return '用户名至少 2 个字符'
  if (username.length > 20) return '用户名最多 20 个字符'
  if (/\s/.test(username)) return '用户名不能包含空白字符'
  if (regForm.password.length < 6) return '密码至少 6 位'
  if (regForm.password.length > 64) return '密码最多 64 位'
  if (regForm.password !== regForm.re_password) return '两次输入的密码不一致'
  return ''
}

async function onRegister() {
  if (loading.value) return
  errorMsg.value = ''
  hintMsg.value = ''

  const problem = validateRegister()
  if (problem) {
    errorMsg.value = problem
    return
  }

  loading.value = true
  try {
    await register({
      email: regForm.email.trim(),
      code: regForm.code.trim(),
      username: regForm.username.trim(),
      password: regForm.password,
      re_password: regForm.re_password,
    })
    regForm.password = ''
    regForm.re_password = ''
    toast.success('注册成功，已自动登录')
    emit('success')
  } catch (err) {
    errorMsg.value = describeError(err)
  } finally {
    loading.value = false
  }
}

async function onSendCode() {
  if (sendingCode.value || countdown.value > 0) return
  errorMsg.value = ''
  hintMsg.value = ''

  const email = regForm.email.trim()
  if (!EMAIL_RE.test(email)) {
    errorMsg.value = '请先填写正确的邮箱地址'
    return
  }

  sendingCode.value = true
  try {
    const data = await sendCode(email)
    const minutes = Math.max(1, Math.ceil((data?.expires_in ?? 300) / 60))
    hintMsg.value = `验证码已发送，${minutes} 分钟内有效`
    startCountdown(60)
  } catch (err) {
    errorMsg.value = describeError(err)
  } finally {
    sendingCode.value = false
  }
}
</script>

<template>
  <div>
    <div class="grid grid-cols-2 gap-1 rounded-xl border border-white/10 bg-white/[0.04] p-1">
      <button
        v-for="tab in ([
          { key: 'login', label: '登录' },
          { key: 'register', label: '注册' },
        ] as const)"
        :key="tab.key"
        type="button"
        class="rounded-lg px-3 py-2 text-xs transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-300"
        :class="
          mode === tab.key
            ? 'bg-white/[0.12] text-white shadow-sm'
            : 'text-white/45 hover:text-white/70'
        "
        @click="switchMode(tab.key)"
      >
        {{ tab.label }}
      </button>
    </div>

    <p
      v-if="errorMsg"
      class="mt-4 rounded-xl border border-rose-400/25 bg-rose-500/10 px-3 py-2 text-xs leading-relaxed text-rose-200"
      role="alert"
    >
      {{ errorMsg }}
    </p>
    <p
      v-if="hintMsg"
      class="mt-4 rounded-xl border border-sky-400/25 bg-sky-500/10 px-3 py-2 text-xs leading-relaxed text-sky-100/80"
    >
      {{ hintMsg }}
    </p>

    <form v-if="mode === 'login'" class="mt-5 space-y-4" @submit.prevent="onLogin">
      <label class="block">
        <span class="label-base">用户名</span>
        <input
          ref="usernameInput"
          v-model="loginForm.username"
          autocomplete="username"
          maxlength="20"
          placeholder="你的用户名"
          class="input-base mt-1.5"
        />
      </label>

      <label class="block">
        <span class="label-base">密码</span>
        <input
          v-model="loginForm.password"
          type="password"
          autocomplete="current-password"
          placeholder="••••••••"
          class="input-base mt-1.5"
        />
      </label>

      <button type="submit" :disabled="loading" class="btn-primary w-full py-2.5">
        {{ loading ? '登录中…' : '登录' }}
      </button>
    </form>

    <form v-else class="mt-5 space-y-4" @submit.prevent="onRegister">
      <label class="block">
        <span class="label-base">邮箱</span>
        <div class="mt-1.5 flex gap-2">
          <input
            ref="emailInput"
            v-model="regForm.email"
            type="email"
            autocomplete="email"
            placeholder="you@example.com"
            class="input-base min-w-0 flex-1"
          />
          <button
            type="button"
            :disabled="sendingCode || countdown > 0"
            class="shrink-0 rounded-xl border border-white/15 bg-white/[0.06] px-3 py-2 text-[11px] text-white/70 transition hover:bg-white/[0.12] hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
            @click="onSendCode"
          >
            {{ countdown > 0 ? `${countdown}s 后重发` : sendingCode ? '发送中…' : '获取验证码' }}
          </button>
        </div>
      </label>

      <div class="grid grid-cols-2 gap-3">
        <label class="block">
          <span class="label-base">验证码</span>
          <input
            v-model="regForm.code"
            inputmode="numeric"
            maxlength="6"
            autocomplete="one-time-code"
            placeholder="6 位数字"
            class="input-base mt-1.5 tracking-[0.2em] placeholder:tracking-normal"
          />
        </label>
        <label class="block">
          <span class="label-base">用户名</span>
          <input
            v-model="regForm.username"
            maxlength="20"
            autocomplete="nickname"
            placeholder="评论里显示的名字"
            class="input-base mt-1.5"
          />
        </label>
      </div>

      <label class="block">
        <span class="label-base">密码</span>
        <input
          v-model="regForm.password"
          type="password"
          autocomplete="new-password"
          maxlength="64"
          placeholder="至少 6 位"
          class="input-base mt-1.5"
        />
      </label>

      <label class="block">
        <span class="label-base">确认密码</span>
        <input
          v-model="regForm.re_password"
          type="password"
          autocomplete="new-password"
          maxlength="64"
          placeholder="再输入一次密码"
          class="input-base mt-1.5"
        />
      </label>

      <button type="submit" :disabled="loading" class="btn-primary w-full py-2.5">
        {{ loading ? '注册中…' : '注册并登录' }}
      </button>
    </form>

    <p class="mt-5 text-[11px] leading-relaxed text-white/25">
      登录状态保存在当前浏览器；令牌有效期 7 天，退出后即失效。
    </p>
  </div>
</template>