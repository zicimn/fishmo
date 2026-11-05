<script setup lang="ts">
useHead({ title: '关于 · Fishmo' })

const features = [
  {
    title: '发布游戏',
    description: '记录作品的名称、简介、封面、截图、平台与标签，建立属于社区的 Galgame 资料库。',
  },
  {
    title: '分享文章',
    description: '用 Markdown 写攻略、评测或随笔，支持分类、标签、封面与插图画廊。',
  },
  {
    title: '评论互动',
    description: '在游戏与文章下留言，支持两层嵌套回复，让讨论保持清晰。',
  },
  {
    title: '收藏与资源',
    description: '收藏喜欢的作品，也可以分享网盘链接与提取码，方便同好找到资源。',
  },
]

const stack = [
  'Python 3.11',
  'FastAPI',
  'SQLAlchemy 2.0',
  'MySQL',
  'Redis',
  'Pydantic v2',
  'Cloudinary',
  'Nuxt 4',
  'Vue 3',
  'TypeScript',
  'Tailwind CSS',
  'Markdown-it',
]
</script>

<template>
  <div class="mx-auto max-w-4xl px-4 pb-20 pt-10 sm:px-6">
    <header class="glass-card relative overflow-hidden p-7 sm:p-10">
      <div class="pointer-events-none absolute -right-20 -top-20 h-64 w-64 rounded-full bg-sky-500/10 blur-3xl" />
      <div class="relative">
        <p class="section-kicker">ABOUT US</p>
        <h1 class="mt-3 text-2xl font-semibold text-white sm:text-4xl">
          fishmo — 一个 Galgame 信息发布社区
        </h1>
        <p class="mt-4 max-w-2xl text-sm leading-7 text-white/45">
          fishmo 是一个由爱好者维护的 Galgame 信息发布社区与文章博客平台。这里不提供游戏本体下载，
          而是记录作品资料、汇总社区分享的资源链接，并让大家用评论和文章留下自己的感受。
        </p>
        <div class="mt-6 flex flex-wrap gap-3">
          <a
            href="https://github.com/zicimn/fishmo"
            target="_blank"
            rel="noopener noreferrer"
            class="btn-primary px-5"
          >
            GitHub 开源地址 ↗
          </a>
          <a href="mailto:fwioe77@gmail.com" class="btn-ghost px-5">
            联系邮箱
          </a>
        </div>
      </div>
    </header>

    <section class="mt-10">
      <p class="section-kicker">FEATURES</p>
      <h2 class="mt-2 text-xl font-semibold text-white">这里可以做什么</h2>
      <div class="mt-5 grid gap-4 sm:grid-cols-2">
        <article
          v-for="(feature, index) in features"
          :key="feature.title"
          class="glass-panel animate-rise p-5"
          :style="{ animationDelay: `${index * 70}ms` }"
        >
          <h3 class="text-sm font-medium text-white/85">{{ feature.title }}</h3>
          <p class="mt-2 text-xs leading-relaxed text-white/40">{{ feature.description }}</p>
        </article>
      </div>
    </section>

    <section class="mt-10">
      <p class="section-kicker">TECH STACK</p>
      <h2 class="mt-2 text-xl font-semibold text-white">技术栈</h2>
      <div class="mt-4 flex flex-wrap gap-2">
        <span
          v-for="item in stack"
          :key="item"
          class="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1.5 text-[11px] text-white/50"
        >
          {{ item }}
        </span>
      </div>
    </section>

    <section class="mt-10 rounded-3xl border border-white/10 bg-white/[0.04] p-6 sm:p-8">
      <p class="section-kicker">CONTACT</p>
      <h2 class="mt-2 text-lg font-semibold text-white">联系与反馈</h2>
      <p class="mt-2 max-w-2xl text-xs leading-relaxed text-white/40">
        如果你发现问题、想补充游戏资料，或者有合作想法，欢迎通过邮件或 GitHub Issue 联系。
      </p>
      <div class="mt-4 flex flex-wrap gap-4 text-xs">
        <a href="mailto:fwioe77@gmail.com" class="text-sky-200/70 transition hover:text-sky-100">
          fwioe77@gmail.com
        </a>
        <a
          href="https://github.com/zicimn/fishmo"
          target="_blank"
          rel="noopener noreferrer"
          class="text-sky-200/70 transition hover:text-sky-100"
        >
          github.com/zicimn/fishmo
        </a>
      </div>
    </section>

    <p class="mt-10 text-center text-[10px] text-white/20">
      本站内容由社区成员发布，仅供学习与交流使用。
    </p>
  </div>
</template>