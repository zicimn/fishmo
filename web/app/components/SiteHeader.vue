<script setup lang="ts">
import type { SearchTypeValue } from '~/types'
import { SEARCH_OPTIONS } from '~/types'
import { describeError } from '~/utils/api'

const route = useRoute()
const router = useRouter()
const runtime = useRuntimeConfig()
const api = useApi()
const toast = useToast()

const { user, ready, isLoggedIn, isAdmin, logout } = useAuth()
const { openAuth } = useAuthDialog()

const isMounted = ref(false)
const mobileOpen = ref(false)
const searchOpen = ref(false)
const searchKeyword = ref('')
const searchType = ref<SearchTypeValue>('name')
const searchInput = ref<HTMLInputElement | null>(null)
const randomLoading = ref(false)
const userMenuOpen = ref(false)
const userMenuRef = ref<HTMLElement | null>(null)
const settingsOpen = ref(false)

const adminBase = computed(() => runtime.public.adminBase || 'http://localhost:3001')

const nav = [
  { label: '首页', to: '/', match: (path: string) => path === '/' },
  {
    label: '全部游戏',
    to: '/games',
    match: (path: string) => path.startsWith('/games') || path.startsWith('/galgame'),
  },
  {
    label: '文章',
    to: '/articles',
    match: (path: string) => path.startsWith('/articles') || path.startsWith('/article'),
  },
  { label: '关于', to: '/about', match: (path: string) => path.startsWith('/about') },
]

const isPublish = computed(() => route.path.startsWith('/publish'))

watch(
  () => route.fullPath,
  () => {
    mobileOpen.value = false
    userMenuOpen.value = false
    searchOpen.value = false
  },
)

watch(searchOpen, async (open) => {
  if (!open) return
  await nextTick()
  searchInput.value?.focus()
})

onMounted(() => {
  isMounted.value = true
  document.addEventListener('click', onDocumentClick)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
})

