<script setup lang="ts">
import { ElMessage } from 'element-plus'
import type { UploadFile } from 'element-plus'
import { readImageAsBase64 } from '~/utils/file'
import type { ArticlePublish } from '~/types'

/**
 * 文章发布/编辑表单（双栏布局：侧栏设定 + 主编辑器）。
 * - 侧栏：分类、标签、封面
 * - 编辑器：标题 + Markdown 内容（含工具栏与预览）
 * - 支持自动保存草稿
 */
const props = defineProps<{
  mode: 'add' | 'edit'
  initial?: Partial<ArticlePublish> | null
  submitting?: boolean
}>()

const emit = defineEmits<{
  submit: [payload: ArticlePublish]
  cancel: []
}>()

const title = ref(props.initial?.title || '')
const content = ref(props.initial?.content || '')
const tagInput = ref('')
const tagList = ref<string[]>(props.initial?.tag || [])
const categoryList = ref<string[]>(props.initial?.category || [])
const coverBase64 = ref('')
const coverPreview = ref(props.initial?.cover || '')
const imagesBase64 = ref<string[]>(props.initial?.images || [])
const showPreview = ref(false)
const categoryInput = ref('')

const CATEGORY_OPTIONS = [
  '游戏评测',
  '游戏推荐',
  '攻略教程',
  '业界资讯',
  '玩家杂谈',
  '技术分享',
  '其他',
]

// ===== Auto-save draft =====
const DRAFT_KEY = 'article_draft'
const lastSavedTime = ref('')
const isSaving = ref(false)
let saveTimer: ReturnType<typeof setInterval> | null = null

function loadDraft() {
  if (props.mode === 'edit') return
  try {
    const raw = localStorage.getItem(DRAFT_KEY)
    if (!raw) return
    const d = JSON.parse(raw)
    title.value = d.title || ''
    content.value = d.content || ''
    tagList.value = d.tagList || []
    categoryList.value = d.categoryList || []
    lastSavedTime.value = d.savedTime || ''
    if (d.coverPreview) coverPreview.value = d.coverPreview
    categoryInput.value = d.categoryInput || ''
  } catch { /* ignore */ }
}

function saveDraft() {
  if (props.mode === 'edit' || props.submitting) return
  if (!title.value && !content.value) return
  isSaving.value = true
  try {
    const d = {
      title: title.value,
      content: content.value,
      tagList: tagList.value,
      categoryList: categoryList.value,
      coverPreview: coverPreview.value.startsWith('data:') ? coverPreview.value : '',
      categoryInput: categoryInput.value,
      savedTime: new Date().toLocaleString(),
    }
    localStorage.setItem(DRAFT_KEY, JSON.stringify(d))
    lastSavedTime.value = d.savedTime
  } catch { /* ignore */ }
  finally { isSaving.value = false }
}

function clearDraft() {
  localStorage.removeItem(DRAFT_KEY)
  lastSavedTime.value = ''
}

watch([title, content, tagList, categoryList, categoryInput], () => { saveDraft() }, { deep: true })

onMounted(() => {
  loadDraft()
  saveTimer = setInterval(saveDraft, 30000)
})

onUnmounted(() => {
  if (saveTimer) clearInterval(saveTimer)
})

// ===== Tag =====
function addTag() {
  const t = tagInput.value.trim()
  if (!t) return
  if (tagList.value.includes(t)) {
    ElMessage.warning('标签已存在')
    return
  }
  tagList.value.push(t)
  tagInput.value = ''
}

function removeTag(idx: number) {
  tagList.value.splice(idx, 1)
}

// ===== Category =====
function addCategory() {
  const c = categoryInput.value.trim()
  if (!c) return
  if (categoryList.value.includes(c)) {
    ElMessage.warning('分类已存在')
    return
  }
  categoryList.value.push(c)
  categoryInput.value = ''
}

function removeCategory(idx: number) {
  categoryList.value.splice(idx, 1)
}

// ===== Cover =====
async function handleCoverChange(file: File) {
  if (!file) return
  try {
    const b64 = await readImageAsBase64(file)
    coverBase64.value = b64
    coverPreview.value = b64
  } catch {
    ElMessage.error('封面图片读取失败')
  }
}

function removeCover() {
  coverBase64.value = ''
  coverPreview.value = ''
}

