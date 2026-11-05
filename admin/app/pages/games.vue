<script setup lang="ts">
import type { AdminGal, PageData } from '~/types'
import { describeError } from '~/utils/api'
import { formatDate } from '~/utils/date'

type GameStatus = 'pending' | 'published' | 'all'

const api = useAdminApi()
const toast = useToast()
const confirm = useConfirm()
const route = useRoute()
const router = useRouter()

useHead({ title: '游戏审核 · Fishmo 管理端' })

const tabs: { value: GameStatus; label: string }[] = [
  { value: 'pending', label: '待审核' },
  { value: 'published', label: '已公开' },
  { value: 'all', label: '全部' },
]

const status = computed<GameStatus>(() => {
  const value = String(route.query.status ?? 'pending')
  return tabs.some((item) => item.value === value) ? (value as GameStatus) : 'pending'
})

const page = ref(1)
const size = 10

const { data, pending, error, refresh } = await useAsyncData<PageData<AdminGal>>(
  () => `admin-games-${status.value}-${page.value}`,
  () =>
    api.get<PageData<AdminGal>>('/api/admin/control/BrowseGal', {
      page: page.value,
      size,
      status: status.value,
    }),
  {
    watch: [status, page],
    default: () => ({ total: 0, items: [] }),
  },
)

watch(
  () => route.query.status,
  () => {
    page.value = 1
  },
)

const games = computed(() => data.value?.items ?? [])
const total = computed(() => data.value?.total ?? 0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / size)))

const siteBase = computed(
  () => useRuntimeConfig().public.siteBase || 'http://localhost:3000',
)

function setStatus(value: GameStatus) {
  if (value === status.value) return
  page.value = 1
  router.replace({ query: { status: value } })
}

async function setPublished(game: AdminGal, value: boolean) {
  if (!value) {
    const ok = await confirm.confirm({
      title: '下架游戏',
      message: `下架「${game.name}」后，普通访客将无法在列表中看到它。作者仍可在个人中心查看。`,
      confirmText: '确认下架',
      danger: true,
    })
    if (!ok) return
  }
  try {
    await api.put('/api/admin/control/UpdateStatus', undefined, {
      gal_id: game.id,
      status: value,
    })
    toast.success(value ? '已通过审核' : '已下架')
    refresh()
  } catch (err) {
    toast.error(describeError(err))
  }
}

async function remove(game: AdminGal) {
  const ok = await confirm.confirm({
    title: '删除游戏',
    message: `「${game.name}」及其链接、评论、收藏都会被删除，且无法恢复。`,
    confirmText: '确认删除',
    danger: true,
  })
  if (!ok) return
  try {
    await api.del('/api/admin/control/DeleteGal', { gal_id: game.id })
    toast.success('游戏已删除')
    if (games.value.length === 1 && page.value > 1) page.value -= 1
    else refresh()
  } catch (err) {
    toast.error(describeError(err))
  }
}

