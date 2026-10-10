<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCommentList, addComment, editComment, deleteComment } from '~/composables/useComment'
import { useAuthStore } from '~/stores/auth'
import { getErrDetail } from '~/utils/request'
import type { CommentItems } from '~/types'

const props = defineProps<{ gameId: number; type?: string }>()

const commentType = computed(() => props.type || 'galgame')

const auth = useAuthStore()
const newContent = ref('')
const submitting = ref(false)
// 评论“作者操作（编辑/删除）”依赖客户端登录态：SSR 首帧无登录态，若直接按 isOwnComment
// 分支，登录用户浏览自己评论时会水合不一致（服务端无按钮、客户端有按钮），故等挂载后再显示。
const isMounted = ref(false)
onMounted(() => {
  isMounted.value = true
})

const { data, pending, error, refresh } = useCommentList(props.gameId, 1, 20, commentType.value)

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
    await addComment(props.gameId, content, commentType.value)
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
      <div class="ce-textarea-wrap">
        <el-input
          v-model="newContent"
          type="textarea"
          :rows="3"
          maxlength="2000"
          show-word-limit
          placeholder="写下你的评论……"
          class="ce-textarea"
        />
      </div>
      <div class="editor-actions">
        <button class="ce-submit-btn" :disabled="submitting" @click="handleSubmit">
          <span v-if="submitting" class="ce-btn-spinner"></span>
          <svg v-else class="ce-btn-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/>
          </svg>
          {{ submitting ? '发表中...' : '发表评论' }}
        </button>
      </div>
    </div>

    <el-skeleton v-if="pending" :rows="4" animated />
    <div v-else-if="error" class="empty-img">
      <img src="/status/1.png" alt="加载失败" />
      <p>评论加载失败，请稍后重试</p>
    </div>
    <ClientOnly v-else-if="!data?.items?.length">
      <div class="empty-img">
        <img src="/status/2.png" alt="暂无评论" />
        <p>暂无评论</p>
      </div>
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
              class="ce-textarea"
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
/* ===== Section Header ===== */
.section-title {
  margin: 0 0 var(--fish-space-lg);
  font-size: var(--fish-text-lg);
  font-weight: 700;
  color: var(--fish-text-1);
}

/* ===== Comment Editor — 类发布页玻璃风格 ===== */
.comment-editor {
  margin-bottom: var(--fish-space-xl);
  background: rgba(24, 24, 31, 0.6);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--fish-radius);
  padding: var(--fish-space-lg);
  transition: border-color 0.2s;
}

.comment-editor:focus-within {
  border-color: rgba(124, 123, 242, 0.2);
}

.ce-textarea-wrap {
  width: 100%;
}

.ce-textarea :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: none;
  border-radius: var(--fish-radius-sm);
  color: var(--fish-text-1);
  font-family: inherit;
  font-size: 0.875rem;
  line-height: 1.7;
  padding: 0.65rem 0.75rem;
  transition: border-color 0.2s, background 0.2s;
  resize: vertical;
}

.ce-textarea :deep(.el-textarea__inner:focus) {
  border-color: rgba(124, 123, 242, 0.3);
  background: rgba(255, 255, 255, 0.03);
  box-shadow: none;
}

.ce-textarea :deep(.el-textarea__inner::placeholder) {
  color: var(--fish-text-3);
  font-size: 0.85rem;
}

.ce-textarea :deep(.el-input__count) {
  color: var(--fish-text-3);
  font-size: 0.7rem;
  background: transparent;
}

.editor-actions {
  margin-top: var(--fish-space-md);
  display: flex;
  justify-content: flex-end;
}

/* ===== 发表按钮（类 ae-publish-btn 风格） ===== */
.ce-submit-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.45rem;
  padding: 0.55rem 1.1rem;
  background: var(--fish-accent);
  border: none;
  border-radius: 0.5rem;
  color: #fff;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  letter-spacing: 0.01em;
  transition: background 0.2s, transform 0.2s, box-shadow 0.2s;
  line-height: 1;
}

.ce-submit-btn:hover:not(:disabled) {
  background: #8F8EF5;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(124, 123, 242, 0.25);
}

.ce-submit-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.ce-submit-btn:disabled {
  background: rgba(124, 123, 242, 0.35);
  color: rgba(255, 255, 255, 0.5);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.ce-btn-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: #fff;
  border-radius: 50%;
  animation: ce-spin 0.7s linear infinite;
  flex-shrink: 0;
}

.ce-btn-icon {
  flex-shrink: 0;
}

@keyframes ce-spin {
  to { transform: rotate(360deg); }
}

/* ===== Comment List ===== */
.comment-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.comment-item {
  display: flex;
  gap: var(--fish-space-md);
  padding: var(--fish-space-lg) 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.comment-item:last-child {
  border-bottom: none;
}

.comment-body {
  flex: 1;
  min-width: 0;
}

.comment-head {
  display: flex;
  align-items: center;
  gap: var(--fish-space-sm);
  margin-bottom: var(--fish-space-xs);
}

.comment-user {
  font-weight: 600;
  font-size: var(--fish-text-sm);
  color: var(--fish-text-1);
}

.comment-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 2px;
}

.comment-content {
  margin: 0;
  font-size: var(--fish-text-sm);
  color: var(--fish-text-2);
  line-height: 1.7;
  word-break: break-word;
}

/* ===== Edit Mode ===== */
.edit-actions {
  margin-top: var(--fish-space-sm);
  display: flex;
  gap: var(--fish-space-sm);
}

/* ===== Empty State — 使用 fishmo 空状态插图 ===== */
.empty-img {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 0;
}

.empty-img img {
  width: 240px;
  max-width: 70%;
  border-radius: 12px;
  opacity: 0.85;
}

.empty-img p {
  margin: 0;
  font-size: 15px;
  color: var(--fish-text-3);
}
</style>
