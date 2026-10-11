<script setup lang="ts">
/**
 * 管理控制台组件 — 嵌入设置面板的"管理"Tab
 * 功能：审核待发布游戏（通过/拒绝/删除），分页浏览
 * 数据来源：/api/admin/control/* 管理员端点
 */
import { ElMessage, ElMessageBox } from 'element-plus'
import { api, getErrDetail } from '~/utils/request'

// ===== 待审核游戏列表 =====
interface PendingGame {
  id: number
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
    if (res.total !== undefined) {
      total.value = res.total
    } else {
      if (ids.length >= pageSize.value) {
        total.value = Math.max(total.value, currentPage.value * pageSize.value + 1)
      } else {
        total.value = (currentPage.value - 1) * pageSize.value + ids.length
      }
    }
    fetchGameDetails(ids)
  } catch (e: unknown) {
    ElMessage.error(getErrDetail(e, '加载待审核列表失败'))
    pendingList.value = []
  } finally {
    loading.value = false
  }
}

/** 批量获取游戏详情 */
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
    return
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

/** 组件挂载时加载数据 */
function init() {
  currentPage.value = 1
  fetchPendingGames()
}

defineExpose({ init })
</script>

<template>
  <div class="admin-control">
    <!-- 概览 -->
    <div class="admin-stat-row">
      <div class="admin-stat">
        <el-icon class="admin-stat-icon"><Clock /></el-icon>
        <span class="admin-stat-num">{{ total }}</span>
        <span class="admin-stat-label">待审核</span>
      </div>
      <button class="admin-refresh-btn" title="刷新列表" @click="fetchPendingGames">
        <el-icon><Refresh /></el-icon>
      </button>
    </div>

    <!-- 加载骨架 -->
    <div v-if="loading && !pendingList.length" class="admin-skeleton">
      <el-skeleton :rows="3" animated />
    </div>

    <!-- 空状态 -->
    <div v-else-if="!pendingList.length" class="admin-empty">
      <el-icon :size="32" class="admin-empty-icon"><CircleCheck /></el-icon>
      <p class="admin-empty-text">暂无待审核游戏</p>
    </div>

    <!-- 审核列表 -->
    <div v-else class="admin-list">
      <div
        v-for="game in pendingList"
        :key="game.id"
        class="admin-item"
      >
        <!-- 封面 -->
        <div class="admin-item-cover">
          <el-skeleton v-if="game.loading" :rows="0" animated style="width: 40px; height: 54px;" />
          <img
            v-else-if="game.cover"
            :src="game.cover"
            :alt="game.name || `游戏 #${game.id}`"
            class="cover-img"
          />
          <div v-else class="cover-placeholder">
            <el-icon :size="14"><Picture /></el-icon>
          </div>
        </div>

        <!-- 信息 -->
        <div class="admin-item-info">
          <div class="admin-item-name">
            <template v-if="game.loading">
              <el-skeleton :rows="1" animated style="width: 140px;" />
            </template>
            <template v-else>
              <NuxtLink :to="`/galgame/${game.id}`" class="game-link" target="_blank">
                {{ game.name || `游戏 #${game.id}` }}
              </NuxtLink>
            </template>
          </div>
          <div class="admin-item-meta">
            <span class="meta-id">#{{ game.id }}</span>
            <span v-if="game.author_name" class="meta-author">{{ game.author_name }}</span>
          </div>
        </div>

        <!-- 操作 -->
        <div class="admin-item-actions">
          <button
            class="act-btn act-btn--ok"
            title="通过"
            :disabled="operatingIds.has(game.id)"
            @click="approveGame(game.id)"
          >
            <el-icon><CircleCheck /></el-icon>
          </button>
          <button
            class="act-btn act-btn--no"
            title="拒绝"
            :disabled="operatingIds.has(game.id)"
            @click="rejectGame(game.id)"
          >
            <el-icon><CircleClose /></el-icon>
          </button>
          <button
            class="act-btn act-btn--del"
            title="删除"
            :disabled="operatingIds.has(game.id)"
            @click="deleteGame(game.id)"
          >
            <el-icon><Delete /></el-icon>
          </button>
        </div>
      </div>
    </div>

    <!-- 分页 -->
    <div v-if="total > pageSize" class="admin-pagination">
      <el-pagination
        v-model:current-page="currentPage"
        :total="total"
        :page-size="pageSize"
        layout="prev, pager, next"
        small
        background
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<style scoped>
.admin-control {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* ===== 概览行 ===== */
.admin-stat-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  background: rgba(245, 158, 11, 0.06);
  border: 1px solid rgba(245, 158, 11, 0.15);
  border-radius: 10px;
}