function altNames(game: AdminGal): string {
  return [game.cn_name, game.jp_name, game.en_name]
    .filter((name) => name && name !== game.name)
    .join(' / ')
}
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <header class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="section-kicker">GAME REVIEW</p>
        <h2 class="mt-2 text-xl font-semibold text-white">游戏审核</h2>
        <p class="mt-1.5 text-xs text-white/35">
          新发布的游戏默认隐藏，通过后才会出现在前台。
        </p>
      </div>
      <p class="text-[11px] text-white/30">
        共 <span class="tabular-nums text-white/55">{{ total }}</span> 条
      </p>
    </header>

    <div class="mt-5 inline-flex rounded-xl border border-white/10 bg-white/[0.04] p-1">
      <button
        v-for="item in tabs"
        :key="item.value"
        type="button"
        class="rounded-lg px-4 py-1.5 text-[11px] transition"
        :class="
          status === item.value
            ? 'bg-white/[0.12] text-white'
            : 'text-white/40 hover:text-white/70'
        "
        @click="setStatus(item.value)"
      >
        {{ item.label }}
      </button>
    </div>

    <div v-if="pending && games.length === 0" class="mt-5 space-y-2">
      <div
        v-for="n in 4"
        :key="n"
        class="h-24 animate-pulse rounded-2xl border border-white/10 bg-white/[0.05]"
      />
    </div>

    <div v-else-if="error && games.length === 0" class="glass-panel mt-5 px-5 py-10 text-center">
      <p class="text-xs text-white/45">游戏列表加载失败</p>
      <button type="button" class="btn-ghost mt-4 px-4 py-1.5" @click="refresh()">重试</button>
    </div>

    <div v-else-if="games.length === 0" class="glass-panel mt-5 px-5 py-12 text-center">
      <p class="text-xs text-white/35">
        {{ status === 'pending' ? '没有待审核的游戏。' : '这个筛选下没有游戏。' }}
      </p>
    </div>

    <ul v-else class="mt-5 space-y-2">
      <li
        v-for="game in games"
        :key="game.id"
        class="glass-panel flex flex-wrap items-center gap-4 p-3.5 transition hover:border-white/20"
      >
        <img
          v-if="game.cover"
          :src="game.cover"
          :alt="game.name"
          class="h-20 w-14 shrink-0 rounded-lg object-cover ring-1 ring-white/10"
        />
        <div v-else class="grid h-20 w-14 shrink-0 place-items-center rounded-lg bg-white/[0.05] text-white/20">
          ?
        </div>

        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <p class="truncate text-xs font-medium text-white/85">{{ game.name }}</p>
            <span
              class="rounded-full border px-2 py-0.5 text-[9px]"
              :class="
                game.status
                  ? 'border-emerald-300/20 bg-emerald-400/10 text-emerald-100/80'
                  : 'border-amber-300/20 bg-amber-400/10 text-amber-100/80'
              "
            >
              {{ game.status ? '已公开' : '待审核' }}
            </span>
            <span v-if="game.category" class="text-[10px] text-white/25">{{ game.category }}</span>
          </div>
          <p v-if="altNames(game)" class="mt-0.5 truncate text-[10px] text-white/30">
            {{ altNames(game) }}
          </p>
          <p class="mt-1 flex flex-wrap items-center gap-3 text-[10px] text-white/30">
            <span class="inline-flex items-center gap-1.5">
              <img
                v-if="game.avatar"
                :src="game.avatar"
                alt=""
                class="h-4 w-4 rounded-full object-cover ring-1 ring-white/10"
              />
              {{ game.author }}
            </span>
            <span>发布于 {{ formatDate(game.created_at) }}</span>
            <span class="tabular-nums">{{ game.views }} 浏览</span>
          </p>
        </div>

        <div class="flex shrink-0 flex-wrap items-center gap-1.5">
          <a
            :href="`${siteBase}/galgame/${game.id}`"
            target="_blank"
            rel="noopener"
            class="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[10px] text-white/50 transition hover:bg-white/[0.1] hover:text-white"
          >
            预览 ↗
          </a>
          <button
            v-if="!game.status"
            type="button"
            class="rounded-lg bg-sky-500/90 px-3 py-1.5 text-[10px] font-medium text-slate-950 transition hover:bg-sky-400"
            @click="setPublished(game, true)"
          >
            通过
          </button>
          <button
            v-else
            type="button"
            class="rounded-lg border border-amber-300/20 bg-amber-400/10 px-3 py-1.5 text-[10px] text-amber-100/80 transition hover:bg-amber-400/15"
            @click="setPublished(game, false)"
          >
            下架
          </button>
          <button
            type="button"
            class="rounded-lg border border-rose-400/20 bg-rose-500/[0.08] px-3 py-1.5 text-[10px] text-rose-200/75 transition hover:bg-rose-500/15"
            @click="remove(game)"
          >
            删除
          </button>
        </div>
      </li>
    </ul>

    <AdminPagination v-model:page="page" :total-pages="totalPages" :total="total" />
  </div>
</template>