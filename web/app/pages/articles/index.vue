<script setup lang="ts">
import type { ArticlePreview, PageData } from '~/types'
import { ARTICLE_CATEGORY_OPTIONS } from '~/types'

useHead({ title: '全部文章 · Fishmo' })

const api = useApi()
const route = useRoute()
const router = useRouter()

const category = computed(() => String(route.query.category ?? ''))
const page = computed(() => Math.max(1, Number(route.query.page) || 1))
const pageSize = 12

const { data, pending, error, refresh } = await useAsyncData<PageData<ArticlePreview>>(
  () => `articles-${route.fullPath}`,
  () =>
    api.get<PageData<ArticlePreview>>('/api/v1/article/', {
      page: page.value,
      size: pageSize,
      category: category.value || undefined,
    }),
  {
    watch: [() => route.fullPath],
    default: () => ({ total: 0, items: [] }),
  },
)

const articles = computed(() => data.value?.items ?? [])
const total = computed(() => data.value?.total ?? 0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))

function setCategory(value: string) {
  const next: Record<string, string> = {}
  for (const [key, item] of Object.entries(route.query)) {
    if (typeof item === 'string' && item && key !== 'page') next[key] = item
  }
  if (value) next.category = value
  router.push({ query: next })
}

function setPage(value: number) {
  const next: Record<string, string> = {}
  for (const [key, item] of Object.entries(route.query)) {
    if (typeof item === 'string' && item && key !== 'page') next[key] = item
  }
  if (value > 1) next.page = String(value)
  router.push({ query: next })
}
</script>

<template>
  <div class="mx-auto max-w-7xl px-4 pb-20 pt-10 sm:px-6">
    <header class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="section-kicker">JOURNAL</p>
        <h1 class="mt-2 text-2xl font-semibold text-white sm:text-3xl">全部文章</h1>
        <p class="mt-2 text-xs text-white/35">
          攻略、资讯、教程与随笔，共
          <span class="tabular-nums text-white/60">{{ total }}</span> 篇
        </p>
      </div>
      <NuxtLink to="/publish?tab=article" class="btn-primary px-5 py-2.5">写文章</NuxtLink>
    </header>

    <div class="no-scrollbar -mx-1 mt-7 flex gap-2 overflow-x-auto px-1 pb-1">
      <button
        type="button"
        class="chip"
        :class="{ 'chip-active': !category }"
        @click="setCategory('')"
      >
        全部
      </button>
      <button
        v-for="item in ARTICLE_CATEGORY_OPTIONS"
        :key="item"
        type="button"
        class="chip"
        :class="{ 'chip-active': category === item }"
        @click="setCategory(item)"
      >
        {{ item }}
      </button>
    </div>

    <div
      v-if="pending && articles.length === 0"
      class="mt-8 grid animate-pulse gap-4 sm:grid-cols-2 lg:grid-cols-4"
      aria-hidden="true"
    >
      <div
        v-for="n in 8"
        :key="n"
        class="overflow-hidden rounded-3xl border border-white/10 bg-white/[0.05]"
      >
        <div class="aspect-[16/10] bg-white/[0.04]" />
        <div class="space-y-2 p-5">
          <div class="h-4 w-4/5 rounded bg-white/10" />
          <div class="h-4 w-3/5 rounded bg-white/10" />
          <div class="h-2.5 w-1/3 rounded bg-white/5" />
        </div>
      </div>
    </div>

    <EmptyState
      v-else-if="error && articles.length === 0"
      class="mt-10"
      title="文章列表加载失败"
      description="请确认后端服务已启动，或稍后重试。"
      image="/status/1.png"
      retryable
      @retry="refresh()"
    />

    <EmptyState
      v-else-if="articles.length === 0"
      class="mt-10"
      title="这个分类下还没有文章"
      description="换个分类看看，或者写下第一篇。"
      image="/status/2.png"
    >
      <NuxtLink to="/publish?tab=article" class="btn-primary mt-5">写文章</NuxtLink>
    </EmptyState>

    <div v-else class="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <ArticleCard
        v-for="(article, index) in articles"
        :key="article.id"
        :article="article"
        :index="index"
      />
    </div>

    <PaginationBar :page="page" :total-pages="totalPages" @update:page="setPage" />
  </div>
</template>