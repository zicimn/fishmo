<script setup lang="ts">
import {
  CATEGORY_OPTIONS,
  PLATFORM_OPTIONS,
  type CategoryValue,
  type PlatformValue,
  type GalgameListQuery,
} from '~/types'
import { api, cleanParams } from '~/utils/request'
import type { GalList } from '~/types'

/**
 * 全部游戏页（/games）：作品/平台均为前后端统一枚举，横排筛选 + 网格 + 分页。
 * URL 参数 ?search_type=tag&keyword= 支持从详情页标签跳转进行标签搜索。
 * URL 参数 ?category= / ?platform= / ?page= 同步，支持分享/刷新保持/前进后退。
 */
const route = useRoute()
const router = useRouter()

// 从 URL 恢复筛选时只接受合法枚举值，非法/缺失值回退为空（避免把非法值当筛选条件提交）
function validCategory(raw: string): CategoryValue | '' {
  return CATEGORY_OPTIONS.some((c) => c.value === raw) ? (raw as CategoryValue) : ''
}
function validPlatform(raw: string): PlatformValue | '' {
  return PLATFORM_OPTIONS.some((p) => p.value === raw) ? (raw as PlatformValue) : ''
}

// 从 URL 恢复搜索类型和关键词（从详情页标签跳转时携带）
const urlSearchType = typeof route.query.search_type === 'string' ? route.query.search_type.trim() : ''
const urlKeyword = typeof route.query.keyword === 'string' ? route.query.keyword.trim() : ''

const filters = reactive({
  searchType: urlSearchType,
  keyword: urlKeyword,
  category: validCategory(typeof route.query.category === 'string' ? route.query.category : ''),
  platform: validPlatform(typeof route.query.platform === 'string' ? route.query.platform : ''),
  page: Number(route.query.page) || 1,
  size: 20,
})

const listQuery = ref<GalgameListQuery>({ ...filters })

// 当 searchType=tag 时使用搜索 API，否则使用 galgame 列表 API
const { data, pending, error, refresh } = useAsyncData(
  'games-page-list',
  async () => {
    const q = { ...listQuery.value }
    if (q.searchType === 'tag' && q.keyword) {
      // 标签搜索：使用搜索 API，保留 keyword, page, size；清除 category/platform/searchType
      const { searchType, category, platform, ...rest } = q
      return api<GalList>('/api/v1/search/', {
        query: cleanParams({ ...rest, search_type: 'tag' }),
      })
    }
    // 常规浏览：使用 galgame 列表 API，清除 searchType
    const { searchType, ...rest } = q
    return api<GalList>('/api/v1/galgame/', { query: cleanParams(rest) })
  },
  { watch: [listQuery] },
)

const total = computed(() => data.value?.total ?? 0)
const items = computed(() => data.value?.items ?? [])

function syncUrl() {
  const q: Record<string, string> = {}
  if (filters.searchType) q.search_type = filters.searchType
  if (filters.keyword) q.keyword = filters.keyword
  if (filters.category) q.category = filters.category
  if (filters.platform) q.platform = filters.platform
  if (filters.page > 1) q.page = String(filters.page)
  router.replace({ query: q })
}

/** 标签搜索时清除标签回到全部列表 */
function clearTagSearch() {
  filters.searchType = ''
  filters.keyword = ''
  filters.page = 1
  listQuery.value = { ...filters }
  syncUrl()
}

function handleFilterChange() {
  filters.page = 1
  listQuery.value = { ...filters }
  syncUrl()
}

// 作品/平台筛选点击
function handleCategorySelect(value: CategoryValue | '') {
  if (filters.category === value) return
  filters.category = value
  handleFilterChange()
}

function handlePlatformSelect(value: PlatformValue | '') {
  if (filters.platform === value) return
  filters.platform = value
  handleFilterChange()
}

