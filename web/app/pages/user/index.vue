<script setup lang="ts">
// 兼容旧链接：前台登录已改为全局弹窗，这里打开弹窗后回首页。
const { openAuth } = useAuthDialog()

onMounted(() => {
  openAuth('login')
  navigateTo('/')
})
</script>

<template>
  <div class="mx-auto flex min-h-[50vh] max-w-3xl items-center justify-center px-4">
    <p class="animate-pulse text-xs text-white/35">正在打开登录面板…</p>
  </div>
</template>