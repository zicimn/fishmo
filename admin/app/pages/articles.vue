<script setup lang="ts">
import type { AdminArticle, PageData } from '~/types'
import { describeError } from '~/utils/api'
import { formatDate } from '~/utils/date'

type ArticleStatus = 'all' | 'published' | 'hidden'

const api = useAdminApi()
const toast = useToast()
const confirm = useConfirm()
const route = useRoute()
const router = useRouter()

useHead({ title: '文章管理 · Fishmo 管理端' })

const tabs: { value: ArticleStatus; label: string }[] = [
  { value: 'all', label: '全部' },
  { value: 'published', label: '已公开' },
  { value: 'hidden', label: '已隐藏' },
]

const status = computed<ArticleStatus>(() => {
  const value = String(route.query.status ?? 'all')
  return tabs.some((item) => item.value === value) ? (value as ArticleStatus) : 'all'
})

const page = ref(1)
const size = 12

const { data, pending, error, refresh } = await useAsyncData<PageData<AdminArticle>>(
  () => `admin-articles-${status.value}-${page.value}`,
  () =>
    api.get<PageData<AdminArticle>>('/api/admin/control/Articles', {
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

const articles = computed(() => data.value?.items ?? [])
const total = computed(() => data.value?.total ?? 0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / size)))

const siteBase = computed(
  () => useRuntimeConfig().public.siteBase || 'http://localhost:3000',
)

function setStatus(value: ArticleStatus) {
  if (value === status.value) return
  page.value = 1
  router.replace({ query: { status: value } })
}

async function setPublished(article: AdminArticle, value: boolean) {
  if (!value) {
    const ok = await confirm.confirm({
      title: '隐藏文章',
      message: `隐藏「${article.title}」后，访客将无法打开这篇文章，作者仍可在个人中心看到。`,
      confirmText: '确认隐藏',
      danger: true,
    })
    if (!ok) return
  }
  try {
    await api.put('/api/admin/control/UpdateArticleStatus', undefined, {
      article_id: article.id,
      status: value,
    })
    toast.success(value ? '文章已公开' : '文章已隐藏')
    refresh()
  } catch (err) {
    toast.error(describeError(err))
  }
}

async function remove(article: AdminArticle) {
  const ok = await confirm.confirm({
    title: '删除文章',
    message: `「${article.title}」及其评论都会被删除，且无法恢复。`,
    confirmText: '确认删除',
    danger: true,
  })
  if (!ok) return
  try {
    await api.del('/api/admin/control/DeleteArticle', { article_id: article.id })
    toast.success('文章已删除')
    if (articles.value.length === 1 && page.value > 1) page.value -= 1
    else refresh()
  } catch (err) {
    toast.error(describeError(err))
  }
}
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <header class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="section-kicker">ARTICLES</p>
        <h2 class="mt-2 text-xl font-semibold text-white">文章管理</h2>
        <p class="mt-1.5 text-xs text-white/35">公开、隐藏或删除社区文章。</p>
      </div>
      <p class="text-[11px] text-white/30">
        共 <span class="tabular-nums text-white/55">{{ total }}</span> 篇
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

    <div v-if="pending && articles.length === 0" class="mt-5 space-y-2">
      <div
        v-for="n in 5"
        :key="n"
        class="h-24 animate-pulse rounded-2xl border border-white/10 bg-white/[0.05]"
      />
    </div>

    <div v-else-if="error && articles.length === 0" class="glass-panel mt-5 px-5 py-10 text-center">
      <p class="text-xs text-white/45">文章列表加载失败</p>
      <button type="button" class="btn-ghost mt-4 px-4 py-1.5" @click="refresh()">重试</button>
    </div>

    <div v-else-if="articles.length === 0" class="glass-panel mt-5 px-5 py-12 text-center">
      <p class="text-xs text-white/35">这个筛选下没有文章。</p>
    </div>

    <ul v-else class="mt-5 space-y-2">
      <li
        v-for="article in articles"
        :key="article.id"
        class="glass-panel flex flex-wrap items-center gap-4 p-3.5 transition hover:border-white/20"
      >
        <img
          v-if="article.cover"
          :src="article.cover"
          :alt="article.title"
          class="h-16 w-24 shrink-0 rounded-lg object-cover ring-1 ring-white/10"
        />
        <div v-else class="grid h-16 w-24 shrink-0 place-items-center rounded-lg bg-white/[0.05] text-white/20">
          ▤
        </div>

        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <p class="truncate text-xs font-medium text-white/85">{{ article.title }}</p>
            <span
              class="rounded-full border px-2 py-0.5 text-[9px]"
              :class="
                article.status
                  ? 'border-emerald-300/20 bg-emerald-400/10 text-emerald-100/80'
                  : 'border-white/10 bg-white/[0.05] text-white/40'
              "
            >
              {{ article.status ? '已公开' : '已隐藏' }}
            </span>
          </div>
          <p class="mt-1 flex flex-wrap items-center gap-1.5 text-[9px] text-white/25">
            <span
              v-for="tag in article.category"
              :key="tag"
              class="rounded border border-white/10 bg-white/[0.04] px-1.5 py-0.5"
            >
              {{ tag }}
            </span>
          </p>
          <p class="mt-1 flex flex-wrap items-center gap-3 text-[10px] text-white/30">
            <span class="inline-flex items-center gap-1.5">
              <img
                v-if="article.avatar"
                :src="article.avatar"
                alt=""
                class="h-4 w-4 rounded-full object-cover ring-1 ring-white/10"
              />
              {{ article.author }}
            </span>
            <span>发布于 {{ formatDate(article.created_at) }}</span>
            <span class="tabular-nums">{{ article.views }} 浏览</span>
          </p>
        </div>

        <div class="flex shrink-0 flex-wrap items-center gap-1.5">
          <a
            :href="`${siteBase}/article/${article.id}`"
            target="_blank"
            rel="noopener"
            class="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[10px] text-white/50 transition hover:bg-white/[0.1] hover:text-white"
          >
            预览 ↗
          </a>
          <button
            v-if="!article.status"
            type="button"
            class="rounded-lg bg-sky-500/90 px-3 py-1.5 text-[10px] font-medium text-slate-950 transition hover:bg-sky-400"
            @click="setPublished(article, true)"
          >
            公开
          </button>
          <button
            v-else
            type="button"
            class="rounded-lg border border-amber-300/20 bg-amber-400/10 px-3 py-1.5 text-[10px] text-amber-100/80 transition hover:bg-amber-400/15"
            @click="setPublished(article, false)"
          >
            隐藏
          </button>
          <button
            type="button"
            class="rounded-lg border border-rose-400/20 bg-rose-500/[0.08] px-3 py-1.5 text-[10px] text-rose-200/75 transition hover:bg-rose-500/15"
            @click="remove(article)"
          >
            删除
          </button>
        </div>
      </li>
    </ul>

    <AdminPagination v-model:page="page" :total-pages="totalPages" :total="total" />
  </div>
</template>