// ===== Images =====
async function handleImageFile(file: File) {
  if (!file) return
  try {
    const b64 = await readImageAsBase64(file)
    imagesBase64.value.push(b64)
  } catch {
    ElMessage.error('图片读取失败')
  }
}

function removeImage(idx: number) {
  imagesBase64.value.splice(idx, 1)
}

// ===== Markdown Toolbar =====
const textareaRef = ref<HTMLTextAreaElement | null>(null)

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.max(300, el.scrollHeight) + 'px'
}

function insertMarkdown(prefix: string, suffix: string, placeholder: string) {
  const textarea = textareaRef.value
  if (!textarea || props.submitting) return

  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const selectedText = content.value.substring(start, end)

  const newText =
    content.value.substring(0, start) +
    prefix +
    (selectedText || placeholder) +
    suffix +
    content.value.substring(end)

  content.value = newText

  nextTick(() => {
    textarea.focus()
    const cursorPos = start + prefix.length + (selectedText || placeholder).length + suffix.length
    textarea.setSelectionRange(cursorPos, cursorPos)
    autoResize()
  })
}

// ===== Submit =====
function handleSubmit() {
  if (!title.value.trim()) {
    ElMessage.warning('请输入文章标题')
    return
  }
  if (!content.value.trim()) {
    ElMessage.warning('请输入文章内容')
    return
  }

  const payload: ArticlePublish = {
    title: title.value.trim(),
    content: content.value.trim(),
    category: categoryList.value,
  }

  if (coverBase64.value) payload.cover = coverBase64.value
  else if (coverPreview.value && !coverPreview.value.startsWith('data:')) {
    payload.cover = coverPreview.value
  }
  if (tagList.value.length) payload.tag = tagList.value
  if (imagesBase64.value.length) payload.images = imagesBase64.value

  clearDraft()
  emit('submit', payload)
}

// ===== Markdown rendering =====
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

const md = new MarkdownIt({ html: true, linkify: true, typographer: true })

const renderedContent = computed(() => {
  if (!content.value) return ''
  const html = md.render(content.value)
  return DOMPurify.sanitize(html)
})
</script>

