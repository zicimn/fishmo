<script setup lang="ts">
import type { GalItem } from '~/types'

const props = defineProps<{
  item: GalItem
  index?: number
}>()

const initial = computed(() => props.item.name.trim().charAt(0) || '游')
</script>

<template>
  <NuxtLink
    :to="`/galgame/${item.id}`"
    class="group animate-rise relative flex flex-col overflow-hidden rounded-3xl border border-white/10 bg-white/[0.06] shadow-[0_12px_40px_-16px_rgba(2,6,23,0.9)] backdrop-blur-2xl transition duration-500 hover:-translate-y-1.5 hover:border-white/25 hover:shadow-[0_24px_70px_-20px_rgba(2,6,23,0.95)] motion-reduce:transition-none motion-reduce:hover:translate-y-0"
    :style="{ animationDelay: `${Math.min(index ?? 0, 8) * 60}ms` }"
  >
    <div class="relative aspect-[2/3] overflow-hidden">
      <img
        v-if="item.cover"
        :src="item.cover"
        :alt="item.name"
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
      <div class="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent" />

      <span
        v-if="item.category"
        class="absolute left-3 top-3 rounded-full border border-white/15 bg-slate-950/55 px-2.5 py-1 text-[10px] text-white/75 backdrop-blur-md"
      >
        {{ item.category }}
      </span>
    </div>

    <div class="relative -mt-6 flex min-w-0 flex-col p-4">
      <h2 class="line-clamp-2 text-sm font-semibold leading-snug text-white">
        {{ item.name }}
      </h2>
      <div class="mt-2.5 flex items-center justify-between text-[11px] text-white/40">
        <span class="inline-flex min-w-0 items-center gap-1.5">
          <img
            v-if="item.avatar"
            :src="item.avatar"
            alt=""
            class="h-4 w-4 rounded-full object-cover ring-1 ring-white/10"
          />
          <span class="truncate">{{ item.author }}</span>
        </span>
        <span class="shrink-0 tabular-nums">{{ item.views }} 浏览</span>
      </div>
    </div>
  </NuxtLink>
</template>