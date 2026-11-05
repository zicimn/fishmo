<script setup lang="ts">
import type { NuxtError } from '#app'

const props = defineProps<{ error: NuxtError }>()

const is404 = computed(() => props.error.statusCode === 404)
const message = computed(() =>
  is404.value ? '这个页面不存在' : '页面出了点问题',
)
const detail = computed(() =>
  is404.value
    ? '它可能已被删除，或者链接地址有误。'
    : '请稍后重试；如果问题持续出现，可以回到首页重新开始。',
)

function goHome() {
  clearError({ redirect: '/' })
}
</script>

<template>
  <div class="relative flex min-h-screen flex-col">
    <div class="fixed inset-0 -z-10 overflow-hidden">
      <img src="/background/2.jpg" alt="" class="h-full w-full scale-105 object-cover brightness-100" />
      <div class="absolute inset-0 bg-slate-950/65" />
      <div class="absolute inset-0 bg-gradient-to-b from-slate-950/10 via-transparent to-slate-950/80" />
    </div>

    <SiteHeader />

    <main class="mx-auto grid w-full max-w-6xl flex-1 place-items-center px-5 py-20 sm:px-8">
      <section class="animate-rise w-full max-w-xl rounded-3xl border border-white/10 bg-white/[0.06] px-6 py-16 text-center backdrop-blur-2xl">
        <p class="text-[11px] uppercase tracking-[0.35em] text-sky-200/50">
          {{ props.error.statusCode || 500 }}
        </p>
        <h1 class="mt-3 text-2xl font-semibold tracking-tight text-white sm:text-3xl">
          {{ message }}
        </h1>
        <p class="mt-3 text-xs leading-relaxed text-white/40">{{ detail }}</p>
        <div class="mt-8 flex items-center justify-center gap-3">
          <button type="button" class="btn-primary" @click="goHome">回到首页</button>
          <NuxtLink to="/games" class="btn-ghost">浏览游戏</NuxtLink>
        </div>
      </section>
    </main>

    <SiteFooter />
  </div>
</template>