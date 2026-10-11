<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { useCommentList, addComment, editComment, deleteComment } from '~/composables/useComment'
import { useAuthStore } from '~/stores/auth'
import { getErrDetail } from '~/utils/request'
import type { NestedCommentItems, ReplyItems } from '~/types'

const props = defineProps<{ gameId: number; type?: string }>()

const commentType = computed(() => props.type || 'galgame')

const auth = useAuthStore()
const newContent = ref('')
const submitting = ref(false)
// 评论"作者操作（编辑/删除）"依赖客户端登录态：SSR 首帧无登录态，若直接按 isOwnComment
// 分支，登录用户浏览自己评论时会水合不一致（服务端无按钮、客户端有按钮），故等挂载后再显示。
const isMounted = ref(false)
onMounted(() => {
  isMounted.value = true
})

const { data, pending, error, refresh } = useCommentList(props.gameId, 1, 20, commentType.value)

// 行内编辑自己的评论
const editingId = ref<number | null>(null)
const editContent = ref('')
const saving = ref(false)

// 回复状态：replyingTo 记录当前展开回复框的目标
// { parentId: 顶级评论 ID, replyToId: 被回复用户 ID | null, username: 被回复用户名（用于 placeholder） }
const replyingTo = ref<{
  parentId: number
  replyToId: number | null
  username: string
} | null>(null)
const replyContent = ref('')
const replySubmitting = ref(false)

function isOwnComment(accountUsername: string): boolean {
  return !!auth.username && accountUsername === auth.username
}

function startEdit(entry: NestedCommentItems | ReplyItems) {
  editingId.value = entry.item.id
  editContent.value = entry.item.content || ''
}

function cancelEdit() {
  editingId.value = null
  editContent.value = ''
}

// 展开回复顶级评论
function replyToTop(entry: NestedCommentItems) {
  replyingTo.value = {
    parentId: entry.item.id,
    replyToId: null,
    username: entry.account.username,
  }
  replyContent.value = ''
  nextTick(() => {
    const el = document.querySelector('.reply-input-inner textarea') as HTMLTextAreaElement | null
    el?.focus()
  })
}

// 展开回复子评论
function replyToReply(topId: number, reply: ReplyItems) {
  replyingTo.value = {
    parentId: topId,
    replyToId: reply.item.id,
    username: reply.account.username,
  }
  replyContent.value = ''
  nextTick(() => {
    const el = document.querySelector('.reply-input-inner textarea') as HTMLTextAreaElement | null
    el?.focus()
  })
}

function cancelReply() {
  replyingTo.value = null
  replyContent.value = ''
}

// 发表顶级评论
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