.admin-stat {
  display: flex;
  align-items: center;
  gap: 8px;
}

.admin-stat-icon {
  font-size: 18px;
  color: var(--el-color-warning);
}

.admin-stat-num {
  font-size: 20px;
  font-weight: 800;
  color: var(--fish-text-1);
  font-variant-numeric: tabular-nums;
}

.admin-stat-label {
  font-size: 12px;
  color: var(--fish-text-3);
}

.admin-refresh-btn {
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border-radius: 8px;
  border: 1px solid var(--fish-border);
  background: var(--fish-bg);
  color: var(--fish-text-2);
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s, background 0.2s;
}

.admin-refresh-btn:hover {
  color: var(--fish-accent);
  border-color: var(--fish-accent-border);
  background: var(--fish-accent-soft);
}

.admin-refresh-btn .el-icon {
  font-size: 15px;
}

/* ===== 骨架 / 空状态 ===== */
.admin-skeleton {
  padding: 8px 0;
}

.admin-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 28px 0;
}

.admin-empty-icon {
  color: var(--fish-text-3);
  opacity: 0.6;
}

.admin-empty-text {
  margin: 0;
  font-size: 13px;
  color: var(--fish-text-3);
}

/* ===== 审核列表 ===== */
.admin-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
  background: var(--fish-border);
  border-radius: 8px;
  overflow: hidden;
  max-height: 340px;
  overflow-y: auto;
}

.admin-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--fish-bg-2);
  transition: background 0.15s;
}

.admin-item:hover {
  background: var(--fish-accent-soft);
}

/* 封面 */
.admin-item-cover {
  flex-shrink: 0;
  width: 40px;
  height: 54px;
  border-radius: 6px;
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

/* 信息 */
.admin-item-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.admin-item-name {
  font-size: 13px;
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

.admin-item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
  color: var(--fish-text-3);
}

.meta-id {
  font-variant-numeric: tabular-nums;
}

/* 操作按钮 */
.admin-item-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  flex-shrink: 0;
}

.act-btn {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 6px;
  border: 1px solid var(--fish-border);
  background: var(--fish-bg);
  color: var(--fish-text-2);
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s, background 0.2s, opacity 0.2s;
}

.act-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.act-btn .el-icon {
  font-size: 14px;
}

.act-btn--ok:hover:not(:disabled) {
  color: var(--el-color-success);
  border-color: rgba(103, 194, 58, 0.3);
  background: rgba(103, 194, 58, 0.08);
}

.act-btn--no:hover:not(:disabled) {
  color: var(--el-color-warning);
  border-color: rgba(245, 158, 11, 0.3);
  background: rgba(245, 158, 11, 0.08);
}

.act-btn--del:hover:not(:disabled) {
  color: var(--el-color-danger);
  border-color: rgba(245, 108, 108, 0.3);
  background: rgba(245, 108, 108, 0.08);
}

/* ===== 分页 ===== */
.admin-pagination {
  display: flex;
  justify-content: center;
  padding-top: 4px;
}

/* ===== 分页组件暗色适配 ===== */
.admin-pagination :deep(.el-pagination) {
  --el-pagination-bg-color: transparent;
  --el-pagination-text-color: var(--fish-text-2);
  --el-pagination-button-bg-color: var(--fish-bg);
  --el-pagination-hover-color: var(--fish-accent);
}

.admin-pagination :deep(.el-pager li.is-active) {
  color: var(--fish-accent);
  background: var(--fish-accent-soft);
}
</style>
