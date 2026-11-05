<script setup lang="ts">
const route = useRoute()
const config = useRuntimeConfig()
const toast = useToast()
const { user, logout } = useAdminAuth()

const siteBase = computed(() => config.public.siteBase || 'http://localhost:3000')

const nav = [
  { label: '概览', to: '/', icon: '▦', match: (path: string) => path === '/' },
  { label: '游戏审核', to: '/games', icon: '◈', match: (path: string) => path.startsWith('/games') },
  { label: '用户管理', to: '/users', icon: '◉', match: (path: string) => path.startsWith('/users') },
  { label: '文章管理', to: '/articles', icon: '▤', match: (path: string) => path.startsWith('/articles') },
]

const pageTitle = computed(() => {
  return nav.find((item) => item.match(route.path))?.label ?? '管理端'
})

async function onLogout() {
  await logout()
  toast.success('已退出管理端')
  await navigateTo('/login')
}
</script>

<template>
  <div class="flex min-h-screen">
    <!-- 侧边栏 -->
    <aside class="hidden w-60 shrink-0 flex-col border-r border-white/10 bg-slate-950/50 px-3 py-5 backdrop-blur-2xl md:flex">
      <NuxtLink to="/" class="flex items-center gap-2.5 px-3">
        <span class="grid h-9 w-9 place-items-center rounded-xl bg-gradient-to-br from-sky-400/30 to-fuchsia-400/20 text-sm font-semibold text-sky-100 ring-1 ring-white/10">
          F
        </span>
        <span>
          <span class="block text-sm font-medium tracking-wide text-white/85">Fishmo</span>
          <span class="block text-[9px] uppercase tracking-[0.28em] text-white/25">Admin Console</span>
        </span>
      </NuxtLink>

      <nav class="mt-8 space-y-1" aria-label="管理导航">
        <NuxtLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          class="flex items-center gap-3 rounded-xl px-3 py-2.5 text-xs transition"
          :class="
            item.match(route.path)
              ? 'bg-white/[0.1] text-white'
              : 'text-white/40 hover:bg-white/[0.05] hover:text-white/80'
          "
        >
          <span class="w-4 text-center text-[13px] opacity-70" aria-hidden="true">{{ item.icon }}</span>
          {{ item.label }}
        </NuxtLink>
      </nav>

      <div class="mt-auto space-y-2 border-t border-white/5 pt-4">
        <a
          :href="siteBase"
          target="_blank"
          rel="noopener"
          class="flex items-center justify-between rounded-xl px-3 py-2 text-[11px] text-white/35 transition hover:bg-white/[0.05] hover:text-white/70"
        >
          返回前台
          <span aria-hidden="true">↗</span>
        </a>

        <div v-if="user" class="rounded-xl bg-white/[0.04] px-3 py-2.5">
          <div class="flex items-center gap-2">
            <img
              v-if="user.avatar"
              :src="user.avatar"
              :alt="user.username"
              class="h-7 w-7 rounded-full object-cover ring-1 ring-white/15"
            />
            <span
              v-else
              class="grid h-7 w-7 place-items-center rounded-full bg-gradient-to-br from-sky-500/30 to-fuchsia-500/30 text-[10px] text-white/80"
            >
              {{ user.username.charAt(0) }}
            </span>
            <div class="min-w-0">
              <p class="truncate text-[11px] font-medium text-white/75">{{ user.username }}</p>
              <p class="text-[9px] uppercase tracking-[0.18em] text-sky-200/40">Administrator</p>
            </div>
          </div>
          <button
            type="button"
            class="mt-2 w-full rounded-lg border border-white/5 py-1.5 text-[10px] text-rose-200/60 transition hover:bg-rose-500/10 hover:text-rose-100"
            @click="onLogout"
          >
            退出登录
          </button>
        </div>
      </div>
    </aside>

    <!-- 主区域 -->
    <div class="flex min-w-0 flex-1 flex-col">
      <header class="sticky top-0 z-30 border-b border-white/10 bg-slate-950/70 px-4 py-3 backdrop-blur-2xl sm:px-6">
        <div class="flex items-center justify-between gap-4">
          <div>
            <p class="text-[9px] uppercase tracking-[0.3em] text-white/25">Fishmo Admin</p>
            <h1 class="mt-0.5 text-sm font-medium text-white/85">{{ pageTitle }}</h1>
          </div>
          <div class="flex items-center gap-2">
            <a
              :href="siteBase"
              target="_blank"
              rel="noopener"
              class="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[10px] text-white/45 transition hover:bg-white/[0.1] hover:text-white md:hidden"
            >
              前台
            </a>
            <span class="rounded-full border border-sky-300/20 bg-sky-400/10 px-2.5 py-1 text-[10px] text-sky-100/70">
              管理员
            </span>
          </div>
        </div>

        <!-- 移动端导航 -->
        <nav class="no-scrollbar mt-3 flex gap-1.5 overflow-x-auto md:hidden" aria-label="管理导航（移动端）">
          <NuxtLink
            v-for="item in nav"
            :key="item.to"
            :to="item.to"
            class="shrink-0 rounded-full border px-3 py-1.5 text-[10px] transition"
            :class="
              item.match(route.path)
                ? 'border-sky-300/30 bg-sky-400/10 text-sky-100'
                : 'border-white/10 bg-white/[0.04] text-white/45'
            "
          >
            {{ item.label }}
          </NuxtLink>
        </nav>
      </header>

      <main class="flex-1 px-4 py-6 sm:px-6 lg:px-8">
        <slot />
      </main>
    </div>
  </div>
</template>