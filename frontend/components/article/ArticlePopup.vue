<script setup lang="ts">
import { useArticleList } from '~/composables/useArticle'
import type { ArticleItem } from '~/types'

const emit = defineEmits<{
  close: []
}>()

const page = ref(1)
const size = ref(8) // 4 cols × 2 rows default

const { data, pending, error, refresh } = useArticleList(page, size)

const items = computed(() => data.value?.items ?? [])
const total = computed(() => data.value?.total ?? 0)

function formatTime(value?: string): string {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  const now = Date.now()
  const diff = now - d.getTime()
  const day = 86400000
  if (diff < day) return '今天'
  if (diff < 2 * day) return '昨天'
  if (diff < 7 * day) return `${Math.floor(diff / day)} 天前`
  return d.toLocaleDateString('zh-CN')
}
</script>

<template>
  <div class="article-popup">
    <!-- 标题行 -->
    <div class="popup-head">
      <h3 class="popup-title">文章</h3>
      <NuxtLink to="/articles" class="popup-more" @click="emit('close')">
        查看更多
        <el-icon><ArrowRight /></el-icon>
      </NuxtLink>
    </div>

    <!-- 加载中 -->
    <div v-if="pending && !items.length" class="popup-loading">
      <el-skeleton :rows="2" animated />
    </div>

    <!-- 错误 -->
    <div v-else-if="error" class="popup-error">
      <p>加载失败</p>
      <el-button size="small" @click="refresh">重试</el-button>
    </div>

    <!-- 空状态 -->
    <ClientOnly v-else-if="!items.length">
      <div class="popup-empty">
        <p>暂无文章</p>
      </div>
    </ClientOnly>

    <!-- 4列文章网格 -->
    <div v-else class="article-grid">
      <NuxtLink
        v-for="item in items"
        :key="item.id"
        :to="`/article/${item.id}`"
        class="article-card"
        @click="emit('close')"
      >
        <div class="card-cover-wrap">
          <el-image :src="item.cover" fit="cover" class="card-cover" lazy />
          <span class="card-view-badge">
            <el-icon><View /></el-icon>
            {{ item.views ?? 0 }}
          </span>
        </div>
        <div class="card-body">
          <h4 class="card-title">{{ item.title }}</h4>
          <div class="card-meta-row">
            <span class="card-meta-time">{{ formatTime(item.time) }}</span>
            <span class="card-meta-comment">
              <el-icon><ChatDotSquare /></el-icon>
              {{ item.comcnt ?? 0 }}
            </span>
          </div>
        </div>
      </NuxtLink>
    </div>
  </div>
</template>

<style scoped>
.article-popup {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* ===== 标题行 ===== */
.popup-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.popup-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: var(--fish-text-1);
}

.popup-more {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  font-weight: 600;
  color: var(--fish-accent);
  text-decoration: none;
  transition: color 0.2s;
}

.popup-more:hover {
  color: var(--fish-accent-strong);
}

.popup-more .el-icon {
  font-size: 14px;
}

/* ===== 状态区 ===== */
.popup-loading {
  padding: 16px 0;
}

.popup-error,
.popup-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px 0;
}

.popup-error p,
.popup-empty p {
  margin: 0;
  font-size: 14px;
  color: var(--fish-text-3);
}

/* ===== 文章网格：4列 ===== */
.article-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

/* ===== 文章卡片（与列表页一致） ===== */
.article-card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--fish-border);
  border-radius: 16px;
  background: var(--fish-card);
  overflow: hidden;
  text-decoration: none;
  transition:
    border-color 0.25s cubic-bezier(0.16, 1, 0.3, 1),
    transform 0.25s cubic-bezier(0.16, 1, 0.3, 1),
    box-shadow 0.25s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: var(--fish-shadow);
}

.article-card:hover {
  border-color: var(--fish-accent-border);
  transform: translateY(-3px) scale(1.015);
  box-shadow: var(--fish-shadow-hover);
}

/* 封面区域 —— 16:10 */
.card-cover-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 10;
  overflow: hidden;
  background: var(--fish-bg);
}

.card-cover {
  width: 100%;
  height: 100%;
  display: block;
  transition: transform 0.35s cubic-bezier(0.16, 1, 0.3, 1);
}

.article-card:hover .card-cover {
  transform: scale(1.06);
}

/* 右下角浏览徽标 */
.card-view-badge {
  position: absolute;
  right: 8px;
  bottom: 8px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  font-size: 11px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
  line-height: 1.3;
  pointer-events: none;
}

.card-view-badge .el-icon {
  font-size: 11px;
}

/* 标题区 */
.card-body {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.card-title {
  margin: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--fish-text-1);
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  transition: color 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.article-card:hover .card-title {
  color: var(--fish-accent);
}

.card-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  gap: var(--fish-space-sm);
}

.card-meta-time {
  font-size: 11px;
  color: var(--fish-text-3);
}

.card-meta-comment {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 11px;
  color: var(--fish-text-3);
}

.card-meta-comment .el-icon {
  font-size: 12px;
}

/* ===== 响应式 ===== */
@media (max-width: 1024px) {
  .article-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 560px) {
  .article-grid {
    grid-template-columns: 1fr;
  }
}
</style>