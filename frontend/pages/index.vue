<script setup lang="ts">
import type { GalItem, GalgameListQuery } from '~/types'
import { useGalgameList } from '~/composables/useGalgame'

// 门户发现数据：一次拉取较大页，用于精选 Hero / 热门条
const discoveryQuery = ref<GalgameListQuery>({ page: 1, size: 50 })
const { data: discovery } = useGalgameList(discoveryQuery, { key: 'home-discovery' })

const discoveryItems = computed(() => discovery.value?.items ?? [])

// 精选：浏览量最高的游戏（后端无 featured 语义，暂用 views 近似）
const featured = computed<GalItem | null>(() => {
  const sorted = [...discoveryItems.value].sort((a, b) => b.views - a.views)
  return sorted[0] ?? null
})

// 热门：按浏览量取前 6
const popular = computed<GalItem[]>(() => {
  return [...discoveryItems.value].sort((a, b) => b.views - a.views).slice(0, 6)
})

// 最新发布：按 discovery 原始顺序（后端默认 updated_at 倒序）取前 8
const latest = computed<GalItem[]>(() => discoveryItems.value.slice(0, 8))

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
    <template v-if="popular.length">
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
          v-for="(g, i) in popular"
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

    <!-- ===== 最新发布：按后端默认时间倒序 ===== -->
    <template v-if="latest.length">
      <div class="section-head">
        <h2 class="section-title">
          <el-icon class="section-icon"><Clock /></el-icon>
          最新发布
        </h2>
        <span class="section-note">最近更新</span>
        <NuxtLink to="/games" class="section-more">更多 →</NuxtLink>
      </div>
      <div class="latest-grid">
        <GameCard v-for="item in latest" :key="item.id" :item="item" />
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
  border-radius: var(--fish-radius);
  overflow: hidden;
  border: 1px solid var(--fish-border);
  text-decoration: none;
  isolation: isolate;
}

.hero-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: -2;
}

/* 径向渐变从左下到右上：文字在左下可读，封面右侧/上方保持清晰 */
.hero-overlay {
  position: absolute;
  inset: 0;
  z-index: -1;
  background: radial-gradient(
    ellipse 80% 70% at 20% 85%,
    rgba(11, 11, 15, 0.94) 0%,
    rgba(11, 11, 15, 0.6) 40%,
    rgba(11, 11, 15, 0.1) 100%
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
  padding: 3px 10px;
  border-radius: 999px;
  background: var(--fish-accent-soft);
  border: 1px solid var(--fish-accent-border);
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
  background: var(--fish-bg-2);
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
   最新发布网格：复用 GameCard，4 列桌面 → 2 列移动
   ======================================================== */
.latest-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--fish-space-lg);
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

  .latest-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: var(--fish-space-md);
  }
}
</style>