<template>
  <div class="article-form-wrap">
    <div class="ae-layout">
      <!-- ===== Left Sidebar ===== -->
      <aside class="ae-sidebar">
        <div class="ae-sidebar-inner">
          <!-- Header -->
          <div class="ae-sidebar-header">
            <h3 class="ae-sidebar-title">文章设定</h3>
          </div>

          <!-- Category -->
          <div class="ae-section">
            <label class="ae-label">分类 <span class="ae-req">*</span></label>
            <div class="ae-tag-row">
              <input
                v-model="categoryInput"
                type="text"
                class="ae-tag-input"
                placeholder="输入分类后添加"
                @keyup.enter="addCategory"
              />
              <button type="button" class="ae-tag-add" @click="addCategory">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              </button>
            </div>
            <div v-if="categoryList.length" class="ae-tag-list">
              <span v-for="(c, i) in categoryList" :key="i" class="ae-tag-item">
                {{ c }}
                <button type="button" class="ae-tag-remove" @click="removeCategory(i)">
                  <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </span>
            </div>
          </div>

          <!-- Tags -->
          <div class="ae-section">
            <label class="ae-label">标签</label>
            <div class="ae-tag-row">
              <input
                v-model="tagInput"
                type="text"
                class="ae-tag-input"
                placeholder="输入后回车"
                @keyup.enter="addTag"
              />
              <button type="button" class="ae-tag-add" @click="addTag">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              </button>
            </div>
            <div v-if="tagList.length" class="ae-tag-list">
              <span v-for="(t, i) in tagList" :key="i" class="ae-tag-item">
                {{ t }}
                <button type="button" class="ae-tag-remove" @click="removeTag(i)">
                  <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </span>
            </div>
          </div>

          <!-- Cover -->
          <div class="ae-section">
            <label class="ae-label">封面图</label>
            <div class="ae-cover-zone">
              <div v-if="coverPreview" class="ae-cover-preview">
                <el-image :src="coverPreview" fit="cover" class="ae-cover-img" />
                <div class="ae-cover-overlay">
                  <el-upload
                    accept="image/*"
                    :show-file-list="false"
                    :auto-upload="false"
                    :before-upload="(file: File) => { handleCoverChange(file); return false }"
                  >
                    <button type="button" class="ae-cover-replace-btn">更换</button>
                  </el-upload>
                  <button type="button" class="ae-cover-remove-btn" @click="removeCover">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </button>
                </div>
              </div>
              <div v-else class="ae-cover-empty">
                <el-upload
                  accept="image/*"
                  :show-file-list="false"
                  :auto-upload="false"
                  :before-upload="(file: File) => { handleCoverChange(file); return false }"
                  class="ae-cover-upload-btn"
                >
                  <div class="ae-cover-placeholder">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                    <span>上传封面</span>
                  </div>
                </el-upload>
              </div>
            </div>
            <p class="ae-hint">建议 16:9 横幅封面</p>
          </div>

          <!-- Spacer -->
          <div class="ae-spacer"></div>

          <!-- Submit -->
          <div class="ae-publish-area">
            <button type="button" class="ae-publish-btn" :disabled="submitting" @click="handleSubmit">
              <span v-if="submitting" class="ae-btn-spinner"></span>
              <svg v-else class="ae-btn-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>
              </svg>
              {{ submitting ? '发布中...' : mode === 'add' ? '发布文章' : '保存修改' }}
            </button>
          </div>

          <!-- Auto-save -->
          <div class="ae-auto-save">
            <span v-if="isSaving" class="ae-as-saving">
              <span class="ae-as-spinner"></span> 保存中...
            </span>
            <span v-else-if="lastSavedTime" class="ae-as-saved">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>
              草稿已保存
            </span>
            <span v-else class="ae-as-idle">草稿自动保存</span>
          </div>
        </div>
      </aside>

      <!-- ===== Main Editor ===== -->
      <main class="ae-editor">
        <div class="ae-editor-inner">
          <!-- Title -->
          <div class="ae-title-field">
            <input
              v-model="title"
              type="text"
              class="ae-title-input"
              placeholder="输入文章标题..."
              :disabled="submitting"
            />
            <div class="ae-title-underline"></div>
          </div>

          <!-- Divider -->
          <div class="ae-divider"></div>

          <!-- Markdown Toolbar -->
          <div class="ae-md-toolbar">
            <button type="button" @click="insertMarkdown('**', '**', '加粗文本')" :disabled="submitting" class="ae-md-btn" title="加粗"><strong>B</strong></button>
            <button type="button" @click="insertMarkdown('*', '*', '斜体文本')" :disabled="submitting" class="ae-md-btn" title="斜体"><em>I</em></button>
            <button type="button" @click="insertMarkdown('~~', '~~', '删除线')" :disabled="submitting" class="ae-md-btn" title="删除线"><del>S</del></button>
            <span class="ae-md-sep"></span>
            <button type="button" @click="insertMarkdown('# ', '', '一级标题')" :disabled="submitting" class="ae-md-btn" title="标题 1">H1</button>
            <button type="button" @click="insertMarkdown('## ', '', '二级标题')" :disabled="submitting" class="ae-md-btn" title="标题 2">H2</button>
            <button type="button" @click="insertMarkdown('### ', '', '三级标题')" :disabled="submitting" class="ae-md-btn" title="标题 3">H3</button>
            <span class="ae-md-sep"></span>
            <button type="button" @click="insertMarkdown('- ', '', '无序列表')" :disabled="submitting" class="ae-md-btn" title="无序列表">&bull;</button>
            <button type="button" @click="insertMarkdown('1. ', '', '有序列表')" :disabled="submitting" class="ae-md-btn" title="有序列表">1.</button>
            <span class="ae-md-sep"></span>
            <button type="button" @click="insertMarkdown('```\n', '\n```', '代码块')" :disabled="submitting" class="ae-md-btn" title="代码块">&lt;/&gt;</button>
            <button type="button" @click="insertMarkdown('`', '`', '行内代码')" :disabled="submitting" class="ae-md-btn" title="行内代码"><code>`</code></button>
            <span class="ae-md-sep"></span>
            <button
              type="button"
              @click="showPreview = !showPreview"
              :disabled="submitting"
              :class="['ae-md-preview-btn', { active: showPreview }]"
            >
              <svg v-if="showPreview" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
              </svg>
              <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                <circle cx="12" cy="12" r="3"/>
              </svg>
              {{ showPreview ? '编辑' : '预览' }}
            </button>
          </div>

          <!-- Content Area -->
          <div class="ae-content-area">
            <textarea
              v-if="!showPreview"
              ref="textareaRef"
              v-model="content"
              class="ae-content-textarea"
              placeholder="在这里开始写作… 支持 Markdown 格式"
              :disabled="submitting"
              @input="autoResize"
            ></textarea>
            <div v-else class="ae-preview-content" v-html="renderedContent"></div>
          </div>

          <!-- Image Strip -->
          <div v-if="imagesBase64.length" class="ae-image-strip">
            <div class="ae-image-strip-label">插图 ({{ imagesBase64.length }})</div>
            <div class="ae-image-strip-grid">
              <div v-for="(img, idx) in imagesBase64" :key="idx" class="ae-image-item">
                <el-image :src="img" fit="cover" class="ae-image-thumb" />
                <button type="button" class="ae-image-remove" @click="removeImage(idx)" :disabled="submitting">
                  <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </div>
              <el-upload
                accept="image/*"
                :show-file-list="false"
                :auto-upload="false"
                :before-upload="(file: File) => { handleImageFile(file); return false }"
              >
                <button type="button" class="ae-image-add-btn">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                </button>
              </el-upload>
            </div>
          </div>

          <!-- Image Add Button (when strip empty) -->
          <div v-else class="ae-image-add-row">
            <el-upload
              accept="image/*"
              multiple
              :show-file-list="false"
              :auto-upload="false"
              :before-upload="(file: File) => { handleImageFile(file); return false }"
            >
              <button type="button" class="ae-image-add-row-btn" :disabled="submitting">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                  <circle cx="8.5" cy="8.5" r="1.5"/>
                  <polyline points="21 15 16 10 5 21"/>
                </svg>
                <span>添加插图</span>
              </button>
            </el-upload>
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<style scoped>
/* ============================================
   Main Layout
   ============================================ */
.article-form-wrap {
  width: 100%;
}

.ae-layout {
  display: flex;
  gap: 0;
  background: rgba(24, 24, 31, 0.75);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.06);
  box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.4);
  overflow: hidden;
}

/* ============================================
   Sidebar
   ============================================ */
.ae-sidebar {
  width: 220px;
  flex-shrink: 0;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 2rem;
  align-self: flex-start;
  max-height: calc(100vh - 6rem);
  overflow-y: auto;
}

.ae-sidebar-inner {
  padding: 1.5rem 1.25rem;
  display: flex;
  flex-direction: column;
  min-height: 100%;
}

.ae-sidebar-header {
  margin-bottom: 0.75rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.ae-sidebar-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--fish-text-3);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin: 0;
}

.ae-section {
  margin-bottom: 1.25rem;
}

.ae-label {
  display: block;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--fish-text-2);
  margin-bottom: 0.4rem;
  letter-spacing: 0.02em;
}

.ae-req {
  color: var(--el-color-danger);
}

.ae-hint {
  margin: 0.35rem 0 0;
  font-size: 0.65rem;
  color: var(--fish-text-3);
  line-height: 1.4;
}

/* ===== Category ===== */
/* ===== Tags ===== */
.ae-tag-row {
  display: flex;
  gap: 0.35rem;
  width: 100%;
}

.ae-tag-input {
  flex: 1;
  min-width: 0;
  padding: 0.4rem 0.55rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.4rem;
  font-size: 0.75rem;
  background: rgba(255, 255, 255, 0.03);
  color: var(--fish-text-1);
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}

.ae-tag-input::placeholder {
  color: var(--fish-text-3);
  font-size: 0.68rem;
}

.ae-tag-input:focus {
  border-color: rgba(124, 123, 242, 0.35);
}

.ae-tag-add {
  width: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 0.4rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  color: var(--fish-text-3);
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s, background 0.2s;
  padding: 0;
}

.ae-tag-add:hover {
  color: var(--fish-accent);
  border-color: rgba(124, 123, 242, 0.25);
  background: rgba(124, 123, 242, 0.06);
}

.ae-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-top: 0.35rem;
}

.ae-tag-item {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  padding: 0.2rem 0.45rem;
  border-radius: 0.3rem;
  background: rgba(124, 123, 242, 0.08);
  border: 1px solid rgba(124, 123, 242, 0.12);
  color: var(--fish-accent);
  font-size: 0.65rem;
  font-weight: 500;
  line-height: 1.3;
}

.ae-tag-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  background: none;
  border: none;
  color: inherit;
  opacity: 0.5;
  cursor: pointer;
}

.ae-tag-remove:hover {
  opacity: 1;
}

/* ===== Cover ===== */
.ae-cover-zone {
  width: 100%;
}

.ae-cover-preview {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 0.5rem;
  overflow: hidden;
  background: var(--fish-bg);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.ae-cover-img {
  width: 100%;
  height: 100%;
  display: block;
}

.ae-cover-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.5);
  opacity: 0;
  transition: opacity 0.2s;
}

.ae-cover-preview:hover .ae-cover-overlay {
  opacity: 1;
}

.ae-cover-replace-btn {
  padding: 0.3rem 0.7rem;
  border-radius: 0.35rem;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  font-size: 0.7rem;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.2s;
}

.ae-cover-replace-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.ae-cover-remove-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: rgba(225, 29, 72, 0.65);
  color: #fff;
  border: none;
  cursor: pointer;
  transition: background 0.2s;
  padding: 0;
}

.ae-cover-remove-btn:hover {
  background: #E11D48;
}

.ae-cover-empty {
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 0.5rem;
  border: 1px dashed rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.ae-cover-empty:hover {
  border-color: rgba(124, 123, 242, 0.25);
  background: rgba(124, 123, 242, 0.03);
}

.ae-cover-upload-btn :deep(.el-upload) {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ae-cover-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  color: var(--fish-text-3);
  font-size: 0.7rem;
}

/* ===== Spacer ===== */
.ae-spacer {
  flex: 1;
  min-height: 0.75rem;
}

/* ===== Publish Button ===== */
.ae-publish-area {
  margin-bottom: 0.5rem;
}

.ae-publish-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.65rem 1rem;
  background: var(--fish-accent);
  border: none;
  border-radius: 0.5rem;
  color: #fff;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  letter-spacing: 0.01em;
  transition: background 0.2s, transform 0.2s, box-shadow 0.2s;
  line-height: 1;
}

.ae-publish-btn:hover:not(:disabled) {
  background: #8F8EF5;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(124, 123, 242, 0.25);
}

.ae-publish-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.ae-publish-btn:disabled {
  background: rgba(124, 123, 242, 0.35);
  color: rgba(255, 255, 255, 0.5);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.ae-btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: #fff;
  border-radius: 50%;
  animation: ae-spin 0.7s linear infinite;
  flex-shrink: 0;
}

.ae-btn-icon {
  flex-shrink: 0;
}

@keyframes ae-spin {
  to { transform: rotate(360deg); }
}

/* ===== Auto Save ===== */
.ae-auto-save {
  padding-top: 0.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  display: flex;
  align-items: center;
}

.ae-as-saving {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.65rem;
  color: var(--fish-accent);
  font-weight: 500;
}

.ae-as-spinner {
  width: 8px;
  height: 8px;
  border: 1.5px solid rgba(124, 123, 242, 0.2);
  border-top-color: var(--fish-accent);
  border-radius: 50%;
  animation: ae-spin 0.8s linear infinite;
  flex-shrink: 0;
}

.ae-as-saved {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.65rem;
  color: var(--el-color-success);
  font-weight: 500;
}

.ae-as-idle {
  font-size: 0.65rem;
  color: var(--fish-text-3);
  font-weight: 400;
}

/* ============================================
   Main Editor
   ============================================ */
.ae-editor {
  flex: 1;
  min-width: 0;
}

.ae-editor-inner {
  padding: 1.75rem 2rem 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

/* ===== Title ===== */
.ae-title-field {
  position: relative;
}

.ae-title-input {
  width: 100%;
  padding: 0.25rem 0;
  border: none;
  background: transparent;
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--fish-text-1);
  letter-spacing: -0.03em;
  line-height: 1.3;
  font-family: inherit;
  outline: none;
  transition: color 0.2s;
}

.ae-title-input::placeholder {
  color: rgba(255, 255, 255, 0.12);
  font-weight: 600;
}

.ae-title-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ae-title-underline {
  height: 2px;
  background: linear-gradient(to right, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.03));
  border-radius: 1px;
  transition: background 0.3s;
  margin-top: 0.25rem;
}

.ae-title-input:focus ~ .ae-title-underline,
.ae-title-input:not(:placeholder-shown) ~ .ae-title-underline {
  background: linear-gradient(to right, var(--fish-accent), rgba(124, 123, 242, 0.25));
}

/* ===== Divider ===== */
.ae-divider {
  height: 1px;
  background: linear-gradient(to right, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.03), transparent);
  margin-bottom: 0.25rem;
}

/* ===== Markdown Toolbar ===== */
.ae-md-toolbar {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.15rem;
  padding: 0.4rem 0.5rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 0.5rem;
  transition: border-color 0.2s;
}

.ae-md-toolbar:focus-within {
  border-color: rgba(124, 123, 242, 0.2);
}

.ae-md-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.3rem 0.45rem;
  border: 1px solid transparent;
  border-radius: 0.35rem;
  background: transparent;
  color: var(--fish-text-3);
  font-size: 0.72rem;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  line-height: 1;
  transition: color 0.2s, background 0.2s, border-color 0.2s;
  min-width: 26px;
}

.ae-md-btn:hover:not(:disabled) {
  background: rgba(124, 123, 242, 0.08);
  border-color: rgba(124, 123, 242, 0.12);
  color: var(--fish-accent);
}

.ae-md-btn:active:not(:disabled) {
  transform: scale(0.94);
}

.ae-md-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.ae-md-btn strong { font-weight: 700; }
.ae-md-btn em { font-style: italic; }
.ae-md-btn del { text-decoration: line-through; }

.ae-md-sep {
  width: 1px;
  height: 16px;
  background: rgba(255, 255, 255, 0.06);
  margin: 0 0.15rem;
  flex-shrink: 0;
}

.ae-md-preview-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.3rem 0.6rem;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 0.35rem;
  background: rgba(255, 255, 255, 0.02);
  color: var(--fish-text-3);
  font-size: 0.7rem;
  font-weight: 500;
  cursor: pointer;
  font-family: inherit;
  line-height: 1;
  transition: color 0.2s, background 0.2s, border-color 0.2s;
  margin-left: auto;
}

.ae-md-preview-btn:hover:not(:disabled) {
  background: rgba(124, 123, 242, 0.06);
  border-color: rgba(124, 123, 242, 0.15);
  color: var(--fish-accent);
}

.ae-md-preview-btn.active {
  background: rgba(124, 123, 242, 0.1);
  border-color: var(--fish-accent);
  color: var(--fish-accent);
}

.ae-md-preview-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ===== Content Area ===== */
.ae-content-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 300px;
}

.ae-content-textarea {
  flex: 1;
  width: 100%;
  min-height: 300px;
  padding: 0.75rem 0;
  border: none;
  background: transparent;
  font-size: 0.95rem;
  line-height: 1.8;
  color: var(--fish-text-1);
  font-family: inherit;
  resize: none;
  outline: none;
}

.ae-content-textarea::placeholder {
  color: rgba(255, 255, 255, 0.1);
}

.ae-content-textarea:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.ae-preview-content {
  flex: 1;
  min-height: 300px;
  padding: 0.75rem 0;
  color: var(--fish-text-1);
  line-height: 1.8;
  word-wrap: break-word;
  overflow-x: auto;
}

.ae-preview-content h1 {
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: -0.03em;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  color: var(--fish-text-1);
}

.ae-preview-content h2 {
  font-size: 1.35rem;
  font-weight: 650;
  letter-spacing: -0.02em;
  margin-top: 2rem;
  margin-bottom: 0.75rem;
  color: var(--fish-text-1);
}

.ae-preview-content h3 {
  font-size: 1.15rem;
  font-weight: 600;
  margin-top: 1.5rem;
  margin-bottom: 0.5rem;
  color: var(--fish-text-2);
}

.ae-preview-content p {
  margin-bottom: 1rem;
  line-height: 1.8;
}

.ae-preview-content strong {
  font-weight: 650;
}

.ae-preview-content em {
  font-style: italic;
}

.ae-preview-content ul,
.ae-preview-content ol {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

.ae-preview-content li {
  margin-bottom: 0.35rem;
  line-height: 1.7;
}

.ae-preview-content code {
  padding: 0.15em 0.35em;
  background: rgba(124, 123, 242, 0.1);
  border-radius: 0.25rem;
  font-size: 0.85em;
  color: var(--fish-accent);
}

.ae-preview-content pre {
  padding: 1rem 1.25rem;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 0.5rem;
  overflow-x: auto;
  margin-bottom: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.04);
}

.ae-preview-content pre code {
  background: transparent;
  padding: 0;
  color: var(--fish-text-2);
}

.ae-preview-content a {
  color: var(--fish-accent);
  text-decoration: none;
}

.ae-preview-content a:hover {
  opacity: 0.8;
}

.ae-preview-content blockquote {
  border-left: 2px solid var(--fish-accent);
  padding: 0.5rem 1rem;
  margin: 1rem 0;
  color: var(--fish-text-2);
  background: rgba(124, 123, 242, 0.03);
  border-radius: 0 0.35rem 0.35rem 0;
}

.ae-preview-content hr {
  border: none;
  height: 1px;
  background: linear-gradient(to right, transparent, rgba(255, 255, 255, 0.06), transparent);
  margin: 2rem 0;
}

/* ===== Image Strip ===== */
.ae-image-strip {
  margin-top: 0.5rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}

.ae-image-strip-label {
  font-size: 0.7rem;
  font-weight: 600;
  color: var(--fish-text-3);
  margin-bottom: 0.5rem;
  letter-spacing: 0.03em;
}

.ae-image-strip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.ae-image-item {
  position: relative;
  width: 68px;
  height: 68px;
  border-radius: 0.4rem;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
  background: var(--fish-bg);
}

.ae-image-thumb {
  width: 100%;
  height: 100%;
  display: block;
}

.ae-image-remove {
  position: absolute;
  top: 2px;
  right: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.55);
  color: #fff;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s;
  cursor: pointer;
  padding: 0;
}

.ae-image-item:hover .ae-image-remove {
  opacity: 1;
}

.ae-image-remove:hover {
  background: #E11D48;
}

.ae-image-remove:disabled {
  opacity: 0;
}

.ae-image-add-btn {
  width: 68px;
  height: 68px;
  border-radius: 0.4rem;
  border: 1px dashed rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
  color: var(--fish-text-3);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
  padding: 0;
}

.ae-image-add-btn:hover {
  border-color: var(--fish-accent-border);
  color: var(--fish-accent);
}

/* ===== Image Add Row (when empty) ===== */
.ae-image-add-row {
  margin-top: 0.5rem;
}

.ae-image-add-row-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.85rem;
  border: 1px dashed rgba(255, 255, 255, 0.1);
  border-radius: 0.4rem;
  background: rgba(255, 255, 255, 0.02);
  color: var(--fish-text-3);
  font-size: 0.75rem;
  font-family: inherit;
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
}

.ae-image-add-row-btn:hover:not(:disabled) {
  border-color: rgba(124, 123, 242, 0.2);
  color: var(--fish-accent);
}

.ae-image-add-row-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* ============================================
   Responsive
   ============================================ */
@media (max-width: 960px) {
  .ae-layout {
    flex-direction: column;
  }

  .ae-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    position: static;
    max-height: none;
    overflow: visible;
  }

  .ae-sidebar-inner {
    padding: 1.25rem;
    min-height: auto;
  }

  .ae-spacer {
    display: none;
  }

  .ae-editor-inner {
    padding: 1.25rem;
  }

  .ae-title-input {
    font-size: 1.4rem;
  }
}

@media (max-width: 600px) {
  .ae-editor-inner {
    padding: 1rem;
  }

  .ae-title-input {
    font-size: 1.2rem;
  }

  .ae-md-toolbar {
    gap: 0.1rem;
    padding: 0.3rem 0.4rem;
  }

  .ae-md-btn {
    padding: 0.25rem 0.35rem;
    font-size: 0.68rem;
    min-width: 22px;
  }

  .ae-image-item {
    width: 56px;
    height: 56px;
  }

  .ae-image-add-btn {
    width: 56px;
    height: 56px;
  }
}
</style>