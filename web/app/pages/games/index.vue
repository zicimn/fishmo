<script setup lang="ts">
import type { GalItem, PageData, SearchTypeValue } from '~/types'
import { CATEGORY_OPTIONS, PLATFORM_OPTIONS, SEARCH_OPTIONS } from '~/types'

useHead({ title: '全部游戏 · Fishmo' })

const api = useApi()
const route = useRoute()
const router = useRouter()

const keyword = computed(() => String(route.query.keyword ?? '').trim())
const searchType = computed<SearchTypeValue>(() => {
  const value = String(route.query.search_type ?? 'name')
  return SEARCH_OPTIONS.some((item) => item.value === value)
    ? (value as SearchTypeValue)
    : 'name'
})
const category = computed(() => String(route.query.category ?? ''))
const platform = computed(() => String(route.query.platform ?? ''))
const sort = computed(() => (route.query.sort === 'views' ? 'views' : 'updated_at'))
const page = computed(() => Math.max(1, Number(route.query.page) || 1))
const pageSize = 20

// 名称搜索走游戏列表（可叠加分类/平台）；标签、公司走全文搜索接口
const isFieldSearch = computed(() => Boolean(keyword.value) && searchType.value !== 'name')

const searchInput = ref(keyword.value)
const searchTypeInput = ref<SearchTypeValue>(searchType.value)
watch(
  () => route.fullPath,
  () => {
    searchInput.value = keyword.value
    searchTypeInput.value = searchType.value
  },
)

const { data, pending, error, refresh } = await useAsyncData<PageData<GalItem>>(
  () => `games-${route.fullPath}`,
  () => {
    if (isFieldSearch.value) {
      return api.get<PageData<GalItem>>('/api/v1/search/', {
        keyword: keyword.value,
        search_type: searchType.value,
        page: page.value,
        size: pageSize,
      })
    }
    return api.get<PageData<GalItem>>('/api/v1/galgame/', {
      page: page.value,
      size: pageSize,
      category: category.value || undefined,
      platform: platform.value || undefined,
      keyword: keyword.value || undefined,
      sort: sort.value,
    })
  },
  {
    watch: [() => route.fullPath],
    default: () => ({ total: 0, items: [] }),
  },
)

