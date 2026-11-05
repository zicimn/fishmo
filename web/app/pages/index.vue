<script setup lang="ts">
import type { ArticlePreview, GalItem, PageData } from '~/types'

useHead({ title: 'Fishmo · Galgame 信息发布社区' })

const api = useApi()

const { data: galData } = await useAsyncData<PageData<GalItem>>(
  'home-games',
  () => api.get<PageData<GalItem>>('/api/v1/galgame/', { page: 1, size: 8, sort: 'updated_at' }),
  { default: () => ({ total: 0, items: [] }) },
)

const { data: articleData } = await useAsyncData<PageData<ArticlePreview>>(
  'home-articles',
  () => api.get<PageData<ArticlePreview>>('/api/v1/article/', { page: 1, size: 4 }),
  { default: () => ({ total: 0, items: [] }) },
)

const games = computed(() => galData.value?.items ?? [])
const articles = computed(() => articleData.value?.items ?? [])
const featured = computed(() => games.value[0] ?? null)
const gallery = computed(() => games.value.slice(1, 7))
</script>

<template>
  <div class="mx-auto max-w-7xl px-4 pb-20 pt-8 sm:px-6 sm:pt-12">
    <!-- Hero -->
    <section class="relative overflow-hidden rounded-[2rem] border border-white/10 bg-white/[0.06] backdrop-blur-2xl">
      <div class="pointer-events-none absolute inset-0">
        <div class="absolute -left-24 -top-24 h-72 w-72 rounded-full bg-sky-500/15 blur-3xl" />
        <div class="absolute -bottom-32 right-0 h-80 w-80 rounded-full bg-fuchsia-500/10 blur-3xl" />
        <div class="absolute inset-x-10 top-0 h-px bg-gradient-to-r from-transparent via-white/40 to-transparent" />
      </div>

      <div class="relative grid gap-8 p-6 sm:p-10 lg:grid-cols-[minmax(0,1fr)_320px] lg:items-center lg:p-12">
        <div class="animate-rise">
          <p class="section-kicker">FISHMO · GALGAME COMMUNITY</p>
          <h1 class="mt-4 max-w-2xl text-3xl font-semibold leading-tight text-white sm:text-5xl">
            在故事里，
            <span class="bg-gradient-to-r from-sky-300 via-indigo-200 to-fuchsia-300 bg-clip-text text-transparent">
              找到另一个世界
            </span>
          </h1>
          <p class="mt-5 max-w-xl text-sm leading-relaxed text-white/45">
            记录你喜欢的 Galgame，分享攻略与感想，也把那些难以忘怀的瞬间留给后来的人。
          </p>

          <div class="mt-8 flex flex-wrap items-center gap-3">
            <NuxtLink to="/games" class="btn-primary px-6 py-3 text-sm">
              开始探索
            </NuxtLink>
            <NuxtLink to="/articles" class="btn-ghost px-6 py-3 text-sm">
              阅读文章
            </NuxtLink>
            <NuxtLink
              v-if="featured"
              :to="`/galgame/${featured.id}`"
              class="group inline-flex items-center gap-1.5 px-2 text-xs text-white/40 transition hover:text-white/80"
            >
              随机看看
              <span class="transition group-hover:translate-x-0.5">→</span>
            </NuxtLink>
          </div>

          <dl class="mt-10 flex flex-wrap gap-x-10 gap-y-4">
            <div>
              <dt class="text-[10px] uppercase tracking-[0.25em] text-white/30">Games</dt>
              <dd class="mt-1 text-2xl font-semibold tabular-nums text-white/85">
                {{ galData?.total ?? 0 }}
              </dd>
            </div>
            <div>
              <dt class="text-[10px] uppercase tracking-[0.25em] text-white/30">Articles</dt>
              <dd class="mt-1 text-2xl font-semibold tabular-nums text-white/85">
                {{ articleData?.total ?? 0 }}
              </dd>
            </div>
            <div>
              <dt class="text-[10px] uppercase tracking-[0.25em] text-white/30">Open Source</dt>
              <dd class="mt-1 text-sm text-white/55">
                <a
                  href="https://github.com/zicimn/fishmo"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="transition hover:text-white"
                >
                  GitHub ↗
                </a>
              </dd>
            </div>
          </dl>
        </div>

        <NuxtLink
          v-if="featured"
          :to="`/galgame/${featured.id}`"
          class="group relative mx-auto w-full max-w-[280px] animate-rise overflow-hidden rounded-2xl border border-white/15 shadow-[0_30px_80px_-30px_rgba(2,6,23,1)]"
          style="animation-delay: 120ms"
        >
          <img
            v-if="featured.cover"
            :src="featured.cover"
            :alt="featured.name"
            class="aspect-[2/3] w-full object-cover transition duration-700 group-hover:scale-105"
          />
          <div class="absolute inset-0 bg-gradient-to-t from-slate-950 via-slate-950/20 to-transparent" />
          <div class="absolute inset-x-0 bottom-0 p-4">
            <p class="text-[10px] uppercase tracking-[0.25em] text-sky-200/60">Latest update</p>
            <p class="mt-1 line-clamp-2 text-sm font-semibold text-white">{{ featured.name }}</p>
            <p class="mt-1 text-[11px] text-white/40">by {{ featured.author }}</p>
          </div>
        </NuxtLink>

        <div
          v-else
          class="mx-auto flex aspect-[2/3] w-full max-w-[280px] flex-col items-center justify-center rounded-2xl border border-dashed border-white/15 bg-white/[0.03] text-center"
        >
          <p class="text-4xl text-white/15">✦</p>
          <p class="mt-3 text-xs text-white/35">还没有游戏</p>
          <NuxtLink to="/publish" class="mt-3 text-[11px] text-sky-200/70 hover:text-white">
            发布第一部作品
          </NuxtLink>
        </div>
      </div>
    </section>

    <!-- 最新游戏 -->
    <section class="mt-16">
      <div class="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p class="section-kicker">RECENTLY UPDATED</p>
          <h2 class="mt-2 text-xl font-semibold text-white">最近更新的游戏</h2>
        </div>
        <NuxtLink to="/games" class="group text-xs text-white/40 transition hover:text-white">
          全部游戏
          <span class="inline-block transition group-hover:translate-x-0.5">→</span>
        </NuxtLink>
      </div>

      <div v-if="gallery.length" class="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
        <GameCard v-for="(game, index) in gallery" :key="game.id" :item="game" :index="index" />
      </div>
      <EmptyState
        v-else
        class="mt-6"
        title="还没有已公开的游戏"
        description="新发布的游戏需要管理员审核通过后才会出现在这里。"
        image="/status/2.png"
      >
        <NuxtLink to="/publish" class="btn-primary mt-5">发布游戏</NuxtLink>
      </EmptyState>
    </section>

    <!-- 最新文章 -->
    <section class="mt-16">
      <div class="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p class="section-kicker">JOURNAL</p>
          <h2 class="mt-2 text-xl font-semibold text-white">来自社区的文章</h2>
        </div>
        <NuxtLink to="/articles" class="group text-xs text-white/40 transition hover:text-white">
          全部文章
          <span class="inline-block transition group-hover:translate-x-0.5">→</span>
        </NuxtLink>
      </div>

      <div v-if="articles.length" class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <ArticleCard
          v-for="(article, index) in articles"
          :key="article.id"
          :article="article"
          :index="index"
        />
      </div>
      <EmptyState
        v-else
        class="mt-6"
        title="还没有文章"
        description="写下第一篇攻略或感想，让社区热闹起来。"
        image="/status/2.png"
      >
        <NuxtLink to="/publish?tab=article" class="btn-primary mt-5">写文章</NuxtLink>
      </EmptyState>
    </section>

    <!-- 关于入口 -->
    <section class="mt-16 overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-r from-sky-500/[0.08] via-white/[0.04] to-fuchsia-500/[0.08] px-6 py-10 backdrop-blur-2xl sm:px-10">
      <div class="flex flex-wrap items-center justify-between gap-6">
        <div class="max-w-xl">
          <p class="section-kicker">ABOUT FISHMO</p>
          <h2 class="mt-2 text-lg font-semibold text-white">一个由 Galgame 爱好者维护的小站</h2>
          <p class="mt-2 text-xs leading-relaxed text-white/40">
            收录作品信息、分享资源链接、记录评论与文章。所有内容来自社区成员，欢迎一起完善。
          </p>
        </div>
        <NuxtLink to="/about" class="btn-ghost shrink-0 px-6">了解更多</NuxtLink>
      </div>
    </section>
  </div>
</template>