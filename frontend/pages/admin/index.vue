<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '~/stores/auth'
import { api, getErrDetail } from '~/utils/request'

// 管理员守卫：非管理员跳转首页
definePageMeta({ middleware: 'admin' })

const authStore = useAuthStore()

// ===== 待审核游戏列表 =====
interface PendingGame {
  id: number
  /** 可选详情（批量补充获取） */
  name?: string
  cover?: string
  author_name?: string
  loading?: boolean
}

const pendingList = ref<PendingGame[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(10)
const loading = ref(false)

/**
 * 从后端 BrowseGal 响应中提取游戏 ID。
 * 后端 select(Galgame.id) 返回 Row 元组，JSON 序列化后可能为 [[1],[2]] 或 [1,2] 等形式。
 */
function extractId(row: unknown): number {
  if (typeof row === 'number') return row
  if (Array.isArray(row)) return Number(row[0])
  if (row && typeof row === 'object' && 'id' in row) return Number((row as { id: unknown }).id)
  return Number(row)
}

async function fetchPendingGames() {
  loading.value = true
  try {
    const res = await api<{ message: string; total?: number; data: unknown[] }>(
      '/api/admin/control/BrowseGal',
      {
        query: { page: currentPage.value, size: pageSize.value },
      },
    )
    const ids = (res.data || []).map(extractId).filter((id) => id > 0)
    pendingList.value = ids.map((id) => ({ id, loading: true }))
    // 使用后端返回的 total（BrowseGal 已包含 total 字段）
    if (res.total !== undefined) {
      total.value = res.total
    } else {
      // 兜底：后端未返回 total 时用列表长度估算
      if (ids.length >= pageSize.value) {
        total.value = Math.max(total.value, (currentPage.value) * pageSize.value + 1)
      } else {
        total.value = (currentPage.value - 1) * pageSize.value + ids.length
      }
    }
    // 批量补充游戏详情（并行请求，提升体验）
    fetchGameDetails(ids)
  } catch (e: unknown) {
    ElMessage.error(getErrDetail(e, '加载待审核列表失败'))
    pendingList.value = []
  } finally {
    loading.value = false
  }
}

/** 批量获取游戏详情（公开端点 + admin token 可查看未审核游戏） */
async function fetchGameDetails(ids: number[]) {
  const tasks = ids.map(async (id) => {
    try {
      const detail = await api<{
        id: number
        name: string
        cover: string
        author_name?: string
      }>(`/api/v1/galgame/${id}`)
      const item = pendingList.value.find((g: PendingGame) => g.id === id)
      if (item) {
        item.name = detail.name
        item.cover = detail.cover
        item.author_name = detail.author_name
        item.loading = false
      }
    } catch {
      // 详情获取失败不影响列表展示，仅标记加载完成
      const item = pendingList.value.find((g: PendingGame) => g.id === id)
      if (item) item.loading = false
    }
  })
  await Promise.allSettled(tasks)
}

// ===== 审核操作 =====
const operatingIds = ref<Set<number>>(new Set())

async function approveGame(galId: number) {
  operatingIds.value.add(galId)
  try {
    await api<{ message: string }>(
      '/api/admin/control/UpdateStatus',
      {
        method: 'PUT',
        query: { gal_id: galId, status: true },
      },
    )
    ElMessage.success(`游戏 #${galId} 已通过审核`)
    // 从列表中移除
    pendingList.value = pendingList.value.filter((g: PendingGame) => g.id !== galId)
    total.value = Math.max(0, total.value - 1)
  } catch (e: unknown) {
    ElMessage.error(getErrDetail(e, '操作失败'))
  } finally {
    operatingIds.value.delete(galId)
  }
}

async function rejectGame(galId: number) {
  operatingIds.value.add(galId)
  try {
    await api<{ message: string }>(
      '/api/admin/control/UpdateStatus',
      {
        method: 'PUT',
        query: { gal_id: galId, status: false },
      },
    )
    ElMessage.success(`游戏 #${galId} 已拒绝`)
    pendingList.value = pendingList.value.filter((g: PendingGame) => g.id !== galId)
    total.value = Math.max(0, total.value - 1)
  } catch (e: unknown) {
    ElMessage.error(getErrDetail(e, '操作失败'))
  } finally {
    operatingIds.value.delete(galId)
  }
}

async function deleteGame(galId: number) {
  try {
    await ElMessageBox.confirm(
      `确定要永久删除游戏 #${galId} 吗？此操作不可撤销。`,
      '确认删除',
      { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'warning' },
    )
  } catch {
    return // 用户取消
  }

  operatingIds.value.add(galId)
  try {
    await api<{ message: string }>(
      '/api/admin/control/DeleteGal',
      {
        method: 'DELETE',
        query: { gal_id: galId },
      },
    )
    ElMessage.success(`游戏 #${galId} 已删除`)
    pendingList.value = pendingList.value.filter((g: PendingGame) => g.id !== galId)
    total.value = Math.max(0, total.value - 1)
  } catch (e: unknown) {
    ElMessage.error(getErrDetail(e, '删除失败'))
  } finally {
    operatingIds.value.delete(galId)
  }
}

function handlePageChange(page: number) {
  currentPage.value = page
  fetchPendingGames()
}

function handleSizeChange(size: number) {
  pageSize.value = size
  currentPage.value = 1
  fetchPendingGames()
}

onMounted(() => fetchPendingGames())
</script>

<template>
  <div class="admin-page">
    <!-- ===== 页头 ===== -->
    <div class="admin-header">
      <h2 class="page-title">管理控制台</h2>
      <p class="page-desc">审核管理待发布的游戏内容</p>
    </div>

    <!-- ===== 概览卡片 ===== -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="stat-icon stat-icon--pending">
          <el-icon :size="24"><Clock /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">{{ total }}</span>
          <span class="stat-label">待审核游戏</span>
        </div>
      </div>
      <div class="stat-card stat-card--link" @click="fetchPendingGames()">
        <div class="stat-icon stat-icon--refresh">
          <el-icon :size="24"><Refresh /></el-icon>
        </div>
        <div class="stat-info">
          <span class="stat-value">刷新</span>
          <span class="stat-label">重新加载列表</span>
        </div>
      </div>
    </div>

    <!-- ===== 审核列表 ===== -->
    <el-card shadow="never" class="review-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">待审核列表</span>
          <el-tag size="small" effect="plain">{{ total }} 条待审核</el-tag>
        </div>
      </template>

      <el-skeleton v-if="loading && !pendingList.length" :rows="5" animated />

      <div v-else-if="!pendingList.length" class="admin-empty">
            <img src="/status/1.png" alt="无待审核" class="empty-404" />
            <p class="empty-text">暂无待审核游戏</p>
          </div>

      <div v-else class="review-list">
        <div
          v-for="game in pendingList"
          :key="game.id"
          class="review-item"
        >
          <!-- 封面缩略图 -->
          <div class="review-cover">
            <el-skeleton v-if="game.loading" :rows="0" animated style="width: 60px; height: 80px;" />
            <img
              v-else-if="game.cover"
              :src="game.cover"
              :alt="game.name || `游戏 #${game.id}`"
              class="cover-img"
            />
            <div v-else class="cover-placeholder">
              <el-icon :size="20"><Picture /></el-icon>
            </div>
          </div>

          <!-- 游戏信息 -->
          <div class="review-info">
            <div class="review-name">
              <template v-if="game.loading">
                <el-skeleton :rows="1" animated style="width: 200px;" />
              </template>
              <template v-else>
                <NuxtLink :to="`/galgame/${game.id}`" class="game-link" target="_blank">
                  {{ game.name || `游戏 #${game.id}` }}
                </NuxtLink>
              </template>
            </div>
            <div class="review-meta">
              <el-tag size="small" type="info">ID {{ game.id }}</el-tag>
              <span v-if="game.author_name" class="meta-author">
                发布者：{{ game.author_name }}
              </span>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="review-actions">
            <el-button
              type="success"
              size="small"
              :loading="operatingIds.has(game.id)"
              @click="approveGame(game.id)"
            >
              <el-icon><CircleCheck /></el-icon>
              通过
            </el-button>
            <el-button
              type="warning"
              size="small"
              :loading="operatingIds.has(game.id)"
              @click="rejectGame(game.id)"
            >
              <el-icon><CircleClose /></el-icon>
              拒绝
            </el-button>
            <el-button
              type="danger"
              size="small"
              :loading="operatingIds.has(game.id)"
              @click="deleteGame(game.id)"
            >
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </div>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="total > 0" class="review-pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          background
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>
  </div>
</template>

<style scoped>
.admin-page {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ===== 页头 ===== */
.admin-header {
  padding-bottom: 4px;
}
.page-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 6px;
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
  background: var(--el-color-warning);
}
.page-desc {
  margin: 0;
  font-size: 14px;
  color: var(--fish-text-3);
}

/* ===== 概览卡片 ===== */
.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}
.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  background: var(--fish-bg-2);
  border: 1px solid var(--fish-border);
  border-radius: var(--fish-radius);
  box-shadow: var(--fish-shadow);
}
.stat-card--link {
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.stat-card--link:hover {
  border-color: var(--fish-accent-border);
  box-shadow: var(--fish-shadow-hover);
}
.stat-icon {
  width: 48px;
  height: 48px;
  display: grid;
  place-items: center;
  border-radius: 12px;
  flex-shrink: 0;
}
.stat-icon--pending {
  background: rgba(245, 158, 11, 0.12);
  color: var(--el-color-warning);
}
.stat-icon--refresh {
  background: var(--fish-accent-soft);
  color: var(--fish-accent);
}
.stat-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.stat-value {
  font-size: 22px;
  font-weight: 800;
  color: var(--fish-text-1);
  line-height: 1.2;
}
.stat-label {
  font-size: 13px;
  color: var(--fish-text-3);
}

/* ===== 审核列表卡片 ===== */
.review-card {
  --el-card-bg-color: var(--fish-bg-2);
  --el-card-border-color: var(--fish-border);
  background: var(--fish-bg-2);
  border: 1px solid var(--fish-border);
  border-radius: var(--fish-radius);
  box-shadow: var(--fish-shadow);
}
.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.card-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--fish-text-1);
}