// 发表回复
async function handleReplySubmit() {
  if (!replyingTo.value) return
  const content = replyContent.value.trim()
  if (!content) {
    ElMessage.warning('请输入回复内容')
    return
  }
  if (!auth.token) {
    navigateTo('/user')
    return
  }
  replySubmitting.value = true
  try {
    await addComment(
      props.gameId,
      content,
      commentType.value,
      replyingTo.value.parentId,
      replyingTo.value.replyToId,
    )
    replyContent.value = ''
    replyingTo.value = null
    ElMessage.success('回复发表成功')
    refresh()
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '回复失败'))
  } finally {
    replySubmitting.value = false
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

async function handleDelete(entry: NestedCommentItems | ReplyItems) {
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

// 计算未加载的回复数
function remainingReplies(entry: NestedCommentItems): number {
  return Math.max(0, entry.reply_count - entry.replies.length)
}
</script>

<template>
  <section class="comment-section">
    <h3 class="section-title">评论（{{ data?.total ?? 0 }}）</h3>

    <!-- 顶级评论输入框 -->
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
        <!-- 顶级评论头像 -->
        <el-avatar :size="36" :src="entry.account.avatar || undefined" class="comment-avatar">
          {{ entry.account.username.charAt(0).toUpperCase() || 'U' }}
        </el-avatar>
        <div class="comment-body">
          <!-- 顶级评论头部 -->
          <div class="comment-head">
            <span class="comment-user">{{ entry.account.username }}</span>
            <span
              v-if="isMounted && isOwnComment(entry.account.username) && editingId !== entry.item.id"
              class="comment-actions"
            >
              <el-button size="small" text type="primary" @click="startEdit(entry)">编辑</el-button>
              <el-button size="small" text type="danger" @click="handleDelete(entry)">删除</el-button>
            </span>
          </div>

          <!-- 编辑模式 -->
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

          <!-- 回复按钮 -->
          <div class="reply-btn-row">
            <button
              class="reply-trigger-btn"
              @click="replyToTop(entry)"
            >
              <svg class="reply-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="9 17 4 12 9 7"/><path d="M20 18v-2a4 4 0 0 0-4-4H4"/>
              </svg>
              回复
            </button>
          </div>

          <!-- 回复输入框（顶级评论下展开） -->
          <div v-if="replyingTo && replyingTo.parentId === entry.item.id && !replyingTo.replyToId" class="reply-input-wrap">
            <div class="reply-input-inner">
              <el-input
                v-model="replyContent"
                type="textarea"
                :rows="2"
                maxlength="2000"
                :placeholder="`回复 @${replyingTo.username}……`"
                class="ce-textarea reply-textarea"
              />
              <div class="reply-input-actions">
                <el-button size="small" @click="cancelReply">取消</el-button>
                <button class="ce-submit-btn ce-submit-btn--sm" :disabled="replySubmitting" @click="handleReplySubmit">
                  <span v-if="replySubmitting" class="ce-btn-spinner"></span>
                  {{ replySubmitting ? '发表中...' : '回复' }}
                </button>
              </div>
            </div>
          </div>

          <!-- 子评论列表（第 2 层） -->
          <ul v-if="entry.replies && entry.replies.length" class="reply-list">
            <li
              v-for="reply in entry.replies"
              :key="reply.item.id"
              class="reply-item"
            >
              <el-avatar :size="28" :src="reply.account.avatar || undefined" class="reply-avatar">
                {{ reply.account.username.charAt(0).toUpperCase() || 'U' }}
              </el-avatar>
              <div class="reply-body">
                <div class="reply-head">
                  <span class="reply-user">{{ reply.account.username }}</span>
                  <template v-if="reply.reply_to_account">
                    <span class="reply-to-label">回复</span>
                    <span class="reply-to-user">@{{ reply.reply_to_account.username }}</span>
                  </template>
                  <span
                    v-if="isMounted && isOwnComment(reply.account.username) && editingId !== reply.item.id"
                    class="comment-actions"
                  >
                    <el-button size="small" text type="primary" @click="startEdit(reply)">编辑</el-button>
                    <el-button size="small" text type="danger" @click="handleDelete(reply)">删除</el-button>
                  </span>
                </div>

                <!-- 子评论编辑模式 -->
                <template v-if="editingId === reply.item.id">
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
                <p v-else class="reply-content">{{ reply.item.content || '（空评论）' }}</p>

                <!-- 子评论回复按钮 -->
                <button
                  class="reply-trigger-btn reply-trigger-btn--sm"
                  @click="replyToReply(entry.item.id, reply)"
                >
                  <svg class="reply-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="9 17 4 12 9 7"/><path d="M20 18v-2a4 4 0 0 0-4-4H4"/>
                  </svg>
                  回复
                </button>

                <!-- 子评论回复输入框 -->
                <div v-if="replyingTo && replyingTo.parentId === entry.item.id && replyingTo.replyToId === reply.item.id" class="reply-input-wrap">
                  <div class="reply-input-inner">
                    <el-input
                      v-model="replyContent"
                      type="textarea"
                      :rows="2"
                      maxlength="2000"
                      :placeholder="`回复 @${replyingTo.username}……`"
                      class="ce-textarea reply-textarea"
                    />
                    <div class="reply-input-actions">
                      <el-button size="small" @click="cancelReply">取消</el-button>
                      <button class="ce-submit-btn ce-submit-btn--sm" :disabled="replySubmitting" @click="handleReplySubmit">
                        <span v-if="replySubmitting" class="ce-btn-spinner"></span>
                        {{ replySubmitting ? '发表中...' : '回复' }}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </li>
          </ul>

          <!-- 查看全部回复按钮 -->
          <div v-if="remainingReplies(entry) > 0" class="show-more-replies">
            <button class="show-more-btn">
              查看全部 {{ remainingReplies(entry) }} 条回复
            </button>
          </div>
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

/* ===== Comment Editor ===== */
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

/* ===== Submit Button ===== */
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

.ce-submit-btn--sm {
  padding: 0.4rem 0.85rem;
  font-size: 0.75rem;
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

.comment-avatar {
  flex-shrink: 0;
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

/* ===== Reply Trigger Button ===== */
.reply-btn-row {
  margin-top: var(--fish-space-sm);
}

.reply-trigger-btn {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: transparent;
  border: none;
  border-radius: 4px;
  color: var(--fish-text-3);
  font-size: 0.75rem;
  font-family: inherit;
  cursor: pointer;
  transition: color 0.2s, background 0.2s;
}

.reply-trigger-btn:hover {
  color: var(--fish-accent);
  background: rgba(124, 123, 242, 0.08);
}

.reply-trigger-btn--sm {
  padding: 2px 6px;
  font-size: 0.7rem;
}

.reply-icon {
  flex-shrink: 0;
}

/* ===== Reply Input ===== */
.reply-input-wrap {
  margin-top: var(--fish-space-md);
}

.reply-input-inner {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: var(--fish-radius-sm);
  padding: var(--fish-space-md);
}

.reply-textarea :deep(.el-textarea__inner) {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 0.8rem;
}

.reply-input-actions {
  margin-top: var(--fish-space-sm);
  display: flex;
  justify-content: flex-end;
  gap: var(--fish-space-sm);
}

/* ===== Reply List (Layer 2) ===== */
.reply-list {
  list-style: none;
  margin: var(--fish-space-sm) 0 0;
  padding: 0;
}

.reply-item {
  display: flex;
  gap: var(--fish-space-sm);
  padding: var(--fish-space-sm) 0;
  margin-bottom: 0;
  background: transparent;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  transition: background 0.2s;
}

.reply-item:last-child {
  margin-bottom: 0;
}

.reply-item:hover {
  background: transparent;
}

.reply-avatar {
  flex-shrink: 0;
}

.reply-body {
  flex: 1;
  min-width: 0;
}

.reply-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.reply-user {
  font-weight: 600;
  font-size: 0.8rem;
  color: var(--fish-text-1);
}

.reply-to-label {
  font-size: 0.75rem;
  color: var(--fish-text-3);
}

.reply-to-user {
  font-size: 0.8rem;
  color: var(--fish-accent);
  font-weight: 500;
}

.reply-content {
  margin: 0;
  font-size: 0.8rem;
  color: var(--fish-text-2);
  line-height: 1.65;
  word-break: break-word;
}

/* ===== Show More Replies ===== */
.show-more-replies {
  margin-top: var(--fish-space-sm);
}

.show-more-btn {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  background: transparent;
  border: 1px solid rgba(124, 123, 242, 0.15);
  border-radius: 4px;
  color: var(--fish-accent);
  font-size: 0.75rem;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}

.show-more-btn:hover {
  background: rgba(124, 123, 242, 0.08);
  border-color: rgba(124, 123, 242, 0.3);
}

/* ===== Edit Mode ===== */
.edit-actions {
  margin-top: var(--fish-space-sm);
  display: flex;
  gap: var(--fish-space-sm);
}

/* ===== Empty State ===== */
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

/* ===== Mobile Responsive ===== */
@media (max-width: 640px) {
  .comment-item {
    gap: var(--fish-space-sm);
  }

  .reply-item {
    gap: 8px;
    padding: var(--fish-space-sm) 0;
  }

  .comment-actions {
    gap: 0;
  }

  .comment-actions :deep(.el-button) {
    padding: 2px 4px;
    font-size: 0.7rem;
  }
}
</style>