const games = computed(() => data.value?.items ?? [])
const total = computed(() => data.value?.total ?? 0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

function updateQuery(patch: Record<string, string | number | undefined>) {
  const next: Record<string, string> = {}
  for (const [key, value] of Object.entries(route.query)) {
    if (typeof value === 'string' && value) next[key] = value
  }
  for (const [key, value] of Object.entries(patch)) {
    if (value === undefined || value === '') delete next[key]
    else next[key] = String(value)
  }
  if (!('page' in patch)) delete next.page
  router.push({ query: next })
}

function selectCategory(value: string) {
  updateQuery({ category: value === category.value ? undefined : value })
}

function onSubmitSearch() {
  updateQuery({
    keyword: searchInput.value.trim() || undefined,
    search_type: searchInput.value.trim() ? searchTypeInput.value : undefined,
  })
}

function clearSearch() {
  searchInput.value = ''
  updateQuery({ keyword: undefined, search_type: undefined })
}

function onPlatformChange(event: Event) {
  updateQuery({ platform: (event.target as HTMLSelectElement).value || undefined })
}

function onSortChange(event: Event) {
  updateQuery({ sort: (event.target as HTMLSelectElement).value })
}
</script>

<template>
  <div class="mx-auto max-w-7xl px-4 pb-20 pt-10 sm:px-6">
    <header class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="section-kicker">GALGAME LIBRARY</p>
        <h1 class="mt-2 text-2xl font-semibold text-white sm:text-3xl">全部游戏</h1>
        <p class="mt-2 text-xs text-white/35">
          共 <span class="tabular-nums text-white/60">{{ total }}</span> 部作品
          <span v-if="isFieldSearch"> · 按{{ SEARCH_OPTIONS.find((item) => item.value === searchType)?.label }}搜索「{{ keyword }}」</span>
        </p>
      </div>

      <div class="flex flex-wrap items-center gap-2">
        <NuxtLink to="/publish" class="btn-primary px-5 py-2.5">发布游戏</NuxtLink>
      </div>
    </header>

    <!-- 搜索 -->
    <form class="mt-6 flex flex-wrap gap-2" role="search" @submit.prevent="onSubmitSearch">
      <div class="relative min-w-[220px] flex-1">
        <span class="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-white/25" aria-hidden="true">
          ⌕
        </span>
        <input
          v-model="searchInput"
          type="search"
          maxlength="50"
          placeholder="搜索游戏名称、标签或公司…"
          class="input-base pl-9"
        />
      </div>
      <select v-model="searchTypeInput" class="input-base w-auto min-w-[104px]" aria-label="搜索字段">
        <option v-for="item in SEARCH_OPTIONS" :key="item.value" :value="item.value">
          {{ item.label }}
        </option>
      </select>
      <button type="submit" class="btn-ghost px-5">搜索</button>
      <button
        v-if="keyword"
        type="button"
        class="btn-ghost px-4 text-white/45"
        @click="clearSearch"
      >
        清除
      </button>
    </form>

    <!-- 筛选 -->
    <div v-if="!isFieldSearch" class="mt-6 flex flex-col gap-4">
      <div class="no-scrollbar -mx-1 flex gap-2 overflow-x-auto px-1 pb-1">
        <button
          type="button"
          class="chip"
          :class="{ 'chip-active': !category }"
          @click="selectCategory('')"
        >
          全部
        </button>
        <button
          v-for="item in CATEGORY_OPTIONS"
          :key="item"
          type="button"
          class="chip"
          :class="{ 'chip-active': category === item }"
          @click="selectCategory(item)"
        >
          {{ item }}
        </button>
      </div>

      <div class="flex flex-wrap items-center gap-3">
        <label class="flex items-center gap-2 text-[11px] text-white/35">
          平台
          <select
            :value="platform"
            class="rounded-lg border border-white/10 bg-slate-950/50 px-3 py-1.5 text-xs text-white/70 outline-none focus:border-sky-300/30"
            @change="onPlatformChange"
          >
            <option value="">全部</option>
            <option v-for="item in PLATFORM_OPTIONS" :key="item" :value="item">{{ item }}</option>
          </select>
        </label>

        <label class="flex items-center gap-2 text-[11px] text-white/35">
          排序
          <select
            :value="sort"
            class="rounded-lg border border-white/10 bg-slate-950/50 px-3 py-1.5 text-xs text-white/70 outline-none focus:border-sky-300/30"
            @change="onSortChange"
          >
            <option value="updated_at">最近更新</option>
            <option value="views">最多浏览</option>
          </select>
        </label>
      </div>
    </div>

    <div
      v-else
      class="mt-5 rounded-xl border border-sky-300/15 bg-sky-400/[0.06] px-4 py-2.5 text-[11px] text-sky-100/60"
    >
      标签 / 公司搜索模式下暂不支持叠加分类与平台筛选。
    </div>

    <!-- 列表 -->
    <div v-if="pending && games.length === 0" class="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
      <div
        v-for="n in 10"
        :key="n"
        class="animate-pulse overflow-hidden rounded-3xl border border-white/10 bg-white/[0.05]"
      >
        <div class="aspect-[2/3] bg-white/[0.04]" />
        <div class="space-y-2 p-4">
          <div class="h-3 w-3/4 rounded bg-white/10" />
          <div class="h-2.5 w-1/2 rounded bg-white/5" />
        </div>
      </div>
    </div>

    <EmptyState
      v-else-if="error && games.length === 0"
      class="mt-10"
      title="游戏列表加载失败"
      description="请确认后端服务已启动，或稍后重试。"
      image="/status/1.png"
      retryable
      @retry="refresh()"
    />

    <EmptyState
      v-else-if="games.length === 0"
      class="mt-10"
      title="没有找到匹配的游戏"
      :description="keyword ? '换一个关键词，或清除搜索条件后再看看。' : '换个分类，或者成为第一个发布作品的人。'"
      image="/status/2.png"
    >
      <NuxtLink to="/publish" class="btn-primary mt-5">发布游戏</NuxtLink>
    </EmptyState>

    <div v-else class="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
      <GameCard v-for="(game, index) in games" :key="game.id" :item="game" :index="index" />
    </div>

    <PaginationBar
      :page="page"
      :total-pages="totalPages"
      @update:page="updateQuery({ page: $event === 1 ? undefined : $event })"
    />
  </div>
</template>