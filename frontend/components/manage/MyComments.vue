<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import type { CommentItems } from '~/types'
import { useUserCommentList, editComment, deleteComment } from '~/composables/useComment'
import { useAuthStore } from '~/stores/auth'
import { getErrDetail } from '~/utils/request'

/** 我的评论：分页管理列表 + 行内编辑（供个人主页「评论」tab 与 /manage 复用）。 */
const auth = useAuthStore()
const SIZE = 20
const page = ref(1)

const query = computed<{ userId?: number; page?: number; size?: number }>(() => ({
  userId: auth.userId ?? undefined,
  page: page.value,
  size: SIZE,
}))
const { data, pending, refresh } = useUserCommentList(query, { key: 'my-comments' })

const dialog = ref(false)
const saving = ref(false)
const form = reactive({ id: 0, content: '' })

function openEdit(entry: CommentItems) {
  form.id = entry.item.id
  form.content = entry.item.content || ''
  dialog.value = true
}

async function submitEdit() {
  if (!form.content.trim()) {
    ElMessage.warning('评论内容不能为空')
    return
  }
  saving.value = true
  try {
    await editComment(form.id, form.content.trim())
    ElMessage.success('评论已更新')
    dialog.value = false
    refresh()
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '更新失败'))
  } finally {
    saving.value = false
  }
}

async function handleDelete(entry: CommentItems) {
  try {
    await ElMessageBox.confirm('确定删除该评论吗？', '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await deleteComment(entry.item.id)
    ElMessage.success('评论已删除')
    refresh()
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '删除失败'))
  }
}
</script>

<template>
  <div class="my-comments">
    <el-skeleton v-if="pending && !data?.items?.length" :rows="6" animated />
    <ClientOnly v-else-if="!data?.items?.length">
      <el-empty description="还没有发表评论" :image-size="90" />
    </ClientOnly>

    <template v-else>
      <ul class="m-list">
        <li v-for="entry in data.items" :key="entry.item.id" class="m-item">
          <div class="m-main">
            <div class="m-title m-title-wrap">{{ entry.item.content || '（空评论）' }}</div>
            <div class="m-meta">
              <NuxtLink :to="`/galgame/${entry.item.receive_id}`" class="m-taglink">
                游戏 #{{ entry.item.receive_id }}
              </NuxtLink>
            </div>
          </div>
          <div class="m-actions">
            <el-button size="small" type="primary" plain @click="openEdit(entry)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="handleDelete(entry)">删除</el-button>
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

    <!-- 编辑评论对话框 -->
    <el-dialog v-model="dialog" title="编辑评论" width="520px">
      <el-input
        v-model="form.content"
        type="textarea"
        :rows="4"
        maxlength="2000"
        show-word-limit
        placeholder="评论内容"
      />
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
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
.m-main {
  flex: 1;
  min-width: 0;
}
.m-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--fish-text-1);
}
.m-title-wrap {
  white-space: normal;
  word-break: break-word;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.m-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 4px;
}
.m-taglink {
  font-size: 12px;
  color: var(--fish-text-3);
  text-decoration: none;
}
.m-taglink:hover {
  color: var(--fish-accent);
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
