<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCommentList, addComment, editComment, deleteComment } from '~/composables/useComment'
import { useAuthStore } from '~/stores/auth'
import { getErrDetail } from '~/utils/request'
import type { CommentItems } from '~/types'

const props = defineProps<{ gameId: number }>()

const auth = useAuthStore()
const newContent = ref('')
const submitting = ref(false)
// 评论“作者操作（编辑/删除）”依赖客户端登录态：SSR 首帧无登录态，若直接按 isOwnComment
// 分支，登录用户浏览自己评论时会水合不一致（服务端无按钮、客户端有按钮），故等挂载后再显示。
const isMounted = ref(false)
onMounted(() => {
  isMounted.value = true
})

const { data, pending, error, refresh } = useCommentList(props.gameId)

// 行内编辑自己的评论：editingId 为正在编辑的评论 id，editContent 为编辑中的内容
const editingId = ref<number | null>(null)
const editContent = ref('')
const saving = ref(false)

function isOwnComment(entry: CommentItems): boolean {
  return !!auth.username && entry.account.username === auth.username
}

function startEdit(entry: CommentItems) {
  editingId.value = entry.item.id
  editContent.value = entry.item.content || ''
}

function cancelEdit() {
  editingId.value = null
  editContent.value = ''
}

async function handleSubmit() {
  const content = newContent.value.trim()
  if (!content) {
    ElMessage.warning('请输入评论内容')
    return
  }
  if (!auth.token) {
    navigateTo('/user')
    return
  }
  submitting.value = true
  try {
    await addComment(props.gameId, content)
    newContent.value = ''
    ElMessage.success('评论发表成功')
    refresh()
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '发表评论失败'))
  } finally {
    submitting.value = false
  }
}

async function saveEdit() {
  if (editingId.value == null) return
  const content = editContent.value.trim()
  if (!content) {
    ElMessage.warning('请输入新的评论内容')
    return
  }
  saving.value = true
  try {
    await editComment(editingId.value, content)
    ElMessage.success('评论已更新')
    cancelEdit()
    refresh()
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '编辑失败'))
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
    if (editingId.value === entry.item.id) cancelEdit()
    refresh()
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '删除失败'))
  }
}
</script>

<template>
  <section class="comment-section">
    <h3 class="section-title">评论（{{ data?.total ?? 0 }}）</h3>

    <div class="comment-editor">
      <el-input
        v-model="newContent"
        type="textarea"
        :rows="3"
        maxlength="2000"
        show-word-limit
        placeholder="写下你的评论……"
      />
      <div class="editor-actions">
        <el-button type="primary" :loading="submitting" @click="handleSubmit">发表评论</el-button>
      </div>
    </div>

    <el-skeleton v-if="pending" :rows="4" animated />
    <el-alert
      v-else-if="error"
      title="评论加载失败，请稍后重试"
      type="error"
      :closable="false"
      show-icon
    />
    <ClientOnly v-else-if="!data?.items?.length">
      <el-empty description="暂无评论，快来抢沙发" :image-size="80" />
    </ClientOnly>
    <ul v-else class="comment-list">
      <li v-for="entry in data.items" :key="entry.item.id" class="comment-item">
        <el-avatar :size="36" :src="entry.account.avatar || undefined">
          {{ entry.account.username.charAt(0).toUpperCase() || 'U' }}
        </el-avatar>
        <div class="comment-body">
          <div class="comment-head">
            <span class="comment-user">{{ entry.account.username }}</span>
            <span
              v-if="isMounted && isOwnComment(entry) && editingId !== entry.item.id"
              class="comment-actions"
            >
              <el-button size="small" text type="primary" @click="startEdit(entry)">编辑</el-button>
              <el-button size="small" text type="danger" @click="handleDelete(entry)">删除</el-button>
            </span>
          </div>
          <template v-if="editingId === entry.item.id">
            <el-input
              v-model="editContent"
              type="textarea"
              :rows="2"
              maxlength="2000"
              show-word-limit
            />
            <div class="edit-actions">
              <el-button size="small" type="primary" :loading="saving" @click="saveEdit">保存</el-button>
              <el-button size="small" @click="cancelEdit">取消</el-button>
            </div>
          </template>
          <p v-else class="comment-content">{{ entry.item.content || '（空评论）' }}</p>
        </div>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.section-title {
  margin: 0 0 16px;
  font-size: 18px;
  font-weight: 700;
}
.comment-editor {
  margin-bottom: 20px;
}
.editor-actions {
  margin-top: 10px;
  text-align: right;
}
.comment-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.comment-item {
  display: flex;
  gap: 12px;
  padding: 16px 0;
  border-bottom: 1px solid rgba(24, 24, 27, 0.08);
}
.comment-item:last-child {
  border-bottom: none;
}
html.dark .comment-item {
  border-bottom-color: rgba(255, 255, 255, 0.08);
}
.comment-body {
  flex: 1;
  min-width: 0;
}
.comment-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}
.comment-user {
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-primary);
}
.comment-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
}
.comment-content {
  margin: 0;
  font-size: 14px;
  color: var(--el-text-color-regular);
  line-height: 1.7;
  word-break: break-word;
}
.edit-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}
</style>
