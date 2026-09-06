<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import type { GalgameListQuery, GalItem } from '~/types'
import { useGalgameList, deleteGalgame } from '~/composables/useGalgame'
import { useAuthStore } from '~/stores/auth'
import { getErrDetail } from '~/utils/request'

/** 我的游戏：分页管理列表（供个人主页「游戏」tab 与 /manage 复用）。 */
const auth = useAuthStore()
const SIZE = 20
const page = ref(1)

const query = computed<GalgameListQuery>(() => ({
  author_id: auth.userId ?? undefined,
  page: page.value,
  size: SIZE,
}))
// server:false —— userId 来自 localStorage 恢复的登录态，SSR 时为空，避免拉取全量游戏
const { data, pending, refresh } = useGalgameList(query, { key: 'my-games', server: false })

async function handleDelete(item: GalItem) {
  try {
    await ElMessageBox.confirm('确定删除该游戏吗？删除后不可恢复。', '删除游戏', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await deleteGalgame(item.id)
    ElMessage.success('删除成功')
    refresh()
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '删除失败'))
  }
}
</script>

<template>
  <div class="my-games">
    <el-skeleton v-if="pending && !data?.items?.length" :rows="6" animated />
    <ClientOnly v-else-if="!data?.items?.length">
      <el-empty description="还没有发布游戏" :image-size="90" />
    </ClientOnly>

    <template v-else>
      <ul class="m-list">
        <li v-for="item in data.items" :key="item.id" class="m-item m-item-game">
          <el-image :src="item.cover" class="m-cover" fit="cover" lazy />
          <div class="m-main">
            <div class="m-title">
              <NuxtLink :to="`/galgame/${item.id}`" class="m-link">{{ item.name }}</NuxtLink>
            </div>
            <div class="m-meta">
              <el-tag size="small" type="info" effect="plain">浏览 {{ item.views }}</el-tag>
              <el-tag v-if="item.author" size="small" effect="plain">{{ item.author }}</el-tag>
            </div>
          </div>
          <div class="m-actions">
            <el-button size="small" type="primary" plain @click="navigateTo(`/manage/${item.id}`)">
              编辑
            </el-button>
            <el-button size="small" type="danger" plain @click="handleDelete(item)">删除</el-button>
          </div>
        </li>
      </ul>
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
.m-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.m-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--fish-border);
  border-radius: 10px;
  margin-bottom: 8px;
  background: var(--fish-bg-2);
  transition: border-color 0.2s, transform 0.2s;
}
.m-item:hover {
  border-color: var(--fish-accent-border);
  transform: translateY(-1px);
}
.m-cover {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  flex-shrink: 0;
}
.m-main {
  flex: 1;
  min-width: 0;
}
.m-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--fish-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.m-link {
  color: var(--fish-accent);
  text-decoration: none;
}
.m-link:hover {
  text-decoration: underline;
}
.m-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 4px;
}
.m-actions {
  flex-shrink: 0;
  display: flex;
  gap: 6px;
}
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

@media (max-width: 560px) {
  .m-item {
    flex-wrap: wrap;
  }
  .m-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
