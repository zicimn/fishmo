<script setup lang="ts">
import {
  CATEGORY_OPTIONS,
  PLATFORM_OPTIONS,
  type CategoryValue,
  type PlatformValue,
  type GalgameListQuery,
} from '~/types'
import { useGalgameList } from '~/composables/useGalgame'

/**
 * 全部游戏页（/games）：作品/平台均为前后端统一枚举，下拉筛选 + 网格 + 分页。
 * URL 参数 ?category= / ?platform= / ?page= 同步，支持分享/刷新保持。
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

const filters = reactive({
  category: validCategory(typeof route.query.category === 'string' ? route.query.category : ''),
  platform: validPlatform(typeof route.query.platform === 'string' ? route.query.platform : ''),
  page: Number(route.query.page) || 1,
  size: 12,
})

// 替换引用触发 useAsyncData 重新拉取（主网格）
const listQuery = ref<GalgameListQuery>({ ...filters })
const { data, pending, error, refresh } = useGalgameList(listQuery)

const total = computed(() => data.value?.total ?? 0)
const items = computed(() => data.value?.items ?? [])

function syncUrl() {
  const q: Record<string, string> = {}
  if (filters.category) q.category = filters.category
  if (filters.platform) q.platform = filters.platform
  if (filters.page > 1) q.page = String(filters.page)
  router.replace({ query: q })
}

function handleSearch() {
  filters.page = 1
  listQuery.value = { ...filters }
  syncUrl()
}

// 作品/平台为横排可点选列表：点击切换筛选并立即搜索
function selectCategory(value: CategoryValue | '') {
  if (filters.category === value) return
  filters.category = value
  handleSearch()
}

function selectPlatform(value: PlatformValue | '') {
  if (filters.platform === value) return
  filters.platform = value
  handleSearch()
}

function handlePageChange(page: number) {
  filters.page = page
  listQuery.value = { ...filters }
  syncUrl()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<template>
  <div class="games-page">
    <div class="page-head">
      <h1 class="page-title">全部游戏</h1>
      <span class="page-count">共 {{ total }} 款</span>
    </div>

    <!-- ===== 枚举筛选：作品 / 平台横排可点选 ===== -->
    <div class="filter-rows">
      <div class="filter-row">
        <span class="filter-label">作品</span>
        <button
          class="filter-chip"
          :class="{ active: !filters.category }"
          @click="selectCategory('')"
        >
          全部
        </button>
        <button
          v-for="c in CATEGORY_OPTIONS"
          :key="c.value"
          class="filter-chip"
          :class="{ active: filters.category === c.value }"
          @click="selectCategory(c.value)"
        >
          {{ c.label }}
        </button>
      </div>
      <div class="filter-row">
        <span class="filter-label">平台</span>
        <button
          class="filter-chip"
          :class="{ active: !filters.platform }"
          @click="selectPlatform('')"
        >
          全部
        </button>
        <button
          v-for="p in PLATFORM_OPTIONS"
          :key="p.value"
          class="filter-chip"
          :class="{ active: filters.platform === p.value }"
          @click="selectPlatform(p.value)"
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
      <el-empty description="暂无符合条件的游戏" class="mb" />
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
  gap: 20px;
}

.mb {
  margin-bottom: 0;
}

.page-head {
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.page-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  letter-spacing: 0.01em;
  color: var(--fish-text-1);
}
.page-title::before {
  content: '';
  width: 4px;
  height: 18px;
  border-radius: 3px;
  background: var(--fish-accent);
}
.page-count {
  font-size: 13px;
  color: var(--fish-text-3);
}

.filter-rows {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.filter-row {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.filter-label {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 700;
  color: var(--fish-text-3);
  margin-right: 2px;
}
.filter-chip {
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid var(--fish-border);
  background: var(--fish-bg-2);
  color: var(--fish-text-2);
  font-size: 13px;
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
  gap: 20px;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 8px;
}

@media (max-width: 560px) {
  .game-grid {
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 14px;
  }
}
</style>
