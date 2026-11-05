<script setup lang="ts">
import type { AdminGal, PageData, Stats } from '~/types'
import { describeError } from '~/utils/api'

const api = useAdminApi()
const toast = useToast()
const confirm = useConfirm()
const { user } = useAdminAuth()

useHead({ title: '概览 · Fishmo 管理端' })

const { data: stats, pending: statsPending, error: statsError, refresh: refreshStats } =
  await useAsyncData<Stats>('admin-stats', () => api.get<Stats>('/api/admin/control/Stats'))

const {
  data: pendingData,
  pending: listPending,
  error: listError,
  refresh: refreshPending,
} = await useAsyncData<PageData<AdminGal>>('admin-pending', () =>
  api.get<PageData<AdminGal>>('/api/admin/control/BrowseGal', {
    page: 1,
    size: 5,
    status: 'pending',
  }),
)

interface StatCard {
  label: string
  value: number
  hint?: string
  to?: string
  accent?: boolean
}

const cards = computed<StatCard[]>(() => {
  const value = stats.value
  return [
    { label: '游戏总数', value: value?.games ?? 0, hint: `${value?.pending_games ?? 0} 部待审核`, to: '/games', accent: true },
    { label: '注册用户', value: value?.users ?? 0, to: '/users' },
    { label: '文章数量', value: value?.articles ?? 0, to: '/articles' },
    { label: '评论数量', value: value?.comments ?? 0 },
    { label: '资源链接', value: value?.links ?? 0 },
    { label: '收藏次数', value: value?.favorites ?? 0 },
  ]
})

const pendingGames = computed(() => pendingData.value?.items ?? [])

async function approve(game: AdminGal) {
  try {
    await api.put('/api/admin/control/UpdateStatus', undefined, {
      gal_id: game.id,
      status: true,
    })
    toast.success(`已通过「${game.name}」`)
    await Promise.all([refreshStats(), refreshPending()])
  } catch (err) {
    toast.error(describeError(err))
  }
}

