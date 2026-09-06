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

    <!-- ===== 热门游戏：按浏览量客户端排序（后端无 sort 参数） ===== -->
    <template v-if="popular.length">
      <div class="section-head">
        <h2 class="section-title">热门游戏</h2>
        <span class="section-note">按浏览热度</span>
        <!-- 全部游戏已移至导航页 /games，这里作为首页出口 -->
        <NuxtLink to="/games" class="section-more">查看全部游戏 →</NuxtLink>
      </div>
      <div class="popular-row">
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

  </div>
</template>

<style scoped>
.home-page {
  display: flex;
  flex-direction: column;
  gap: 26px;
}

/* ========================================================
   精选 Hero
   ======================================================== */
.hero-card {
  position: relative;
  display: block;
  height: 300px;
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

.hero-overlay {
  position: absolute;
  inset: 0;
  z-index: -1;
  background: linear-gradient(
    90deg,
    rgba(11, 11, 15, 0.92) 0%,
    rgba(11, 11, 15, 0.55) 50%,
    rgba(11, 11, 15, 0.15) 100%
  );
}

.hero-info {
  position: absolute;
  left: 0;
  bottom: 0;
  max-width: 640px;
  padding: 40px 32px 28px;
}

.hero-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  background: var(--fish-accent-soft);
  border: 1px solid var(--fish-accent-border);
  color: var(--fish-accent);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.04em;
  margin-bottom: 14px;
}

.hero-title {
  margin: 0 0 12px;
  font-size: 30px;
  font-weight: 800;
  line-height: 1.25;
  color: #f5f5f5;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.hero-meta {
  display: flex;
  align-items: center;
  gap: 18px;
  color: rgba(255, 255, 255, 0.72);
  font-size: 14px;
}

.hero-author {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.hero-stat {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

/* ========================================================
   区块标题
   ======================================================== */
.section-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.section-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.01em;
  color: var(--fish-text-1);
}

.section-title::before {
  content: '';
  width: 4px;
  height: 18px;
  border-radius: 3px;
  background: var(--fish-accent);
  flex-shrink: 0;
}

.section-note {
  font-size: 13px;
  color: var(--fish-text-3);
}

.section-more {
  margin-left: auto;
  font-size: 13px;
  font-weight: 600;
  color: var(--fish-accent);
  text-decoration: none;
  transition: opacity 0.2s;
}

.section-more:hover {
  opacity: 0.8;
}

/* ========================================================
   热门条
   ======================================================== */
.popular-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 14px;
}

.popular-item {
  position: relative;
  display: block;
  padding: 8px;
  border-radius: 10px;
  background: var(--fish-bg-2);
  border: 1px solid var(--fish-border);
  text-decoration: none;
  transition: border-color 0.2s, transform 0.2s;
}

.popular-item:hover {
  border-color: var(--fish-accent-border);
  transform: translateY(-2px);
}

.popular-cover {
  width: 100%;
  aspect-ratio: 2 / 3;
  border-radius: 6px;
  display: block;
  background: var(--fish-bg);
}

.popular-name {
  margin-top: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--fish-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.popular-views {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  font-size: 12px;
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
  border-radius: 6px;
  background: rgba(11, 11, 15, 0.7);
  color: rgba(255, 255, 255, 0.85);
  font-size: 12px;
  font-weight: 700;
}

.popular-rank.top {
  background: var(--fish-accent);
  color: #fff;
}

/* ========================================================
   响应式
   ======================================================== */
@media (max-width: 1024px) {
  .hero-card {
    height: 260px;
  }
}

@media (max-width: 560px) {
  .hero-card {
    height: 220px;
  }

  .hero-info {
    padding: 24px 20px 20px;
  }

  .hero-title {
    font-size: 22px;
  }

  .hero-meta {
    gap: 12px;
  }
}
</style>
