<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { useArticleManage, deleteArticle } from '~/composables/useArticle'
import { getErrDetail } from '~/utils/request'
import type { ArticleManageItem } from '~/types'

/** 我的文章：小型卡片网格（供管理页与个人主页复用）。 */
const SIZE = ref(20)
const page = ref(1)

const { data, pending, refresh } = useArticleManage(page, SIZE)

async function handleDelete(item: ArticleManageItem) {
  try {
    await ElMessageBox.confirm('确定删除该文章吗？删除后不可恢复。', '删除文章', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await deleteArticle(item.id)
    ElMessage.success('删除成功')
    refresh()
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '删除失败'))
  }
}
</script>

<template>
  <div class="my-articles">
    <el-skeleton v-if="pending && !data?.items?.length" :rows="4" animated />
    <ClientOnly v-else-if="!data?.items?.length">
      <el-empty description="还没有发布文章" :image-size="90" />
    </ClientOnly>

    <template v-else>
      <div class="card-grid">
        <div v-for="item in data.items" :key="item.id" class="mini-card">
          <NuxtLink :to="`/article/${item.id}`" class="card-link">
            <div class="card-cover">
              <el-image v-if="item.cover" :src="item.cover" fit="cover" class="cover-img" lazy>
                <template #error>
                  <div class="cover-placeholder">无封面</div>
                </template>
              </el-image>
              <div v-else class="cover-placeholder">
                <span class="placeholder-icon">A</span>
              </div>
            </div>
            <div class="card-name">{{ item.title }}</div>
          </NuxtLink>
          <div class="card-actions">
            <el-button
              size="small"
              text
              @click="navigateTo(`/manage/article/${item.id}`)"
            >
              编辑
            </el-button>
            <el-button size="small" text type="danger" @click="handleDelete(item)">删除</el-button>
          </div>
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
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 12px;
}

.mini-card {
  border: 1px solid var(--fish-border);
  border-radius: var(--fish-radius-sm);
  overflow: hidden;
  background: transparent;
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1),
    border-color 0.2s cubic-bezier(0.16, 1, 0.3, 1),
    box-shadow 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.mini-card:hover {
  transform: translateY(-2px);
  border-color: var(--fish-accent-border);
  box-shadow: var(--fish-shadow-hover);
}

.card-link {
  display: flex;
  flex-direction: column;
  color: inherit;
  text-decoration: none;
}

.card-cover {
  aspect-ratio: 2 / 3;
  overflow: hidden;
  background: transparent;
}

.cover-img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.mini-card:hover .cover-img {
  transform: scale(1.04);
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--fish-text-3);
  font-size: var(--fish-text-sm);
  background: transparent;
}

.placeholder-icon {
  font-size: 28px;
  font-weight: 700;
  color: var(--fish-accent);
  opacity: 0.4;
}

.card-name {
  padding: 8px 10px;
  font-size: var(--fish-text-sm);
  font-weight: 600;
  color: var(--fish-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  text-align: center;
  transition: color 0.2s;
}

.card-link:hover .card-name {
  color: var(--fish-accent);
}

.card-actions {
  display: flex;
  justify-content: center;
  gap: 2px;
  padding: 0 8px 8px;
}

.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

@media (max-width: 560px) {
  .card-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
}
</style>