async function removeGame(game: AdminGal) {
  const ok = await confirm.confirm({
    title: '删除游戏',
    message: `「${game.name}」及其关联的链接、评论、收藏都会被删除，且无法恢复。`,
    confirmText: '确认删除',
    danger: true,
  })
  if (!ok) return
  try {
    await api.del('/api/admin/control/DeleteGal', { gal_id: game.id })
    toast.success('游戏已删除')
    await Promise.all([refreshStats(), refreshPending()])
  } catch (err) {
    toast.error(describeError(err))
  }
}
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <header class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="section-kicker">DASHBOARD</p>
        <h2 class="mt-2 text-xl font-semibold text-white">
          你好，{{ user?.username ?? '管理员' }}
        </h2>
        <p class="mt-1.5 text-xs text-white/35">这是社区目前的内容概况。</p>
      </div>
      <NuxtLink
        v-if="stats?.pending_games"
        to="/games?status=pending"
        class="rounded-xl border border-amber-300/25 bg-amber-400/10 px-4 py-2 text-[11px] text-amber-100/85 transition hover:bg-amber-400/15"
      >
        {{ stats.pending_games }} 部游戏等待审核 →
      </NuxtLink>
    </header>

    <div v-if="statsPending && !stats" class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="n in 6"
        :key="n"
        class="h-28 animate-pulse rounded-2xl border border-white/10 bg-white/[0.05]"
      />
    </div>

    <div
      v-else-if="statsError && !stats"
      class="glass-panel mt-6 px-5 py-10 text-center"
    >
      <p class="text-xs text-white/45">统计数据加载失败</p>
      <button type="button" class="btn-ghost mt-4 px-4 py-1.5" @click="refreshStats()">重试</button>
    </div>

    <div v-else class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <template v-for="(card, index) in cards" :key="card.label">
        <NuxtLink
          v-if="card.to"
          :to="card.to"
          class="glass-panel animate-rise relative overflow-hidden p-5 transition hover:border-white/25"
          :style="{ animationDelay: `${index * 50}ms` }"
        >
          <div
            v-if="card.accent && stats?.pending_games"
            class="absolute right-4 top-4 rounded-full border border-amber-300/25 bg-amber-400/10 px-2 py-0.5 text-[9px] text-amber-100/80"
          >
            待审核 {{ stats.pending_games }}
          </div>
          <p class="text-[10px] uppercase tracking-[0.22em] text-white/25">{{ card.label }}</p>
          <p class="mt-3 text-3xl font-semibold tabular-nums text-white/85">{{ card.value }}</p>
          <p v-if="card.hint" class="mt-1 text-[10px] text-white/30">{{ card.hint }}</p>
        </NuxtLink>
        <div
          v-else
          class="glass-panel animate-rise relative overflow-hidden p-5"
          :style="{ animationDelay: `${index * 50}ms` }"
        >
          <p class="text-[10px] uppercase tracking-[0.22em] text-white/25">{{ card.label }}</p>
          <p class="mt-3 text-3xl font-semibold tabular-nums text-white/85">{{ card.value }}</p>
          <p v-if="card.hint" class="mt-1 text-[10px] text-white/30">{{ card.hint }}</p>
        </div>
      </template>
    </div>

    <!-- 待审核预览 -->
    <section class="mt-8">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="section-kicker">PENDING REVIEW</p>
          <h3 class="mt-1.5 text-base font-semibold text-white">待审核游戏</h3>
        </div>
        <NuxtLink to="/games?status=pending" class="text-[11px] text-white/35 transition hover:text-white">
          查看全部 →
        </NuxtLink>
      </div>

      <div v-if="listPending && !pendingData" class="mt-4 space-y-2">
        <div
          v-for="n in 3"
          :key="n"
          class="h-16 animate-pulse rounded-2xl border border-white/10 bg-white/[0.05]"
        />
      </div>

      <div v-else-if="listError && !pendingData" class="glass-panel mt-4 px-5 py-8 text-center">
        <p class="text-xs text-white/45">待审核列表加载失败</p>
        <button type="button" class="btn-ghost mt-4 px-4 py-1.5" @click="refreshPending()">重试</button>
      </div>

      <div v-else-if="pendingGames.length === 0" class="glass-panel mt-4 px-5 py-10 text-center">
        <p class="text-xs text-white/35">没有待审核的游戏，社区很干净。</p>
      </div>

      <ul v-else class="mt-4 space-y-2">
        <li
          v-for="game in pendingGames"
          :key="game.id"
          class="glass-panel flex flex-wrap items-center gap-3 px-3 py-2.5"
        >
          <img
            v-if="game.cover"
            :src="game.cover"
            :alt="game.name"
            class="h-14 w-10 shrink-0 rounded-lg object-cover ring-1 ring-white/10"
          />
          <div class="min-w-0 flex-1">
            <p class="truncate text-xs font-medium text-white/80">{{ game.name }}</p>
            <p class="mt-0.5 text-[10px] text-white/30">
              {{ game.author }} · {{ game.created_at?.slice(0, 10) }}
              <span v-if="game.category" class="ml-1 text-white/20">· {{ game.category }}</span>
            </p>
          </div>
          <div class="flex shrink-0 gap-1.5">
            <button type="button" class="btn-primary px-3 py-1.5" @click="approve(game)">通过</button>
            <button type="button" class="btn-danger px-3 py-1.5" @click="removeGame(game)">删除</button>
          </div>
        </li>
      </ul>
    </section>

    <!-- 快捷入口 -->
    <section class="mt-8 grid gap-3 sm:grid-cols-3">
      <NuxtLink to="/games" class="glass-panel px-4 py-3 text-xs text-white/55 transition hover:border-white/25 hover:text-white">
        游戏审核 <span class="float-right text-white/25">→</span>
      </NuxtLink>
      <NuxtLink to="/users" class="glass-panel px-4 py-3 text-xs text-white/55 transition hover:border-white/25 hover:text-white">
        用户管理 <span class="float-right text-white/25">→</span>
      </NuxtLink>
      <NuxtLink to="/articles" class="glass-panel px-4 py-3 text-xs text-white/55 transition hover:border-white/25 hover:text-white">
        文章管理 <span class="float-right text-white/25">→</span>
      </NuxtLink>
    </section>
  </div>
</template>