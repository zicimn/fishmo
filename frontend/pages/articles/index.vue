<script setup lang="ts">
import { useArticleList } from '~/composables/useArticle'
import type { ArticleItem } from '~/types'

const route = useRoute()
const router = useRouter()

// ---- 状态 ----
const page = ref(Number(route.query.page) || 1)
const size = ref(20)
const activeCategory = ref<string | undefined>(undefined)

// ---- 数据加载 ----
const { data, pending, error, refresh } = useArticleList(page, size, activeCategory)

const total = computed(() => data.value?.total ?? 0)
const items = computed(() => data.value?.items ?? [])

// ---- 分类标签选项 ----
const categoryOptions = ['全部', '攻略', '资讯', '公告', '教程', '其他']

function selectCategory(cat: string) {
  if (cat === '全部') {
    activeCategory.value = undefined
  } else {
    activeCategory.value = cat
  }
  page.value = 1
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function handlePageChange(p: number) {
  page.value = p
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// ---- 格式化 ----
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
  return d.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

// ---- 水合安全 ----
const isMounted = ref(false)
onMounted(() => {
  isMounted.value = true
})
</script>

<template>
  <div class="articles-layout">
    <!-- ===== 主内容区 ===== -->
    <main class="main-content">
      <!-- 页面头部：标题 + 总数 -->
      <header class="page-head">
        <h1 class="page-title">文章</h1>
        <span class="page-count">共 {{ total }} 篇</span>
      </header>

      <!-- 分类标签筛选 -->
      <div class="category-pills">
        <button
          v-for="cat in categoryOptions"
          :key="cat"
          class="pill"
          :class="{ 'pill-active': cat === '全部' ? !activeCategory : activeCategory === cat }"
          @click="selectCategory(cat)"
        >
          {{ cat }}
        </button>
      </div>

      <!-- 加载骨架 -->
      <div v-if="pending && !items.length" class="loading-grid">
        <div v-for="n in 8" :key="n" class="skeleton-card">
          <el-skeleton animated class="skeleton-cover" />
          <el-skeleton :rows="2" animated class="skeleton-body" />
        </div>
      </div>

      <!-- 错误 -->
      <div v-else-if="error" class="empty-state">
        <img src="/status/1.png" alt="加载失败" class="empty-img" />
        <p class="empty-text">加载失败，请稍后重试</p>
        <el-button size="small" @click="refresh">重试</el-button>
      </div>

      <!-- 空 -->
      <div v-else-if="!items.length" class="empty-state">
        <img src="/status/2.png" alt="暂无文章" class="empty-img" />
        <p class="empty-text">暂无文章</p>
      </div>

      <!-- 文章网格 -->
      <div v-else class="article-grid">
        <NuxtLink
          v-for="item in items"
          :key="item.id"
          :to="`/article/${item.id}`"
          class="article-card"
        >
          <!-- 封面 -->
          <div class="card-cover-wrap">
            <el-image :src="item.cover" fit="cover" class="card-cover" lazy />
            <span class="card-view-badge">
              <el-icon><View /></el-icon>
              {{ item.views ?? 0 }}
            </span>
          </div>

          <!-- 内容 -->
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

      <!-- 分页 -->
      <div v-if="total > size" class="pagination-wrap">
        <el-pagination
          layout="prev, pager, next, total"
          :total="total"
          :page-size="size"
          :current-page="page"
          background
          @current-change="handlePageChange"
        />
      </div>
    </main>
  </div>
</template>

<style scoped>
/* ============================================================
   布局
   ============================================================ */
.articles-layout {
  max-width: 1280px;
  margin: 0 auto;
}

/* ============================================================
   主内容区
   ============================================================ */
.main-content {
  display: flex;
  flex-direction: column;
  gap: var(--fish-space-lg);
}

/* ===== 页面标题 ===== */
.page-head {
  display: flex;
  align-items: baseline;
  gap: var(--fish-space-sm);
}

.page-title {
  display: inline-flex;
  align-items: center;
  gap: var(--fish-space-sm);
  margin: 0;
  font-size: var(--fish-text-4xl);
  font-weight: 800;
  letter-spacing: var(--fish-tracking-tight);
  color: var(--fish-accent);
  line-height: 1.2;
}

.page-count {
  font-size: var(--fish-text-sm);
  color: var(--fish-text-3);
  font-weight: 500;
}

/* ===== 分类药丸筛选 ===== */
.category-pills {
  display: flex;
  flex-wrap: wrap;
  gap: var(--fish-space-sm);
}

.pill {
  display: inline-flex;
  align-items: center;
  padding: 6px 16px;
  border-radius: 999px;
  border: 1px solid var(--fish-border);
  background: transparent;
  color: var(--fish-text-2);
  font-size: var(--fish-text-sm);
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  user-select: none;
}

.pill:hover {
  border-color: var(--fish-accent-border);
  color: var(--fish-accent);
  background: var(--fish-accent-soft);
}

.pill-active {
  background: var(--fish-accent) !important;
  border-color: var(--fish-accent) !important;
  color: #ffffff !important;
  font-weight: 600;
}

/* ===== 4 列文章网格 ===== */
.article-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

/* ===== 文章卡片 ===== */
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

/* 封面区域 —— 16:10 比例 */
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

/* 卡片内容区 */
.card-body {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.card-title {
  margin: 0;
  font-size: var(--fish-text-base);
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

/* 底部元信息行 */
.card-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: auto;
  gap: var(--fish-space-sm);
}

.card-meta-time {
  font-size: var(--fish-text-xs);
  color: var(--fish-text-3);
}

.card-meta-comment {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: var(--fish-text-xs);
  color: var(--fish-text-3);
}

.card-meta-comment .el-icon {
  font-size: 12px;
}

/* ===== 分页 ===== */
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: var(--fish-space-sm);
}

:deep(.el-pagination) {
  --el-pagination-bg-color: transparent;
  --el-pagination-button-bg-color: var(--fish-bg-2);
  --el-pagination-button-color: var(--fish-text-2);
  --el-pagination-hover-color: var(--fish-accent);
}

:deep(.el-pagination.is-background .el-pager li) {
  background: var(--fish-bg-2);
  border: 1px solid var(--fish-border);
  color: var(--fish-text-2);
  border-radius: var(--fish-radius-xs);
}

:deep(.el-pagination.is-background .el-pager li.is-active) {
  background: var(--fish-accent) !important;
  border-color: var(--fish-accent) !important;
  color: #fff !important;
}

:deep(.el-pagination.is-background .el-pager li:hover) {
  color: var(--fish-accent);
  border-color: var(--fish-accent-border);
}

:deep(.el-pagination button.btn-prev),
:deep(.el-pagination button.btn-next) {
  background: var(--fish-bg-2) !important;
  border: 1px solid var(--fish-border);
  color: var(--fish-text-2);
  border-radius: var(--fish-radius-xs);
}

:deep(.el-pagination button:disabled) {
  color: var(--fish-text-3) !important;
  opacity: 0.4;
}

/* ===== 骨架 ===== */
.loading-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.skeleton-card {
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  overflow: hidden;
  background: var(--fish-card);
  border: 1px solid var(--fish-border);
}

.skeleton-cover {
  aspect-ratio: 16 / 10;
  width: 100%;
  display: block;
}

.skeleton-body {
  padding: 12px;
}

/* ===== 空 / 错误状态 ===== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--fish-space-md);
  padding: var(--fish-space-2xl) var(--fish-space-lg);
}

.empty-img {
  width: 300px;
  max-width: 80%;
  border-radius: 12px;
  opacity: 0.85;
}

.empty-text {
  margin: 0;
  font-size: var(--fish-text-lg);
  color: var(--fish-text-3);
}

/* ============================================================
   响应式
   ============================================================ */

/* 平板：3 列 */
@media (max-width: 1024px) {
  .article-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .loading-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* 小屏：2 列 */
@media (max-width: 768px) {
  .article-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--fish-space-md);
  }

  .loading-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

/* 移动端：单列 */
@media (max-width: 480px) {
  .article-grid {
    grid-template-columns: 1fr;
  }

  .loading-grid {
    grid-template-columns: 1fr;
  }

  .page-title {
    font-size: var(--fish-text-2xl);
  }

  .category-pills {
    overflow-x: auto;
    flex-wrap: nowrap;
    -webkit-overflow-scrolling: touch;
    padding-bottom: 4px;
  }

  .pill {
    flex-shrink: 0;
    padding: 5px 14px;
  }
}
</style>