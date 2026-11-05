<script setup lang="ts">
import type { GalItem, PageData, UserPublic } from '~/types'
import { describeError } from '~/utils/api'
import { formatDate } from '~/utils/date'

const route = useRoute()
const api = useApi()

const id = computed(() => Number(route.params.id))

const { data: profile, pending, error, refresh } = await useAsyncData<UserPublic>(
  () => `user-${id.value}`,
  () => api.get<UserPublic>('/api/v1/user/', { id: id.value }),
  { watch: [id] },
)

const { data: gameData } = await useAsyncData<PageData<GalItem>>(
  () => `user-games-${id.value}`,
  () =>
    api.get<PageData<GalItem>>('/api/v1/galgame/', {
      author_id: id.value,
      page: 1,
      size: 12,
      sort: 'updated_at',
    }),
  {
    server: false,
    watch: [id],
    default: () => ({ total: 0, items: [] }),
  },
)

const games = computed(() => gameData.value?.items ?? [])

useHead(() => ({
  title: profile.value ? `${profile.value.username} 的主页 · Fishmo` : '用户主页 · Fishmo',
}))
</script>

<template>
  <div class="mx-auto max-w-6xl px-4 pb-20 pt-10 sm:px-6">
    <div v-if="pending && !profile" class="animate-pulse space-y-4" aria-hidden="true">
      <div class="h-40 rounded-3xl border border-white/10 bg-white/[0.05]" />
      <div class="h-64 rounded-3xl border border-white/10 bg-white/[0.04]" />
    </div>

    <EmptyState
      v-else-if="error && !profile"
      class="mt-6"
      title="找不到这个用户"
      :description="describeError(error)"
      image="/status/1.png"
      retryable
      @retry="refresh()"
    >
      <NuxtLink to="/" class="btn-ghost mt-5">返回首页</NuxtLink>
    </EmptyState>

    <template v-else-if="profile">
      <section class="glass-card relative overflow-hidden p-6 sm:p-8">
        <div class="pointer-events-none absolute -left-16 -top-16 h-56 w-56 rounded-full bg-fuchsia-500/10 blur-3xl" />
        <div class="relative flex flex-wrap items-center gap-5">
          <img
            v-if="profile.avatar"
            :src="profile.avatar"
            :alt="profile.username"
            class="h-20 w-20 rounded-3xl object-cover ring-1 ring-white/15"
          />
          <span
            v-else
            class="grid h-20 w-20 place-items-center rounded-3xl bg-gradient-to-br from-sky-500/30 to-fuchsia-500/30 text-2xl font-medium text-white/80 ring-1 ring-white/10"
            aria-hidden="true"
          >
            {{ profile.username.charAt(0) }}
          </span>

          <div class="min-w-0 flex-1">
            <h1 class="text-xl font-semibold text-white sm:text-2xl">{{ profile.username }}</h1>
            <p v-if="profile.bio" class="mt-2 max-w-2xl text-xs leading-relaxed text-white/45">
              {{ profile.bio }}
            </p>
            <p v-else class="mt-2 text-xs text-white/25">这位用户还没有填写简介。</p>
            <p class="mt-3 flex flex-wrap gap-x-6 gap-y-1 text-[11px] text-white/35">
              <span class="tabular-nums">{{ profile.gal_cnt }} 部游戏</span>
              <span class="tabular-nums">{{ profile.article_cnt }} 篇文章</span>
              <span v-if="profile.email" class="text-white/30">{{ profile.email }}</span>
              <span v-if="profile.created_at">加入于 {{ formatDate(profile.created_at) }}</span>
            </p>
          </div>

          <div v-if="profile.is_self" class="flex flex-wrap gap-2">
            <NuxtLink to="/user/profile" class="btn-ghost px-4 py-2">编辑资料</NuxtLink>
            <NuxtLink to="/manage" class="btn-primary px-4 py-2">个人中心</NuxtLink>
          </div>
        </div>
      </section>

      <section class="mt-10">
        <div class="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p class="section-kicker">WORKS</p>
            <h2 class="mt-2 text-lg font-semibold text-white">TA 发布过的游戏</h2>
          </div>
          <NuxtLink
            v-if="profile.is_self"
            :to="{ path: '/manage', query: { tab: 'games' } }"
            class="group text-xs text-white/40 transition hover:text-white"
          >
            管理作品
            <span class="inline-block transition group-hover:translate-x-0.5">→</span>
          </NuxtLink>
        </div>

        <div v-if="games.length" class="mt-5 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
          <GameCard v-for="(game, index) in games" :key="game.id" :item="game" :index="index" />
        </div>
        <div v-else class="glass-panel mt-5 px-5 py-10 text-center">
          <p class="text-xs text-white/35">还没有已公开的作品。</p>
        </div>
      </section>
    </template>
  </div>
</template>