function handlePageChange(page: number) {
  filters.page = page
  listQuery.value = { ...filters }
  syncUrl()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

/**
 * 监听 URL query 变化（浏览器前进后退）：
 * 同步到 filters，触发列表刷新。
 */
watch(
  () => route.query,
  (newQuery: Record<string, unknown>) => {
    const st = typeof newQuery.search_type === 'string' ? newQuery.search_type.trim() : ''
    const kw = typeof newQuery.keyword === 'string' ? newQuery.keyword.trim() : ''
    const cat = validCategory(typeof newQuery.category === 'string' ? newQuery.category : '')
    const plat = validPlatform(typeof newQuery.platform === 'string' ? newQuery.platform : '')
    const pg = Number(newQuery.page) || 1

    if (
      filters.searchType !== st ||
      filters.keyword !== kw ||
      filters.category !== cat ||
      filters.platform !== plat ||
      filters.page !== pg
    ) {
      filters.searchType = st
      filters.keyword = kw
      filters.category = cat
      filters.platform = plat
      filters.page = pg
      listQuery.value = { ...filters }
    }
  },
)
</script>

<template>
  <div class="games-page">
    <!-- ===== 页面标题：标签搜索时显示搜索提示 ===== -->
    <div class="page-head">
      <h1 class="page-title">
        {{ filters.searchType === 'tag' && filters.keyword ? `标签：${filters.keyword}` : '全部游戏' }}
      </h1>
      <span class="page-count">共 {{ total }} 款</span>
    </div>

    <!-- ===== 标签搜索提示：当从详情页标签跳转时显示 ===== -->
    <div v-if="filters.searchType === 'tag' && filters.keyword" class="tag-search-banner">
      <span class="tag-search-label">标签搜索：</span>
      <span class="tag-search-chip">{{ filters.keyword }}</span>
      <el-button size="small" text @click="clearTagSearch">
        <el-icon><Close /></el-icon>
        清除筛选
      </el-button>
    </div>

    <!-- ===== 枚举筛选：作品 / 平台横排可点选，标签搜索时隐藏 ===== -->
    <div v-if="!filters.searchType" class="filter-rows">
      <div class="filter-row">
        <span class="filter-label">作品</span>
        <button
          class="filter-chip"
          :class="{ active: !filters.category }"
          @click="handleCategorySelect('')"
        >
          全部
        </button>
        <button
          v-for="c in CATEGORY_OPTIONS"
          :key="c.value"
          class="filter-chip"
          :class="{ active: filters.category === c.value }"
          @click="handleCategorySelect(c.value)"
        >
          {{ c.label }}
        </button>
      </div>
      <div class="filter-row">
        <span class="filter-label">平台</span>
        <button
          class="filter-chip"
          :class="{ active: !filters.platform }"
          @click="handlePlatformSelect('')"
        >
          全部
        </button>
        <button
          v-for="p in PLATFORM_OPTIONS"
          :key="p.value"
          class="filter-chip"
          :class="{ active: filters.platform === p.value }"
          @click="handlePlatformSelect(p.value)"
        >
          {{ p.label }}
        </button>
      </div>
    </div>

    <el-alert
      v-if="error"
      title="游戏列表加载失败（后端接口可能尚未跑通）"
      type="error"
      :closable="false"
      show-icon
      class="mb"
    >
      <template #default>
        <p>{{ error instanceof Error ? error.message : String(error) }}</p>
        <el-button size="small" @click="refresh">重试</el-button>
      </template>
    </el-alert>

    <el-skeleton v-if="pending && !items.length" :rows="6" animated class="mb" />

    <ClientOnly v-else-if="!items.length">
      <div class="empty-state">
        <el-icon class="empty-icon" :size="48"><Search /></el-icon>
        <p class="empty-text">
          <template v-if="filters.searchType === 'tag'">
            未找到标签为「<span class="empty-keyword">{{ filters.keyword }}</span>」的游戏
          </template>
          <template v-else-if="filters.keyword">
            未找到与「<span class="empty-keyword">{{ filters.keyword }}</span>」相关的游戏
          </template>
          <template v-else>
            暂无符合条件的游戏
          </template>
        </p>
        <NuxtLink to="/publish" class="empty-action">
          发布第一款 →
        </NuxtLink>
      </div>
    </ClientOnly>

    <div v-else class="game-grid">
      <GameCard v-for="item in items" :key="item.id" :item="item" />
    </div>

    <div v-if="total > 0" class="pagination-wrap">
      <el-pagination
        layout="prev, pager, next, total"
        :total="total"
        :page-size="filters.size"
        :current-page="filters.page"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<style scoped>
.games-page {
  display: flex;
  flex-direction: column;
  gap: var(--fish-space-lg);
}

.mb {
  margin-bottom: 0;
}

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
  font-size: var(--fish-text-3xl);
  font-weight: 800;
  letter-spacing: var(--fish-tracking-tight);
  color: var(--fish-text-1);
}
.page-title::before {
  content: '';
  width: 4px;
  height: 22px;
  border-radius: 3px;
  background: var(--fish-accent);
}
.page-count {
  font-size: var(--fish-text-sm);
  color: var(--fish-text-3);
}

