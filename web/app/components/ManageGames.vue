<script setup lang="ts">
import type { GalItem, PageData } from '~/types'
import { describeError } from '~/utils/api'
import { formatDate } from '~/utils/date'

const api = useApi()
const toast = useToast()
const confirm = useConfirm()
const { user } = useAuth()

const page = ref(1)
const size = 12

const { data, pending, error, refresh } = await useAsyncData<PageData<GalItem>>(
  () => `manage-games-${user.value?.id ?? 0}-${page.value}`,
  () =>
    api.get<PageData<GalItem>>('/api/v1/galgame/', {
      page: page.value,
      size,
      author_id: user.value?.id,
    }),
  {
    server: false,
    watch: [page, () => user.value?.id],
    default: () => ({ total: 0, items: [] }),
  },
)

const games = computed(() => data.value?.items ?? [])
const total = computed(() => data.value?.total ?? 0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / size)))

async function remove(game: GalItem) {
  const ok = await confirm.confirm({
    title: '删除游戏',
    message: `「${game.name}」及其链接、评论、收藏记录都会被删除，且无法恢复。`,
    confirmText: '确认删除',
    danger: true,
  })
  if (!ok) return
  try {
    await api.del('/api/v1/galgame/delete', { id: game.id })
    toast.success('游戏已删除')
    if (games.value.length === 1 && page.value > 1) page.value -= 1
    else refresh()
  } catch (err) {
    toast.error(describeError(err))
  }
}
</script>

<template>
  <section>
    <div class="flex flex-wrap items-center justify-between gap-3">
      <p class="text-[11px] text-white/35">
        共 <span class="tabular-nums text-white/60">{{ total }}</span> 部作品
      </p>
      <NuxtLink to="/publish" class="btn-primary px-4 py-2">发布新游戏</NuxtLink>
    </div>

    <div v-if="pending && games.length === 0" class="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      <div
        v-for="n in 4"
        :key="n"
        class="animate-pulse overflow-hidden rounded-2xl border border-white/10 bg-white/[0.05]"
      >
        <div class="aspect-[2/3] bg-white/[0.04]" />
        <div class="space-y-2 p-4">
          <div class="h-3 w-2/3 rounded bg-white/10" />
          <div class="h-2.5 w-1/3 rounded bg-white/5" />
        </div>
      </div>
    </div>

    <div v-else-if="error && games.length === 0" class="glass-panel mt-5 px-5 py-10 text-center">
      <p class="text-xs text-white/45">作品列表加载失败</p>
      <button type="button" class="btn-ghost mt-4 px-4 py-1.5" @click="refresh()">重试</button>
    </div>

    <div v-else-if="games.length === 0" class="glass-panel mt-5 px-5 py-12 text-center">
      <p class="text-xs text-white/40">你还没有发布过游戏。</p>
      <NuxtLink to="/publish" class="btn-primary mt-5">发布第一部作品</NuxtLink>
    </div>

    <div v-else class="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
      <article
        v-for="game in games"
        :key="game.id"
        class="group overflow-hidden rounded-2xl border border-white/10 bg-white/[0.05] backdrop-blur-2xl transition hover:border-white/20"
      >
        <NuxtLink :to="`/galgame/${game.id}`" class="relative block aspect-[2/3] overflow-hidden">
          <img
            v-if="game.cover"
            :src="game.cover"
            :alt="game.name"
            loading="lazy"
            class="h-full w-full object-cover transition duration-500 group-hover:scale-105"
          />
          <span
            class="absolute left-3 top-3 rounded-full border px-2.5 py-1 text-[10px] backdrop-blur-md"
            :class="
              game.status
                ? 'border-emerald-300/25 bg-emerald-400/15 text-emerald-100/90'
                : 'border-amber-300/25 bg-amber-400/15 text-amber-100/90'
            "
          >
            {{ game.status ? '已公开' : '待审核' }}
          </span>
        </NuxtLink>

        <div class="p-4">
          <h3 class="line-clamp-1 text-xs font-medium text-white/85">{{ game.name }}</h3>
          <p class="mt-1.5 flex items-center justify-between text-[10px] text-white/30">
            <span>{{ formatDate(game.updated_at) }}</span>
            <span class="tabular-nums">{{ game.views }} 浏览</span>
          </p>
          <div class="mt-3 flex items-center gap-1.5">
            <NuxtLink
              :to="`/galgame/${game.id}`"
              class="flex-1 rounded-lg border border-white/10 bg-white/[0.04] py-1.5 text-center text-[10px] text-white/55 transition hover:bg-white/[0.1] hover:text-white"
            >
              查看
            </NuxtLink>
            <NuxtLink
              :to="`/manage/${game.id}`"
              class="flex-1 rounded-lg border border-white/10 bg-white/[0.04] py-1.5 text-center text-[10px] text-white/55 transition hover:bg-white/[0.1] hover:text-white"
            >
              编辑
            </NuxtLink>
            <button
              type="button"
              class="flex-1 rounded-lg border border-rose-400/20 bg-rose-500/[0.08] py-1.5 text-[10px] text-rose-200/70 transition hover:bg-rose-500/15 hover:text-rose-100"
              @click="remove(game)"
            >
              删除
            </button>
          </div>
        </div>
      </article>
    </div>

    <PaginationBar v-model:page="page" :total-pages="totalPages" />
  </section>
</template>