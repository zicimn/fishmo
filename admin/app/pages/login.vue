<script setup lang="ts">
import { describeError } from '~/utils/api'

definePageMeta({ layout: false })

const route = useRoute()
const router = useRouter()
const toast = useToast()
const { login } = useAdminAuth()

const form = reactive({ username: '', password: '' })
const loading = ref(false)
const errorMsg = ref('')

useHead({ title: '管理员登录 · Fishmo' })

async function submit() {
  if (loading.value) return
  errorMsg.value = ''
  const username = form.username.trim()
  if (!username) {
    errorMsg.value = '请输入管理员用户名'
    return
  }
  if (!form.password) {
    errorMsg.value = '请输入密码'
    return
  }

  loading.value = true
  try {
    await login(username, form.password)
    toast.success('登录成功')
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
    if (redirect.startsWith('/') && !redirect.startsWith('//')) {
      await router.replace(redirect)
    } else {
      await router.replace('/')
    }
  } catch (err) {
    errorMsg.value = describeError(err)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="mx-auto grid min-h-screen max-w-6xl items-center gap-10 px-5 py-10 lg:grid-cols-2 lg:px-8">
    <!-- 品牌区 -->
    <section class="hidden lg:block">
      <div class="inline-flex items-center gap-3">
        <span class="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-sky-400/30 to-fuchsia-400/20 text-lg font-semibold text-sky-100 ring-1 ring-white/10">
          F
        </span>
        <div>
          <p class="text-sm font-medium tracking-wide text-white/85">Fishmo</p>
          <p class="text-[9px] uppercase tracking-[0.3em] text-white/25">Admin Console</p>
        </div>
      </div>

      <h1 class="mt-10 text-4xl font-semibold leading-tight text-white">
        管理社区内容，
        <br />
        <span class="bg-gradient-to-r from-sky-300 via-indigo-200 to-fuchsia-300 bg-clip-text text-transparent">
          让好作品被看见
        </span>
      </h1>
      <p class="mt-5 max-w-md text-sm leading-relaxed text-white/40">
        审核新发布的游戏、管理用户账号、隐藏或删除违规文章。所有操作实时生效。
      </p>

      <ul class="mt-10 space-y-4">
        <li v-for="item in ['游戏发布审核与下架', '用户账号启用与禁用', '文章公开状态管理', '社区数据概览']" :key="item" class="flex items-center gap-3 text-xs text-white/45">
          <span class="grid h-5 w-5 place-items-center rounded-full border border-sky-300/20 bg-sky-400/10 text-[9px] text-sky-200/80">✓</span>
          {{ item }}
        </li>
      </ul>
    </section>

    <!-- 登录卡片 -->
    <section class="mx-auto w-full max-w-md">
      <div class="glass-card p-7 sm:p-9">
        <div class="lg:hidden">
          <span class="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-sky-400/30 to-fuchsia-400/20 text-base font-semibold text-sky-100 ring-1 ring-white/10">
            F
          </span>
        </div>

        <p class="section-kicker mt-5 lg:mt-0">SIGN IN</p>
        <h2 class="mt-2 text-xl font-semibold text-white">管理员登录</h2>
        <p class="mt-1.5 text-xs leading-relaxed text-white/35">
          仅限拥有管理员权限的 Fishmo 账号登录。
        </p>

        <form class="mt-6 space-y-4" @submit.prevent="submit">
          <label class="block">
            <span class="label-base">用户名</span>
            <input
              v-model="form.username"
              autocomplete="username"
              maxlength="20"
              placeholder="管理员用户名"
              class="input-base mt-1.5"
            />
          </label>

          <label class="block">
            <span class="label-base">密码</span>
            <input
              v-model="form.password"
              type="password"
              autocomplete="current-password"
              placeholder="••••••••"
              class="input-base mt-1.5"
            />
          </label>

          <p
            v-if="errorMsg"
            class="rounded-xl border border-rose-400/25 bg-rose-500/10 px-3 py-2 text-xs leading-relaxed text-rose-200"
            role="alert"
          >
            {{ errorMsg }}
          </p>

          <button type="submit" class="btn-primary w-full py-2.5" :disabled="loading">
            {{ loading ? '登录中…' : '进入管理端' }}
          </button>
        </form>

        <p class="mt-6 text-[10px] leading-relaxed text-white/20">
          登录状态保存在当前浏览器；令牌有效期 7 天。非管理员账号无法进入。
        </p>
      </div>
    </section>
  </div>
</template>