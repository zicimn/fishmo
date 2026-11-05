<template>
  <footer class="px-5 pb-8 pt-6 sm:px-8">
    <div
      class="mx-auto flex max-w-6xl flex-col gap-4 rounded-2xl border border-white/10 bg-white/[0.04] px-5 py-5 backdrop-blur-xl sm:flex-row sm:items-center sm:justify-between"
    >
      <div>
        <p class="text-xs font-medium tracking-wide text-white/60">
          Fishmo · Galgame 社区
        </p>
        <p class="mt-1 text-[11px] text-white/30">
          游戏资讯、资源链接与文章，一起留在时间里的玻璃碎片。
        </p>
      </div>
      <nav class="flex flex-wrap items-center gap-x-5 gap-y-2 text-[11px] text-white/40">
        <NuxtLink to="/games" class="transition hover:text-white/80">全部游戏</NuxtLink>
        <NuxtLink to="/articles" class="transition hover:text-white/80">全部文章</NuxtLink>
        <NuxtLink to="/about" class="transition hover:text-white/80">关于</NuxtLink>
        <a
          href="https://github.com/zicimn/fishmo"
          target="_blank"
          rel="noopener noreferrer"
          class="transition hover:text-white/80"
        >
          GitHub
        </a>
      </nav>
    </div>
  </footer>
</template>