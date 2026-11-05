<script setup lang="ts">
import type { ArticleDetail } from '~/types'
import { describeError } from '~/utils/api'
import { formatDate, formatDateTime } from '~/utils/date'
import { renderMarkdown } from '~/utils/markdown'

const route = useRoute()
const api = useApi()
const { user } = useAuth()

const id = computed(() => Number(route.params.id))

const { data: article, pending, error, refresh } = await useAsyncData<ArticleDetail>(
  () => `article-${id.value}`,
  () => api.get<ArticleDetail>(`/api/v1/article/${id.value}`),
  { watch: [id] },
)

useHead(() => ({
  title: article.value ? `${article.value.title} · Fishmo` : '文章 · Fishmo',
  meta: article.value
    ? [{ name: 'description', content: article.value.content.slice(0, 120) }]
    : [],
}))

const html = computed(() => renderMarkdown(article.value?.content))
const images = computed(() => article.value?.images ?? [])

const mounted = ref(false)
onMounted(() => {
  mounted.value = true
})

const canEdit = computed(
  () =>
    mounted.value &&
    Boolean(user.value) &&
    (user.value!.id === article.value?.author_id || user.value!.is_admin),
)

const lightboxOpen = ref(false)
const lightboxIndex = ref(0)
const lightboxImages = computed(() => images.value)

function openImage(index: number) {
  lightboxIndex.value = index
  lightboxOpen.value = true
}
</script>

<template>
  <div class="mx-auto max-w-4xl px-4 pb-20 pt-8 sm:px-6">
    <nav class="flex items-center gap-2 text-[11px] text-white/30" aria-label="面包屑">
      <NuxtLink to="/" class="transition hover:text-white/70">首页</NuxtLink>
      <span>/</span>
      <NuxtLink to="/articles" class="transition hover:text-white/70">文章</NuxtLink>
      <span>/</span>
      <span class="truncate text-white/50">{{ article?.title ?? '详情' }}</span>
    </nav>

    <div v-if="pending && !article" class="mt-6 animate-pulse" aria-hidden="true">
      <div class="h-4 w-24 rounded bg-white/10" />
      <div class="mt-4 h-9 w-3/4 rounded bg-white/10" />
      <div class="mt-3 h-3 w-1/2 rounded bg-white/5" />
      <div class="mt-6 aspect-[21/9] rounded-3xl bg-white/[0.05]" />
      <div class="mt-8 space-y-3">
        <div class="h-3 w-full rounded bg-white/5" />
        <div class="h-3 w-11/12 rounded bg-white/5" />
        <div class="h-3 w-4/5 rounded bg-white/5" />
      </div>
    </div>

    <EmptyState
      v-else-if="error && !article"
      class="mt-10"
      title="无法打开这篇文章"
      :description="describeError(error)"
      image="/status/1.png"
      retryable
      @retry="refresh()"
    >
      <NuxtLink to="/articles" class="btn-ghost mt-5">返回文章列表</NuxtLink>
    </EmptyState>

    <article v-else-if="article">
      <header class="mt-6">
        <div class="flex flex-wrap items-center gap-1.5">
          <NuxtLink
            v-for="category in article.category"
            :key="category"
            :to="`/articles?category=${encodeURIComponent(category)}`"
            class="rounded-full border border-sky-300/20 bg-sky-400/10 px-2.5 py-1 text-[10px] text-sky-100/80 transition hover:bg-sky-400/15"
          >
            {{ category }}
          </NuxtLink>
          <span
            v-if="!article.status"
            class="rounded-full border border-amber-300/25 bg-amber-400/15 px-2.5 py-1 text-[10px] text-amber-100/90"
          >
            已隐藏
          </span>
        </div>

        <h1 class="mt-4 text-2xl font-semibold leading-tight text-white sm:text-4xl">
          {{ article.title }}
        </h1>

        <div class="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-[11px] text-white/35">
          <span class="inline-flex items-center gap-1.5">
            <img
              v-if="article.author_avatar"
              :src="article.author_avatar"
              alt=""
              class="h-5 w-5 rounded-full object-cover ring-1 ring-white/10"
            />
            <NuxtLink :to="`/user/${article.author_id}`" class="transition hover:text-white/70">
              {{ article.author_name }}
            </NuxtLink>
          </span>
          <time :datetime="article.created_at">{{ formatDate(article.created_at) }}</time>
          <span class="tabular-nums">{{ article.views }} 次浏览</span>
          <span class="tabular-nums">{{ article.comment_count }} 条评论</span>
          <NuxtLink
            v-if="canEdit"
            :to="`/manage/article/${article.id}`"
            class="ml-auto text-sky-200/60 transition hover:text-white"
          >
            编辑文章
          </NuxtLink>
        </div>
      </header>

      <div
        v-if="article.cover"
        class="mt-6 overflow-hidden rounded-3xl border border-white/10"
      >
        <img
          :src="article.cover"
          :alt="article.title"
          class="aspect-[16/9] w-full object-cover sm:aspect-[21/9]"
        />
      </div>

      <div class="article-content mt-8" v-html="html" />

      <div v-if="article.tag.length" class="mt-8 flex flex-wrap items-center gap-2 border-t border-white/5 pt-6">
        <span class="section-kicker mr-1">TAGS</span>
        <span
          v-for="tag in article.tag"
          :key="tag"
          class="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[10px] text-white/45"
        >
          # {{ tag }}
        </span>
      </div>

      <section v-if="images.length" class="mt-10">
        <h2 class="text-sm font-medium tracking-wide text-white/70">插图画廊</h2>
        <div class="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
          <button
            v-for="(image, index) in images"
            :key="`${image}-${index}`"
            type="button"
            class="group relative aspect-[4/3] overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04]"
            @click="openImage(index)"
          >
            <img
              :src="image"
              alt=""
              loading="lazy"
              class="h-full w-full object-cover transition duration-500 group-hover:scale-105"
            />
          </button>
        </div>
      </section>

      <CommentList :target-id="article.id" type="article" />

      <p class="mt-10 text-[10px] text-white/20">
        发布于 {{ formatDateTime(article.created_at) }}
        <span v-if="article.updated_at !== article.created_at">
          · 更新于 {{ formatDateTime(article.updated_at) }}
        </span>
      </p>

      <ImageLightbox
        v-model:index="lightboxIndex"
        :open="lightboxOpen"
        :images="lightboxImages"
        @close="lightboxOpen = false"
      />
    </article>
  </div>
</template>