function onDocumentClick(event: MouseEvent) {
  if (!userMenuRef.value) return
  if (!userMenuRef.value.contains(event.target as Node)) userMenuOpen.value = false
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    searchOpen.value = false
    mobileOpen.value = false
    userMenuOpen.value = false
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

function submitSearch() {
  const keyword = searchKeyword.value.trim()
  if (!keyword) return
  searchOpen.value = false
  mobileOpen.value = false
  router.push({
    path: '/games',
    query: { keyword, search_type: searchType.value },
  })
}

async function randomGame() {
  if (randomLoading.value) return
  randomLoading.value = true
  try {
    const data = await api.get<{ id: number }>('/api/v1/galgame/rvisit')
    mobileOpen.value = false
    await router.push(`/galgame/${data.id}`)
  } catch (err) {
    toast.error(describeError(err))
  } finally {
    randomLoading.value = false
  }
}

function login(mode: 'login' | 'register') {
  userMenuOpen.value = false
  mobileOpen.value = false
  openAuth(mode)
}

async function onLogout() {
  userMenuOpen.value = false
  mobileOpen.value = false
  await logout()
  toast.success('已退出登录')
  await router.push('/')
}

const initial = computed(() => user.value?.username.trim().charAt(0) || 'U')
</script>

<template>
  <header class="px-5 pt-6 sm:px-8">
    <div
      class="mx-auto flex max-w-6xl items-center justify-between rounded-2xl border border-white/10 bg-white/[0.06] px-4 py-3 backdrop-blur-xl sm:px-6"
    >
      <NuxtLink to="/" class="flex shrink-0 items-center gap-3">
        <img
          src="/favicon.ico"
          alt="Fishmo"
          class="h-9 w-9 rounded-xl object-cover ring-1 ring-white/20"
        />
        <span class="hidden text-sm font-medium tracking-wide text-white/80 sm:block">
          Fishmo · Galgame
        </span>
      </NuxtLink>

      <div class="flex items-center gap-2 sm:gap-3">
        <nav
          class="hidden items-center gap-0.5 rounded-full border border-white/10 bg-white/[0.04] p-1 md:flex"
          aria-label="主导航"
        >
          <NuxtLink
            v-for="item in nav"
            :key="item.to"
            :to="item.to"
            class="rounded-full px-3 py-1.5 text-[11px] transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-300"
            :class="
              item.match(route.path)
                ? 'bg-white/[0.12] text-white'
                : 'text-white/45 hover:text-white/80'
            "
          >
            {{ item.label }}
          </NuxtLink>
        </nav>

        <div class="flex items-center gap-1.5">
          <!-- 搜索 -->
          <button
            type="button"
            class="grid h-8 w-8 place-items-center rounded-full border border-white/10 bg-white/[0.04] text-white/50 transition hover:bg-white/[0.12] hover:text-white"
            aria-label="搜索游戏"
            @click="searchOpen = true"
          >
            <svg viewBox="0 0 20 20" fill="none" class="h-3.5 w-3.5" aria-hidden="true">
              <circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" stroke-width="1.6" />
              <path d="M13 13l4 4" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
            </svg>
          </button>

          <!-- 随机游戏 -->
          <button
            type="button"
            class="hidden h-8 w-8 place-items-center rounded-full border border-white/10 bg-white/[0.04] text-white/50 transition hover:bg-white/[0.12] hover:text-white sm:grid"
            :class="{ 'animate-pulse': randomLoading }"
            aria-label="随机游戏"
            :disabled="randomLoading"
            @click="randomGame"
          >
            <svg viewBox="0 0 20 20" fill="none" class="h-3.5 w-3.5" aria-hidden="true">
              <path
                d="M3 5h3l8 10h3M3 15h3l2.2-2.8M12 7l2-2h3"
                stroke="currentColor"
                stroke-width="1.5"
                stroke-linecap="round"
                stroke-linejoin="round"
              />
            </svg>
          </button>

          <!-- 发布 -->
          <NuxtLink
            v-if="isMounted && ready && isLoggedIn"
            to="/publish"
            class="hidden rounded-full border px-3.5 py-1.5 text-[11px] transition sm:inline-flex"
            :class="
              isPublish
                ? 'border-sky-300/40 bg-sky-400/15 text-sky-100'
                : 'border-white/10 bg-white/[0.04] text-white/55 hover:bg-white/[0.1] hover:text-white'
            "
          >
            发布
          </NuxtLink>

          <!-- 设置 -->
          <button
            type="button"
            class="grid h-8 w-8 place-items-center rounded-full border border-white/10 bg-white/[0.04] text-white/50 transition hover:bg-white/[0.12] hover:text-white"
            aria-label="外观设置"
            @click="settingsOpen = true"
          >
            <svg viewBox="0 0 20 20" fill="none" class="h-3.5 w-3.5" aria-hidden="true">
              <circle cx="10" cy="10" r="2.6" stroke="currentColor" stroke-width="1.5" />
              <path
                d="M10 2.5v2M10 15.5v2M2.5 10h2M15.5 10h2M4.7 4.7l1.4 1.4M13.9 13.9l1.4 1.4M15.3 4.7l-1.4 1.4M6.1 13.9l-1.4 1.4"
                stroke="currentColor"
                stroke-width="1.4"
                stroke-linecap="round"
              />
            </svg>
          </button>

          <!-- 用户 -->
          <div ref="userMenuRef" class="relative">
            <div
              v-if="!isMounted || !ready"
              class="h-8 w-8 animate-pulse rounded-full bg-white/10"
              aria-hidden="true"
            />
            <template v-else-if="isLoggedIn && user">
              <button
                type="button"
                class="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] py-1 pl-1 pr-2 text-[11px] text-white/60 transition hover:bg-white/[0.1] hover:text-white"
                :aria-expanded="userMenuOpen"
                @click="userMenuOpen = !userMenuOpen"
              >
                <img
                  v-if="user.avatar"
                  :src="user.avatar"
                  :alt="user.username"
                  class="h-6 w-6 rounded-full object-cover ring-1 ring-white/15"
                />
                <span
                  v-else
                  class="grid h-6 w-6 place-items-center rounded-full bg-gradient-to-br from-sky-500/40 to-fuchsia-500/40 text-[10px] font-medium text-white/85 ring-1 ring-white/10"
                >
                  {{ initial }}
                </span>
                <span class="hidden max-w-20 truncate sm:block">{{ user.username }}</span>
              </button>

              <div
                v-if="userMenuOpen"
                class="absolute right-0 top-full z-50 mt-2 w-52 overflow-hidden rounded-2xl border border-white/10 bg-slate-900/90 p-1.5 shadow-[0_20px_60px_-20px_rgba(2,6,23,0.95)] backdrop-blur-2xl"
              >
                <p class="px-3 py-2 text-[11px] text-white/35">
                  {{ user.username }}
                  <span v-if="isAdmin" class="ml-1 text-sky-200/70">管理员</span>
                </p>
                <NuxtLink
                  to="/user/profile"
                  class="block rounded-xl px-3 py-2 text-xs text-white/60 transition hover:bg-white/[0.08] hover:text-white"
                  @click="userMenuOpen = false"
                >
                  个人资料
                </NuxtLink>
                <NuxtLink
                  to="/manage"
                  class="block rounded-xl px-3 py-2 text-xs text-white/60 transition hover:bg-white/[0.08] hover:text-white"
                  @click="userMenuOpen = false"
                >
                  我的内容
                </NuxtLink>
                <NuxtLink
                  v-if="isAdmin"
                  :to="adminBase"
                  target="_blank"
                  class="block rounded-xl px-3 py-2 text-xs text-sky-100/70 transition hover:bg-white/[0.08] hover:text-white"
                  @click="userMenuOpen = false"
                >
                  管理端 ↗
                </NuxtLink>
                <button
                  type="button"
                  class="mt-1 block w-full rounded-xl border-t border-white/5 px-3 py-2 text-left text-xs text-rose-200/70 transition hover:bg-rose-500/10 hover:text-rose-100"
                  @click="onLogout"
                >
                  退出登录
                </button>
              </div>
            </template>
            <div v-else class="flex items-center gap-1.5">
              <button type="button" class="hidden px-2 py-1 text-[11px] text-white/45 transition hover:text-white sm:block" @click="login('login')">
                登录
              </button>
              <button
                type="button"
                class="rounded-full bg-sky-500/90 px-3.5 py-1.5 text-[11px] font-medium text-slate-950 transition hover:bg-sky-400"
                @click="login('register')"
              >
                注册
              </button>
            </div>
          </div>

          <!-- 移动端菜单 -->
          <button
            type="button"
            class="grid h-8 w-8 place-items-center rounded-full border border-white/10 bg-white/[0.04] text-white/50 transition hover:bg-white/[0.12] hover:text-white md:hidden"
            aria-label="打开菜单"
            @click="mobileOpen = !mobileOpen"
          >
            <svg viewBox="0 0 20 20" fill="none" class="h-4 w-4" aria-hidden="true">
              <path d="M3 5h14M3 10h14M3 15h14" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" />
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- 移动端抽屉 -->
    <Teleport to="body">
      <div
        v-if="mobileOpen"
        class="fixed inset-0 z-[90] bg-slate-950/70 backdrop-blur-sm md:hidden"
        @click.self="mobileOpen = false"
      >
        <div class="mx-4 mt-24 rounded-3xl border border-white/10 bg-slate-900/90 p-4 shadow-2xl backdrop-blur-2xl">
          <nav class="grid grid-cols-2 gap-2">
            <NuxtLink
              v-for="item in nav"
              :key="item.to"
              :to="item.to"
              class="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-xs text-white/60 transition hover:bg-white/[0.1] hover:text-white"
              @click="mobileOpen = false"
            >
              {{ item.label }}
            </NuxtLink>
            <NuxtLink
              to="/publish"
              class="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-xs text-white/60 transition hover:bg-white/[0.1] hover:text-white"
              @click="mobileOpen = false"
            >
              发布
            </NuxtLink>
            <NuxtLink
              to="/manage"
              class="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-xs text-white/60 transition hover:bg-white/[0.1] hover:text-white"
              @click="mobileOpen = false"
            >
              我的内容
            </NuxtLink>
          </nav>

          <div class="mt-3 grid grid-cols-2 gap-2">
            <button
              type="button"
              class="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-xs text-white/60 transition hover:bg-white/[0.1] hover:text-white"
              @click="searchOpen = true; mobileOpen = false"
            >
              搜索游戏
            </button>
            <button
              type="button"
              class="rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-xs text-white/60 transition hover:bg-white/[0.1] hover:text-white"
              @click="randomGame"
            >
              随机游戏
            </button>
          </div>

          <div v-if="isMounted && ready" class="mt-4 border-t border-white/10 pt-4">
            <template v-if="isLoggedIn && user">
              <p class="px-1 text-[11px] text-white/35">已登录：{{ user.username }}</p>
              <div class="mt-2 grid grid-cols-2 gap-2">
                <NuxtLink to="/user/profile" class="btn-ghost" @click="mobileOpen = false">个人资料</NuxtLink>
                <button type="button" class="btn-ghost" @click="onLogout">退出登录</button>
              </div>
            </template>
            <div v-else class="grid grid-cols-2 gap-2">
              <button type="button" class="btn-ghost" @click="login('login')">登录</button>
              <button type="button" class="btn-primary" @click="login('register')">注册</button>
            </div>
          </div>
        </div>
      </div>

      <!-- 搜索浮层 -->
      <div
        v-if="searchOpen"
        class="fixed inset-0 z-[92] bg-slate-950/70 px-4 pt-24 backdrop-blur-sm"
        @click.self="searchOpen = false"
      >
        <div class="mx-auto w-full max-w-2xl rounded-3xl border border-white/10 bg-slate-900/90 p-5 shadow-[0_24px_80px_-24px_rgba(2,6,23,0.95)] backdrop-blur-2xl sm:p-6">
          <form class="flex flex-col gap-3 sm:flex-row" @submit.prevent="submitSearch">
            <input
              ref="searchInput"
              v-model="searchKeyword"
              maxlength="50"
              placeholder="搜索游戏名称、标签或公司…"
              class="input-base min-w-0 flex-1"
            />
            <select v-model="searchType" class="input-base sm:w-28">
              <option v-for="item in SEARCH_OPTIONS" :key="item.value" :value="item.value">
                {{ item.label }}
              </option>
            </select>
            <button type="submit" class="btn-primary shrink-0 px-6">搜索</button>
          </form>
          <p class="mt-3 text-[11px] text-white/30">
            也可以直接到
            <NuxtLink to="/games" class="text-sky-200/60 underline underline-offset-2" @click="searchOpen = false">
              全部游戏
            </NuxtLink>
            按分类与平台筛选。
          </p>
        </div>
      </div>
    </Teleport>

    <SettingsDialog :open="settingsOpen" @close="settingsOpen = false" />
  </header>
</template>