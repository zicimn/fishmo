<script setup lang="ts">
import type { UserPublic } from '~/types'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const router = useRouter()
const api = useApi()
const { user, ready, isAdmin } = useAuth()
const adminBase = useRuntimeConfig().public.adminBase as string

const tabs = [
  { value: 'games', label: '游戏' },
  { value: 'articles', label: '文章' },
  { value: 'comments', label: '评论' },
  { value: 'links', label: '链接' },
  { value: 'favorites', label: '收藏' },
] as const

type TabValue = (typeof tabs)[number]['value']

const tab = computed<TabValue>(() => {
  const value = String(route.query.tab ?? 'games')
  return tabs.some((item) => item.value === value) ? (value as TabValue) : 'games'
})

function switchTab(value: TabValue) {
  router.replace({ query: { ...route.query, tab: value } })
}

const mounted = ref(false)
onMounted(() => {
  mounted.value = true
})

const { data: profile } = await useAsyncData<UserPublic>(
  () => `manage-profile-${user.value?.id ?? 0}`,
  () => api.get<UserPublic>('/api/v1/user/', { id: user.value?.id }),
  { server: false, watch: [() => user.value?.id] },
)

useHead({ title: '个人中心 · Fishmo' })
</script>

<template>
  <div class="mx-auto max-w-7xl px-4 pb-20 pt-10 sm:px-6">
    <template v-if="mounted && ready && user">
      <!-- 个人概览 -->
      <section class="glass-card relative overflow-hidden p-6 sm:p-8">
        <div class="pointer-events-none absolute -right-16 -top-16 h-56 w-56 rounded-full bg-sky-500/10 blur-3xl" />
        <div class="relative flex flex-wrap items-center gap-5">
          <img
            v-if="user.avatar"
            :src="user.avatar"
            :alt="user.username"
            class="h-16 w-16 rounded-2xl object-cover ring-1 ring-white/15"
          />
          <span
            v-else
            class="grid h-16 w-16 place-items-center rounded-2xl bg-gradient-to-br from-sky-500/30 to-fuchsia-500/30 text-xl font-medium text-white/80 ring-1 ring-white/10"
            aria-hidden="true"
          >
            {{ user.username.charAt(0) }}
          </span>

          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <h1 class="text-xl font-semibold text-white">{{ user.username }}</h1>
              <span
                v-if="isAdmin"
                class="rounded-full border border-fuchsia-300/25 bg-fuchsia-400/10 px-2.5 py-0.5 text-[10px] text-fuchsia-100/80"
              >
                管理员
              </span>
            </div>
            <p class="mt-1 truncate text-xs text-white/35">{{ user.email }}</p>
            <p v-if="user.bio" class="mt-2 max-w-xl text-xs leading-relaxed text-white/45">
              {{ user.bio }}
            </p>
          </div>

          <div class="flex flex-wrap items-center gap-2">
            <NuxtLink to="/user/profile" class="btn-ghost px-4 py-2">编辑资料</NuxtLink>
            <NuxtLink
              :to="`/user/${user.id}`"
              class="btn-ghost px-4 py-2"
            >
              公开主页
            </NuxtLink>
            <a
              v-if="isAdmin"
              :href="adminBase"
              target="_blank"
              rel="noopener"
              class="btn-primary px-4 py-2"
            >
              管理控制台 ↗
            </a>
          </div>
        </div>

        <dl v-if="profile" class="relative mt-6 flex flex-wrap gap-x-10 gap-y-3 border-t border-white/5 pt-5">
          <div>
            <dt class="text-[10px] uppercase tracking-[0.2em] text-white/25">Games</dt>
            <dd class="mt-1 text-lg font-semibold tabular-nums text-white/80">{{ profile.gal_cnt }}</dd>
          </div>
          <div>
            <dt class="text-[10px] uppercase tracking-[0.2em] text-white/25">Articles</dt>
            <dd class="mt-1 text-lg font-semibold tabular-nums text-white/80">{{ profile.article_cnt }}</dd>
          </div>
          <div>
            <dt class="text-[10px] uppercase tracking-[0.2em] text-white/25">Joined</dt>
            <dd class="mt-1 text-xs text-white/50">{{ profile.created_at?.slice(0, 10) ?? '—' }}</dd>
          </div>
        </dl>
      </section>

      <!-- 分区标签 -->
      <div class="no-scrollbar mt-6 flex gap-1.5 overflow-x-auto rounded-2xl border border-white/10 bg-white/[0.04] p-1.5">
        <button
          v-for="item in tabs"
          :key="item.value"
          type="button"
          class="shrink-0 rounded-xl px-4 py-2 text-xs transition"
          :class="
            tab === item.value
              ? 'bg-white/[0.12] text-white'
              : 'text-white/40 hover:bg-white/[0.05] hover:text-white/70'
          "
          @click="switchTab(item.value)"
        >
          {{ item.label }}
        </button>
      </div>

      <div class="mt-5">
        <ManageGames v-if="tab === 'games'" />
        <ManageArticles v-else-if="tab === 'articles'" />
        <ManageComments v-else-if="tab === 'comments'" />
        <ManageLinks v-else-if="tab === 'links'" />
        <ManageFavorites v-else />
      </div>
    </template>

    <div v-else class="space-y-4" aria-hidden="true">
      <div class="h-48 animate-pulse rounded-3xl border border-white/10 bg-white/[0.05]" />
      <div class="h-12 animate-pulse rounded-2xl border border-white/10 bg-white/[0.04]" />
      <div class="h-64 animate-pulse rounded-3xl border border-white/10 bg-white/[0.04]" />
    </div>
  </div>
</template>