/* ===== 标签搜索提示条 ===== */
.tag-search-banner {
  display: flex;
  align-items: center;
  gap: var(--fish-space-sm);
  padding: var(--fish-space-sm) var(--fish-space-md);
  border-radius: var(--fish-radius-sm);
  background: var(--fish-accent-soft);
  border: 1px solid var(--fish-accent-border);
  font-size: var(--fish-text-sm);
}

.tag-search-label {
  color: var(--fish-text-3);
  font-weight: 600;
}

.tag-search-chip {
  padding: 2px 10px;
  border-radius: 999px;
  background: var(--fish-accent);
  color: #fff;
  font-weight: 600;
  font-size: var(--fish-text-xs);
}

.filter-rows {
  display: flex;
  flex-direction: column;
  gap: var(--fish-space-sm);
}
.filter-row {
  display: flex;
  align-items: center;
  gap: var(--fish-space-sm);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
  scrollbar-width: none;
  padding-bottom: 2px;
}
.filter-row::-webkit-scrollbar {
  height: 0;
}
.filter-label {
  flex-shrink: 0;
  font-size: var(--fish-text-sm);
  font-weight: 700;
  color: var(--fish-text-3);
  margin-right: var(--fish-space-xs);
}
.filter-chip {
  flex-shrink: 0;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid var(--fish-border);
  background: var(--fish-bg-2);
  color: var(--fish-text-2);
  font-size: var(--fish-text-sm);
  font-family: inherit;
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s, background 0.2s;
}
.filter-chip:hover {
  color: var(--fish-accent);
  border-color: var(--fish-accent-border);
}
.filter-chip.active {
  background: var(--fish-accent-soft);
  border-color: var(--fish-accent);
  color: var(--fish-accent);
  font-weight: 600;
}

.game-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--fish-space-lg);
}

/* 分页器：颜色融入设计系统 */
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: var(--fish-space-sm);
}

/* 分页器定制：融入深色设计系统 */
:deep(.el-pagination) {
  --el-pagination-bg-color: transparent;
  --el-pagination-text-color: var(--fish-text-2);
  --el-pagination-button-bg-color: var(--fish-bg-2);
  --el-pagination-button-color: var(--fish-text-2);
  --el-pagination-hover-color: var(--fish-accent);
}

:deep(.el-pagination .el-pager li) {
  background: var(--fish-bg-2);
  border: 1px solid var(--fish-border);
  color: var(--fish-text-2);
  border-radius: var(--fish-radius-xs);
}

:deep(.el-pagination .el-pager li.is-active) {
  background: var(--fish-accent);
  border-color: var(--fish-accent);
  color: #fff;
}

:deep(.el-pagination .el-pager li:hover) {
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

/* 定制空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--fish-space-md);
  padding: var(--fish-space-2xl) var(--fish-space-lg);
}

.empty-icon {
  color: var(--fish-text-3);
  opacity: 0.5;
}

.empty-text {
  margin: 0;
  font-size: var(--fish-text-lg);
  color: var(--fish-text-3);
}

.empty-keyword {
  color: var(--fish-accent);
  font-weight: 600;
}

.empty-action {
  font-size: var(--fish-text-sm);
  font-weight: 600;
  color: var(--fish-accent);
  text-decoration: none;
  padding: var(--fish-space-sm) var(--fish-space-md);
  border-radius: var(--fish-radius-sm);
  border: 1px solid var(--fish-accent-border);
  background: var(--fish-accent-soft);
  transition: opacity 0.2s;
}

.empty-action:hover {
  opacity: 0.85;
}

@media (max-width: 560px) {
  .game-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: var(--fish-space-md);
  }
}
</style>
