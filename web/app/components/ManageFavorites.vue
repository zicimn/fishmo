<script setup lang="ts">
import type { FavoriteItem, PageData } from '~/types'
import { describeError } from '~/utils/api'
import { formatDate } from '~/utils/date'

const api = useApi()
const toast = useToast()
const confirm = useConfirm()

const page = ref(1)
const size = 12

const { data, pending, error, refresh } = await useAsyncData<PageData<FavoriteItem>>(
  () => `manage-favorites-${page.value}`,
  () => api.get<PageData<FavoriteItem>>('/api/v1/favorite/list', { page: page.value, size }),
  {
    server: false,
    watch: [page],
    default: () => ({ total: 0, items: [] }),
  },
)

const favorites = computed(() => data.value?.items ?? [])
const total = computed(() => data.value?.total ?? 0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / size)))

async function remove(item: FavoriteItem) {
  const ok = await confirm.confirm({
    title: '取消收藏',
    message: `确定将「${item.name}」移出收藏夹吗？`,
    confirmText: '取消收藏',
    danger: true,
  })
  if (!ok) return
  try {
    await api.del('/api/v1/favorite/remove', { gal_id: item.id })
    toast.success('已取消收藏')
    if (favorites.value.length === 1 && page.value > 1) page.value -= 1
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
        共收藏 <span class="tabular-nums text-white/60">{{ total }}</span> 部游戏
      </p>
      <NuxtLink to="/games" class="btn-ghost px-4 py-2">去发现更多</NuxtLink>
    </div>

    <div v-if="pending && favorites.length === 0" class="mt-5 grid gap-4 sm:grid-cols-3 lg:grid-cols-4">
      <div
        v-for="n in 4"
        :key="n"
        class="animate-pulse overflow-hidden rounded-2xl border border-white/10 bg-white/[0.05]"
      >
        <div class="aspect-[2/3] bg-white/[0.04]" />
        <div class="p-4"><div class="h-3 w-2/3 rounded bg-white/10" /></div>
      </div>
    </div>

    <div v-else-if="error && favorites.length === 0" class="glass-panel mt-5 px-5 py-10 text-center">
      <p class="text-xs text-white/45">收藏列表加载失败</p>
      <button type="button" class="btn-ghost mt-4 px-4 py-1.5" @click="refresh()">重试</button>
    </div>

    <div v-else-if="favorites.length === 0" class="glass-panel mt-5 px-5 py-12 text-center">
      <p class="text-xs text-white/40">收藏夹还是空的，遇到喜欢的作品就点一下收藏吧。</p>
      <NuxtLink to="/games" class="btn-primary mt-5">浏览游戏</NuxtLink>
    </div>

    <div v-else class="mt-5 grid gap-4 sm:grid-cols-3 lg:grid-cols-4">
      <article
        v-for="item in favorites"
        :key="item.id"
        class="group overflow-hidden rounded-2xl border border-white/10 bg-white/[0.05] backdrop-blur-2xl transition hover:border-white/20"
      >
        <NuxtLink :to="`/galgame/${item.id}`" class="relative block aspect-[2/3] overflow-hidden">
          <img
            v-if="item.cover"
            :src="item.cover"
            :alt="item.name"
            loading="lazy"
            class="h-full w-full object-cover transition duration-500 group-hover:scale-105"
          />
          <div class="absolute inset-0 bg-gradient-to-t from-slate-950/75 to-transparent" />
          <span
            v-if="item.category"
            class="absolute left-3 top-3 rounded-full border border-white/15 bg-slate-950/55 px-2.5 py-1 text-[10px] text-white/75 backdrop-blur-md"
          >
            {{ item.category }}
          </span>
        </NuxtLink>

        <div class="p-4">
          <h3 class="line-clamp-1 text-xs font-medium text-white/85">{{ item.name }}</h3>
          <p class="mt-1 flex items-center justify-between text-[10px] text-white/30">
            <span>收藏于 {{ formatDate(item.favorited_at) }}</span>
            <span class="tabular-nums">{{ item.views }} 浏览</span>
          </p>
          <div class="mt-3 flex gap-1.5">
            <NuxtLink
              :to="`/galgame/${item.id}`"
              class="flex-1 rounded-lg border border-white/10 bg-white/[0.04] py-1.5 text-center text-[10px] text-white/55 transition hover:bg-white/[0.1] hover:text-white"
            >
              查看
            </NuxtLink>
            <button
              type="button"
              class="flex-1 rounded-lg border border-rose-400/20 bg-rose-500/[0.08] py-1.5 text-[10px] text-rose-200/70 transition hover:bg-rose-500/15"
              @click="remove(item)"
            >
              取消收藏
            </button>
          </div>
        </div>
      </article>
    </div>

    <PaginationBar v-model:page="page" :total-pages="totalPages" />
  </section>
</template>