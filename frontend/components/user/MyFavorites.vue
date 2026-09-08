<script setup lang="ts">
import { useFavoriteList, removeFavorite } from '~/composables/useFavorite'
import { getErrDetail } from '~/utils/request'
import { ElMessage } from 'element-plus'

/** 我的收藏：小封面卡片网格 + 分页，封面优先、不显示浏览量 */
const SIZE = 12
const page = ref(1)

const query = computed(() => ({
  page: page.value,
  size: SIZE,
}))

const { data, pending, refresh } = useFavoriteList(query)

/** 取消收藏 */
const removingIds = ref<Set<number>>(new Set())

async function handleRemove(item: { id: number; name: string }) {
  if (removingIds.value.has(item.id)) return
  removingIds.value.add(item.id)
  try {
    await removeFavorite(item.id)
    ElMessage.success('已取消收藏')
    refresh()
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '取消收藏失败'))
  } finally {
    removingIds.value.delete(item.id)
  }
}
</script>

<template>
  <div class="my-favorites">
    <el-skeleton v-if="pending && !data?.items?.length" :rows="4" animated />
    <ClientOnly v-else-if="!data?.items?.length">
      <el-empty description="还没有收藏任何游戏" :image-size="90" />
    </ClientOnly>

    <template v-else>
      <div class="fav-grid">
        <div v-for="item in data.items" :key="item.id" class="fav-card">
          <NuxtLink :to="`/galgame/${item.id}`" class="fav-link">
            <!-- 2:3 封面 -->
            <div class="fav-cover">
              <el-image :src="item.cover" fit="cover" class="cover-img" lazy>
                <template #error>
                  <div class="cover-ph">
                    <el-icon :size="20"><Picture /></el-icon>
                  </div>
                </template>
              </el-image>
            </div>
            <!-- 游戏名 -->
            <div class="fav-name" :title="item.name">{{ item.name }}</div>
          </NuxtLink>

          <!-- 取消收藏按钮 -->
          <button
            class="fav-remove-btn"
            :class="{ 'is-loading': removingIds.has(item.id) }"
            :disabled="removingIds.has(item.id)"
            title="取消收藏"
            @click.stop="handleRemove(item)"
          >
            <el-icon :size="12" :class="{ 'spin-icon': removingIds.has(item.id) }">
              <Close />
            </el-icon>
          </button>
        </div>
      </div>
      <div class="pagination-wrap">
        <el-pagination
          layout="prev, pager, next, total"
          :total="data.total"
          :page-size="SIZE"
          :current-page="page"
          @current-change="(p: number) => (page = p)"
        />
      </div>
    </template>
  </div>
</template>

<style scoped>
/* 小封面卡片网格 */
.fav-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(130px, 1fr));
  gap: var(--fish-space-md);
}

.fav-card {
  position: relative;
}

.fav-link {
  display: block;
  text-decoration: none;
  color: inherit;
}

/* 2:3 封面 */
.fav-cover {
  position: relative;
  aspect-ratio: 2 / 3;
  border-radius: var(--fish-radius-sm);
  overflow: hidden;
  background: var(--fish-bg-2);
  border: 1px solid var(--fish-border-strong);
  box-shadow: var(--fish-shadow);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.fav-link:hover .fav-cover {
  border-color: var(--fish-accent-border);
  box-shadow: var(--fish-shadow-hover);
}

.cover-img {
  width: 100%;
  height: 100%;
  display: block;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.fav-link:hover .cover-img {
  transform: scale(1.04);
}

.cover-ph {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--fish-text-3);
}

/* 游戏名 */
.fav-name {
  margin-top: var(--fish-space-xs);
  font-size: var(--fish-text-sm);
  font-weight: 600;
  line-height: var(--fish-leading-snug);
  color: var(--fish-text-1);
  text-align: center;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color 0.2s;
}

.fav-link:hover .fav-name {
  color: var(--fish-accent);
}

/* 取消收藏按钮：卡片右上角 */
.fav-remove-btn {
  position: absolute;
  top: var(--fish-space-sm);
  right: var(--fish-space-sm);
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s, background 0.2s, color 0.2s;
  z-index: 2;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.fav-card:hover .fav-remove-btn {
  opacity: 1;
}

.fav-remove-btn:hover {
  background: var(--el-color-danger);
  color: #fff;
}

.fav-remove-btn.is-loading {
  opacity: 1;
  cursor: not-allowed;
}

.spin-icon {
  animation: fav-spin 0.8s linear infinite;
}

@keyframes fav-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: var(--fish-space-lg);
}

@media (max-width: 560px) {
  .fav-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: var(--fish-space-sm);
  }
}
</style>
