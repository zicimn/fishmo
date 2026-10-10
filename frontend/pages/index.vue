<script setup lang="ts">
import type { GalItem, GalgameListQuery } from '~/types'
import { useGalgameList } from '~/composables/useGalgame'

// 热门游戏：按浏览量倒序取前 10
const popularQuery = ref<GalgameListQuery>({ page: 1, size: 10, sort: 'views' })
const { data: popular } = useGalgameList(popularQuery, { key: 'home-popular' })

// 最新发布：按更新时间倒序取前 10（默认排序）
const latestQuery = ref<GalgameListQuery>({ page: 1, size: 10 })
const { data: latest } = useGalgameList(latestQuery, { key: 'home-latest' })

const popularItems = computed(() => popular.value?.items ?? [])
const latestItems = computed(() => latest.value?.items ?? [])

// 精选：热门中浏览量最高的游戏（popularItems 已按 views 倒序，首项即最高）
const featured = computed<GalItem | null>(() => popularItems.value[0] ?? null)

const featuredInitial = computed(() => (featured.value?.author || 'U').charAt(0).toUpperCase())
</script>

<template>
  <div class="home-page">
    <!-- ===== 精选 Hero：游戏美术优先，不做巨型 CTA ===== -->
    <NuxtLink v-if="featured" :to="`/galgame/${featured.id}`" class="hero-card">
      <el-image :src="featured.cover" fit="cover" class="hero-bg" loading="eager" />
      <div class="hero-overlay" />
      <div class="hero-info">
        <span class="hero-badge">精选推荐</span>
        <h2 class="hero-title">{{ featured.name }}</h2>
        <div class="hero-meta">
          <span class="hero-author">
            <el-avatar :size="20" :src="featured.avatar || undefined">{{ featuredInitial }}</el-avatar>
            {{ featured.author }}
          </span>
          <span class="hero-stat">
            <el-icon><View /></el-icon>
            {{ featured.views }} 浏览
          </span>
        </div>
      </div>
    </NuxtLink>

    <!-- ===== 热门游戏：横向滚动 + 序号突出前 3 ===== -->
    <template v-if="popularItems.length">
      <div class="section-head">
        <h2 class="section-title">
          <el-icon class="section-icon"><TrendCharts /></el-icon>
          热门游戏
        </h2>
        <span class="section-note">按浏览热度</span>
        <NuxtLink to="/games" class="section-more">查看全部游戏 →</NuxtLink>
      </div>
      <div class="popular-scroll">
        <NuxtLink
          v-for="(g, i) in popularItems"
          :key="g.id"
          :to="`/galgame/${g.id}`"
          class="popular-item"
        >
          <el-image :src="g.cover" fit="cover" class="popular-cover" lazy />
          <div class="popular-name" :title="g.name">{{ g.name }}</div>
          <div class="popular-views">
            <el-icon><View /></el-icon>
            {{ g.views }}
          </div>
          <span class="popular-rank" :class="{ top: i < 3 }">{{ i + 1 }}</span>
        </NuxtLink>
      </div>
    </template>

    <!-- ===== 最新发布：与热门游戏一致的横向卡片样式 ===== -->
    <template v-if="latestItems.length">
      <div class="section-head">
        <h2 class="section-title">
          <el-icon class="section-icon"><Clock /></el-icon>
          最新发布
        </h2>
        <span class="section-note">最近更新</span>
        <NuxtLink to="/games" class="section-more">更多 →</NuxtLink>
      </div>
      <div class="popular-scroll latest-scroll">
        <NuxtLink
          v-for="item in latestItems"
          :key="item.id"
          :to="`/galgame/${item.id}`"
          class="popular-item"
        >
          <el-image :src="item.cover" fit="cover" class="popular-cover" lazy />
          <div class="popular-name" :title="item.name">{{ item.name }}</div>
          <div class="popular-views">
            <el-icon><View /></el-icon>
            {{ item.views }}
          </div>
        </NuxtLink>
      </div>
    </template>

  </div>
</template>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  gap: var(--fish-space-xl);
}

/* ========================================================
   精选 Hero：响应式高度 + 径向渐变遮罩（不遮挡封面主体）
   ======================================================== */
.hero-card {
  position: relative;
  display: block;
  height: clamp(220px, 30vw, 400px);
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid var(--fish-border);
  text-decoration: none;
  isolation: isolate;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1),
              box-shadow 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.hero-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.35), 0 4px 12px rgba(0, 0, 0, 0.2);
}

/* 深色模式下：极细微光边框 */
html.dark .hero-card {
  box-shadow: 0 0 0 1px rgba(143, 142, 245, 0.08);
}

html.dark .hero-card:hover {
  box-shadow: 0 0 0 1px rgba(143, 142, 245, 0.15),
              0 12px 40px rgba(0, 0, 0, 0.35),
              0 4px 12px rgba(0, 0, 0, 0.2);
}

.hero-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: -2;
}

/* 底部深色渐变遮罩：从下到上渐变，图片上方保持清晰 */
.hero-overlay {
  position: absolute;
  inset: 0;
  z-index: -1;
  background: linear-gradient(
    to top,
    rgba(0, 0, 0, 0.85) 0%,
    rgba(0, 0, 0, 0.45) 35%,
    transparent 65%
  );
}

