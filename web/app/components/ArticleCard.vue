<script setup lang="ts">
import type { ArticlePreview } from '~/types'
import { formatDate } from '~/utils/date'

const props = defineProps<{
  article: ArticlePreview
  index?: number
}>()

const initial = computed(() => props.article.title.trim().charAt(0) || '文')
</script>

<template>
  <NuxtLink
    :to="`/article/${article.id}`"
    class="group animate-rise flex flex-col overflow-hidden rounded-3xl border border-white/10 bg-white/[0.06] shadow-[0_12px_40px_-16px_rgba(2,6,23,0.9)] backdrop-blur-2xl transition duration-500 hover:-translate-y-1.5 hover:border-white/25 hover:shadow-[0_24px_70px_-20px_rgba(2,6,23,0.95)] motion-reduce:transition-none motion-reduce:hover:translate-y-0"
    :style="{ animationDelay: `${Math.min(index ?? 0, 8) * 60}ms` }"
  >
    <div class="relative aspect-[16/10] overflow-hidden">
      <img
        v-if="article.cover"
        :src="article.cover"
        :alt="article.title"
        loading="lazy"
        class="absolute inset-0 h-full w-full object-cover transition-transform duration-700 group-hover:scale-[1.05]"
      />
      <div
        v-else
        class="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-sky-500/35 via-indigo-500/25 to-fuchsia-500/35"
        aria-hidden="true"
      >
        <span class="text-6xl font-semibold text-white/20">{{ initial }}</span>
      </div>
      <div class="absolute inset-0 bg-gradient-to-t from-slate-950/70 via-transparent to-transparent" />
      <div
        class="pointer-events-none absolute inset-x-6 top-0 h-px bg-gradient-to-r from-transparent via-white/50 to-transparent"
      />
    </div>

    <div class="flex flex-1 flex-col p-5">
      <div class="flex flex-wrap gap-1.5">
        <span
          v-for="category in article.category"
          :key="category"
          class="rounded-full border border-sky-300/15 bg-sky-400/10 px-2 py-0.5 text-[10px] text-sky-100/70"
        >
          {{ category }}
        </span>
      </div>

      <h2 class="mt-2.5 line-clamp-2 text-base font-semibold leading-snug text-white">
        {{ article.title }}
      </h2>

      <div class="mt-auto flex items-center justify-between pt-4 text-[11px] text-white/40">
        <time :datetime="article.created_at">{{ formatDate(article.created_at) }}</time>
        <span class="flex items-center gap-3 tabular-nums">
          <span>{{ article.views }} 浏览</span>
          <span>{{ article.comcnt }} 评论</span>
        </span>
      </div>
    </div>
  </NuxtLink>
</template>