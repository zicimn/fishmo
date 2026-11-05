<script setup lang="ts">
const { background, brightness, alpha } = useAppearance()
</script>

<template>
  <div class="relative min-h-screen">
    <!-- 全屏背景：玻璃卡片需要“背后有东西可透”，所以背景图固定铺满整屏 -->
    <div class="fixed inset-0 -z-10 overflow-hidden">
      <img
        :src="background"
        alt=""
        class="h-full w-full scale-105 object-cover transition-[filter] duration-300"
        :style="{ filter: `brightness(${brightness})` }"
      />
      <div class="absolute inset-0 bg-slate-950" :style="{ opacity: alpha }" />
      <div
        class="absolute inset-0 bg-[radial-gradient(120%_80%_at_50%_-10%,rgba(56,189,248,0.18),transparent_55%)]"
      />
      <div class="absolute inset-0 bg-gradient-to-b from-slate-950/10 via-transparent to-slate-950/80" />
    </div>

    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>

    <AuthDialog />
    <ConfirmHost />
    <ToastHost />
  </div>
</template>