/* ===== 审核条目 ===== */
.review-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
  background: var(--fish-border);
  border-radius: var(--fish-radius-sm);
  overflow: hidden;
}
.review-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  background: var(--fish-bg-2);
  transition: background 0.15s;
}
.review-item:hover {
  background: var(--fish-accent-soft);
}

/* 封面缩略图 */
.review-cover {
  flex-shrink: 0;
  width: 60px;
  height: 80px;
  border-radius: var(--fish-radius-xs);
  overflow: hidden;
  background: var(--fish-bg);
  border: 1px solid var(--fish-border);
}
.cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.cover-placeholder {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  color: var(--fish-text-3);
}

/* 游戏信息 */
.review-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.review-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--fish-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.game-link {
  color: var(--fish-text-1);
  text-decoration: none;
  transition: color 0.2s;
}
.game-link:hover {
  color: var(--fish-accent);
}
.review-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.meta-author {
  font-size: 13px;
  color: var(--fish-text-3);
}

/* 操作按钮 */
.review-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

/* 分页 */
.review-pagination {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid var(--fish-border);
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .review-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  .review-cover {
    width: 48px;
    height: 64px;
  }
  .review-actions {
    width: 100%;
    justify-content: flex-end;
  }
  .stat-cards {
    grid-template-columns: 1fr;
  }
}

.admin-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--fish-space-md);
  padding: var(--fish-space-2xl) var(--fish-space-lg);
}

.admin-empty .empty-404 {
  width: 260px;
  max-width: 70%;
  border-radius: 12px;
  opacity: 0.85;
}

.admin-empty .empty-text {
  margin: 0;
  font-size: var(--fish-text-lg);
  color: var(--fish-text-3);
}
</style>