.hero-info {
  position: absolute;
  left: 0;
  bottom: 0;
  max-width: 60%;
  padding: var(--fish-space-2xl) var(--fish-space-xl) var(--fish-space-lg);
}

.hero-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 999px;
  background: rgba(143, 142, 245, 0.15);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid rgba(143, 142, 245, 0.25);
  color: var(--fish-accent);
  font-size: var(--fish-text-xs);
  font-weight: 600;
  letter-spacing: 0.04em;
  margin-bottom: var(--fish-space-md);
}

.hero-title {
  margin: 0 0 var(--fish-space-sm);
  font-size: var(--fish-text-4xl);
  font-weight: 800;
  line-height: var(--fish-leading-tight);
  color: var(--fish-text-1);
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.hero-meta {
  display: flex;
  align-items: center;
  gap: var(--fish-space-md);
  color: rgba(255, 255, 255, 0.72);
  font-size: var(--fish-text-sm);
}

.hero-author {
  display: inline-flex;
  align-items: center;
  gap: var(--fish-space-sm);
}

.hero-stat {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

/* ========================================================
   区块标题：首页使用 icon+文字（与详情页竖条装饰差异化）
   ======================================================== */
.section-head {
  display: flex;
  align-items: center;
  gap: var(--fish-space-sm);
}

.section-title {
  display: inline-flex;
  align-items: center;
  gap: var(--fish-space-sm);
  margin: 0;
  font-size: var(--fish-text-xl);
  font-weight: 800;
  letter-spacing: var(--fish-tracking-tight);
  color: var(--fish-text-1);
}

/* 首页 icon 装饰：accent 色，替代竖条 */
.section-icon {
  color: var(--fish-accent);
  font-size: 20px;
  flex-shrink: 0;
}

.section-note {
  font-size: var(--fish-text-sm);
  color: var(--fish-text-3);
  margin-left: var(--fish-space-xs);
}

.section-more {
  margin-left: auto;
  font-size: var(--fish-text-sm);
  font-weight: 600;
  color: var(--fish-accent);
  text-decoration: none;
  transition: opacity 0.2s;
}

.section-more:hover {
  opacity: 0.8;
}

/* ========================================================
   热门条：横向滚动 + snap，减少网格拥挤感
   ======================================================== */
.popular-scroll {
  display: flex;
  gap: var(--fish-space-md);
  overflow-x: auto;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
  padding-bottom: var(--fish-space-xs);
}

/* 隐藏滚动条但保留功能 */
.popular-scroll::-webkit-scrollbar {
  height: 4px;
}
.popular-scroll::-webkit-scrollbar-thumb {
  background: var(--fish-border-strong);
  border-radius: 2px;
}

.popular-item {
  position: relative;
  display: block;
  flex-shrink: 0;
  width: 160px;
  padding: var(--fish-space-sm);
  border-radius: var(--fish-radius-sm);
  background: transparent;
  border: 1px solid var(--fish-border);
  text-decoration: none;
  scroll-snap-align: start;
  transition: border-color 0.2s, transform 0.2s, box-shadow 0.2s;
}

.popular-item:hover {
  border-color: var(--fish-accent-border);
  transform: translateY(-2px);
  box-shadow: var(--fish-shadow-hover);
}

.popular-cover {
  width: 100%;
  aspect-ratio: 2 / 3;
  border-radius: var(--fish-radius-xs);
  display: block;
  background: var(--fish-bg);
}

.popular-name {
  margin-top: var(--fish-space-sm);
  font-size: var(--fish-text-sm);
  font-weight: 600;
  color: var(--fish-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.popular-views {
  display: flex;
  align-items: center;
  gap: var(--fish-space-xs);
  margin-top: var(--fish-space-xs);
  font-size: var(--fish-text-xs);
  color: var(--fish-text-3);
}

.popular-rank {
  position: absolute;
  top: 12px;
  left: 12px;
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  border-radius: var(--fish-radius-xs);
  background: rgba(11, 11, 15, 0.7);
  color: rgba(255, 255, 255, 0.85);
  font-size: var(--fish-text-xs);
  font-weight: 700;
}

.popular-rank.top {
  background: var(--fish-accent);
  color: #fff;
}

/* ========================================================
   最新发布：与热门游戏一致的横向卡片（复用 popular-scroll 样式）
   ======================================================== */
.latest-scroll {
  /* 复用 popular-scroll 的样式（flex row + scroll-snap），仅作语义区分 */
}

/* ========================================================
   响应式
   ======================================================== */
@media (max-width: 1024px) {
  .hero-info {
    max-width: 70%;
    padding: var(--fish-space-lg) var(--fish-space-lg) var(--fish-space-md);
  }

  .hero-title {
    font-size: var(--fish-text-3xl);
  }
}

@media (max-width: 560px) {
  .home-page {
    gap: var(--fish-space-lg);
  }

  .hero-info {
    max-width: 85%;
    padding: var(--fish-space-lg) var(--fish-space-md) var(--fish-space-md);
  }

  .hero-title {
    font-size: var(--fish-text-2xl);
  }

  .hero-meta {
    gap: var(--fish-space-sm);
  }

  .popular-item {
    width: 130px;
  }
}
</style>
