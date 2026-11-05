<script setup lang="ts">
import type { ArticleManageItem, PageData } from '~/types'
import { describeError } from '~/utils/api'
import { formatDate } from '~/utils/date'

const api = useApi()
const toast = useToast()
const confirm = useConfirm()

const page = ref(1)
const size = 10

const { data, pending, error, refresh } = await useAsyncData<PageData<ArticleManageItem>>(
  () => `manage-articles-${page.value}`,
  () => api.get<PageData<ArticleManageItem>>('/api/v1/article/manage', { page: page.value, size }),
  {
    server: false,
    watch: [page],
    default: () => ({ total: 0, items: [] }),
  },
)

const articles = computed(() => data.value?.items ?? [])
const total = computed(() => data.value?.total ?? 0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / size)))

async function remove(article: ArticleManageItem) {
  const ok = await confirm.confirm({
    title: '删除文章',
    message: `「${article.title}」及其评论都会被删除，且无法恢复。`,
    confirmText: '确认删除',
    danger: true,
  })
  if (!ok) return
  try {
    await api.del('/api/v1/article/delete', { id: article.id })
    toast.success('文章已删除')
    if (articles.value.length === 1 && page.value > 1) page.value -= 1
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
        共 <span class="tabular-nums text-white/60">{{ total }}</span> 篇文章
      </p>
      <NuxtLink :to="{ path: '/publish', query: { tab: 'article' } }" class="btn-primary px-4 py-2">
        写新文章
      </NuxtLink>
    </div>

    <div v-if="pending && articles.length === 0" class="mt-5 space-y-2">
      <div
        v-for="n in 4"
        :key="n"
        class="h-24 animate-pulse rounded-2xl border border-white/10 bg-white/[0.05]"
      />
    </div>

    <div v-else-if="error && articles.length === 0" class="glass-panel mt-5 px-5 py-10 text-center">
      <p class="text-xs text-white/45">文章列表加载失败</p>
      <button type="button" class="btn-ghost mt-4 px-4 py-1.5" @click="refresh()">重试</button>
    </div>

    <div v-else-if="articles.length === 0" class="glass-panel mt-5 px-5 py-12 text-center">
      <p class="text-xs text-white/40">你还没有写过文章。</p>
      <NuxtLink :to="{ path: '/publish', query: { tab: 'article' } }" class="btn-primary mt-5">
        写第一篇文章
      </NuxtLink>
    </div>

    <ul v-else class="mt-5 space-y-2">
      <li
        v-for="article in articles"
        :key="article.id"
        class="glass-panel flex flex-wrap items-center gap-4 p-3.5 transition hover:border-white/20 sm:flex-nowrap"
      >
        <NuxtLink
          :to="`/article/${article.id}`"
          class="h-20 w-32 shrink-0 overflow-hidden rounded-xl border border-white/10 bg-white/[0.04]"
        >
          <img
            v-if="article.cover"
            :src="article.cover"
            :alt="article.title"
            loading="lazy"
            class="h-full w-full object-cover"
          />
        </NuxtLink>

        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-1.5">
            <span
              v-for="category in article.category"
              :key="category"
              class="rounded-full border border-sky-300/15 bg-sky-400/10 px-2 py-0.5 text-[10px] text-sky-100/70"
            >
              {{ category }}
            </span>
            <span
              class="rounded-full border px-2 py-0.5 text-[10px]"
              :class="
                article.status
                  ? 'border-emerald-300/20 bg-emerald-400/10 text-emerald-100/80'
                  : 'border-amber-300/20 bg-amber-400/10 text-amber-100/80'
              "
            >
              {{ article.status ? '已公开' : '已隐藏' }}
            </span>
          </div>
          <NuxtLink
            :to="`/article/${article.id}`"
            class="mt-1.5 line-clamp-1 text-xs font-medium text-white/80 transition hover:text-white"
          >
            {{ article.title }}
          </NuxtLink>
          <p class="mt-1 flex flex-wrap gap-3 text-[10px] text-white/30">
            <span :title="article.updated_at">更新于 {{ formatDate(article.updated_at) }}</span>
            <span class="tabular-nums">{{ article.views }} 浏览</span>
          </p>
        </div>

        <div class="flex shrink-0 items-center gap-1.5">
          <NuxtLink
            :to="`/manage/article/${article.id}`"
            class="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[10px] text-white/55 transition hover:bg-white/[0.1] hover:text-white"
          >
            编辑
          </NuxtLink>
          <button
            type="button"
            class="rounded-lg border border-rose-400/20 bg-rose-500/[0.08] px-3 py-1.5 text-[10px] text-rose-200/70 transition hover:bg-rose-500/15 hover:text-rose-100"
            @click="remove(article)"
          >
            删除
          </button>
        </div>
      </li>
    </ul>

    <PaginationBar v-model:page="page" :total-pages="totalPages" />
  </section>
</template>