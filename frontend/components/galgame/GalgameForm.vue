<script setup lang="ts">
import { ElMessage } from 'element-plus'
import type { UploadFile, UploadUserFile } from 'element-plus'
import { readImageAsBase64 } from '~/utils/file'
import {
  PLATFORM_OPTIONS,
  CATEGORY_OPTIONS,
  type PlatformValue,
  type CategoryValue,
  type GalgameDetail,
  type AddGal,
  type EditGal,
} from '~/types'

/**
 * 游戏发布/编辑表单（双栏布局：侧栏设定 + 主编辑器）。
 * - mode="add"：完整校验（至少一个名称 + 封面必填），提交 AddGal。
 * - mode="edit"：预填已发布字段；仅上传了新封面/新截图时才提交 cover/images。
 * - 布局仿照 blog 发布页：左 220px 侧栏（封面/设定）+ 右 1fr 编辑器（名称 + 简介）。
 */
const props = defineProps<{
  mode: 'add' | 'edit'
  initial?: GalgameDetail | null
  submitting?: boolean
}>()

const emit = defineEmits<{
  submit: [payload: AddGal | EditGal]
  cancel: []
}>()

// ===== 封面 & 截图 =====
const coverBase64 = ref('')
const coverPreview = ref('')
const imageFileList = ref<UploadUserFile[]>([])
const imageBase64Map = new Map<string, string>()
const imagesBase64 = computed(() =>
  imageFileList.value
    .map((f: UploadUserFile) => (f.uid != null ? imageBase64Map.get(String(f.uid)) : undefined))
    .filter((b: string | undefined): b is string => !!b),
)

// ===== 表单数据 =====
const form = reactive({
  cn_name: '',
  jp_name: '',
  en_name: '',
  content: '',
  company: [] as string[],
  category: '' as CategoryValue | '',
  tag: [] as string[],
  platfrom: [] as PlatformValue[],
})

// 编辑模式预填
if (props.mode === 'edit' && props.initial) {
  const initial = props.initial
  form.cn_name = initial.cn_name || ''
  form.jp_name = initial.jp_name || ''
  form.en_name = initial.en_name || ''
  form.content = initial.content || ''
  form.company = initial.company || []
  form.category = CATEGORY_OPTIONS.some((c) => c.value === initial.category)
    ? (initial.category as CategoryValue)
    : ''
  form.tag = initial.tag || []
  form.platfrom = (initial.platfrom || []) as PlatformValue[]
  coverPreview.value = initial.cover || ''
}

// ===== Auto-save draft =====
const DRAFT_KEY = 'galgame_draft'
const lastSavedTime = ref('')
const isSaving = ref(false)
let saveTimer: ReturnType<typeof setInterval> | null = null

function loadDraft() {
  if (props.mode === 'edit') return
  try {
    const raw = localStorage.getItem(DRAFT_KEY)
    if (!raw) return
    const d = JSON.parse(raw)
    form.cn_name = d.cn_name || ''
    form.jp_name = d.jp_name || ''
    form.en_name = d.en_name || ''
    form.content = d.content || ''
    form.company = d.company || []
    form.category = d.category || ''
    form.tag = d.tag || []
    form.platfrom = d.platfrom || []
    lastSavedTime.value = d.savedTime || ''
    if (d.coverPreview) coverPreview.value = d.coverPreview
  } catch { /* ignore */ }
}

function saveDraft() {
  if (props.mode === 'edit' || props.submitting) return
  if (!form.cn_name && !form.jp_name && !form.en_name && !form.content) return
  isSaving.value = true
  try {
    const d = {
      cn_name: form.cn_name,
      jp_name: form.jp_name,
      en_name: form.en_name,
      content: form.content,
      company: form.company,
      category: form.category,
      tag: form.tag,
      platfrom: form.platfrom,
      coverPreview: coverPreview.value.startsWith('data:') ? coverPreview.value : '',
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

watch([() => form.cn_name, () => form.jp_name, () => form.en_name, () => form.content, () => form.company, () => form.category, () => form.tag, () => form.platfrom, coverPreview], () => {
  saveDraft()
}, { deep: true })

onMounted(() => {
  loadDraft()
  saveTimer = setInterval(saveDraft, 30000)
})

onUnmounted(() => {
  if (saveTimer) clearInterval(saveTimer)
})

// ===== 交互函数 =====
function togglePlatform(value: PlatformValue) {
  const i = form.platfrom.indexOf(value)
  if (i >= 0) form.platfrom.splice(i, 1)
  else form.platfrom.push(value)
}

async function onCoverChange(uploadFile: UploadFile) {
  const raw = uploadFile.raw
  if (!raw) return
  try {
    const b64 = await readImageAsBase64(raw)
    coverBase64.value = b64
    coverPreview.value = b64
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '图片读取失败')
  }
}

function onCoverRemove() {
  coverBase64.value = ''
  coverPreview.value = props.mode === 'edit' && props.initial ? props.initial.cover || '' : ''
}

async function onImagesChange(uploadFile: UploadFile) {
  const raw = uploadFile.raw
  if (!raw) return
  try {
    const b64 = await readImageAsBase64(raw)
    imageBase64Map.set(String(uploadFile.uid), b64)
  } catch (err) {
    imageFileList.value = imageFileList.value.filter((f: UploadUserFile) => f.uid !== uploadFile.uid)
    ElMessage.error(err instanceof Error ? err.message : '图片读取失败')
  }
}

function onImagesRemove(uploadFile: UploadFile) {
  imageBase64Map.delete(String(uploadFile.uid))
}

// ===== 标签输入 =====
const tagInput = ref('')

function addTag() {
  const t = tagInput.value.trim()
  if (!t) return
  if (form.tag.includes(t)) {
    ElMessage.warning('标签已存在')
    return
  }
  form.tag.push(t)
  tagInput.value = ''
}

function removeTag(idx: number) {
  form.tag.splice(idx, 1)
}

// ===== 发行商输入 =====
const companyInput = ref('')

function addCompany() {
  const c = companyInput.value.trim()
  if (!c) return
  if (form.company.includes(c)) {
    ElMessage.warning('已存在')
    return
  }
  form.company.push(c)
  companyInput.value = ''
}

function removeCompany(idx: number) {
  form.company.splice(idx, 1)
}

// ===== 预览数据 =====
const previewName = computed(() => form.cn_name || form.jp_name || form.en_name || '未命名游戏')
const previewSubNames = computed(() => {
  const main = previewName.value
  const set = new Set<string>()
  for (const n of [form.cn_name, form.jp_name, form.en_name]) {
    if (n && n !== main) set.add(n)
  }
  return [...set]
})

const previewTags = computed(() => {
  const tags: string[] = []
  if (form.category) tags.push(form.category)
  tags.push(...form.platfrom)
  tags.push(...form.tag)
  return tags.slice(0, 5)
})

// ===== 校验与提交 =====
function validate(): boolean {
  if (props.mode === 'add' && !form.cn_name && !form.jp_name && !form.en_name) {
    ElMessage.warning('中文名 / 日文名 / 英文名至少填写一个')
    return false
  }
  if (props.mode === 'add' && !coverBase64.value && !coverPreview.value) {
    ElMessage.warning('请上传封面图')
    return false
  }
  return true
}

function buildPayload(): AddGal | EditGal {
  const base = {
    cn_name: form.cn_name || null,
    jp_name: form.jp_name || null,
    en_name: form.en_name || null,
    content: form.content || null,
    company: form.company.length ? form.company : null,
    category: form.category || null,
    tag: form.tag.length ? form.tag : null,
    platfrom: form.platfrom.length ? form.platfrom : null,
  }

  if (props.mode === 'add') {
    const payload: AddGal = {
      ...base,
      cover: coverBase64.value || coverPreview.value,
      images: imagesBase64.value.length ? imagesBase64.value : null,
    }
    return payload
  }

  const payload: EditGal = { ...base }
  if (coverBase64.value) payload.cover = coverBase64.value
  if (imagesBase64.value.length) payload.images = imagesBase64.value
  return payload
}

function handleSubmit() {
  if (!validate()) return
  clearDraft()
  emit('submit', buildPayload())
}
</script>

<template>
  <div class="gal-form-wrap">
    <div class="ge-layout">
      <!-- ===== Left Sidebar ===== -->
      <aside class="ge-sidebar">
        <div class="ge-sidebar-inner">
          <!-- Header -->
          <div class="ge-sidebar-header">
            <h3 class="ge-sidebar-title">游戏信息</h3>
          </div>

          <!-- Cover Upload -->
          <div class="ge-section">
            <label class="ge-label">封面图 <span v-if="mode === 'add'" class="ge-req">*</span></label>
            <div class="ge-cover-zone">
              <div v-if="coverPreview" class="ge-cover-preview" @click="() => {}">
                <el-image :src="coverPreview" fit="cover" class="ge-cover-img" />
                <div class="ge-cover-overlay">
                  <el-upload
                    :show-file-list="false"
                    :auto-upload="false"
                    accept="image/*"
                    :on-change="onCoverChange"
                    class="ge-cover-replace"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
                    <span>更换</span>
                  </el-upload>
                  <button type="button" class="ge-cover-remove" @click="onCoverRemove" title="移除封面">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  </button>
                </div>
              </div>
              <div v-else class="ge-cover-empty" @click="() => {}">
                <el-upload
                  :show-file-list="false"
                  :auto-upload="false"
                  accept="image/*"
                  :on-change="onCoverChange"
                  class="ge-cover-upload-btn"
                >
                  <div class="ge-cover-placeholder">
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                    <span>上传 2:3 封面</span>
                  </div>
                </el-upload>
              </div>
            </div>
            <p class="ge-hint">竖版封面，建议 2:3 比例</p>
          </div>

          <!-- Category -->
          <div class="ge-section">
            <label class="ge-label">作品类型</label>
            <el-select
              v-model="form.category"
              placeholder="选择作品类型"
              class="ge-select"
              clearable
            >
              <el-option
                v-for="opt in CATEGORY_OPTIONS"
                :key="opt.value"
                :label="opt.label"
                :value="opt.value"
              />
            </el-select>
          </div>

          <!-- Platform Chips -->
          <div class="ge-section">
            <label class="ge-label">支持平台</label>
            <div class="ge-chips">
              <button
                v-for="p in PLATFORM_OPTIONS"
                :key="p.value"
                type="button"
                class="ge-chip"
                :class="{ active: form.platfrom.includes(p.value) }"
                @click="togglePlatform(p.value)"
              >
                {{ p.label }}
              </button>
            </div>
          </div>

          <!-- Tags -->
          <div class="ge-section">
            <label class="ge-label">标签</label>
            <div class="ge-tag-row">
              <input
                v-model="tagInput"
                type="text"
                class="ge-tag-input"
                placeholder="输入后回车添加"
                @keyup.enter="addTag"
              />
              <button type="button" class="ge-tag-add-btn" @click="addTag">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              </button>
            </div>
            <div v-if="form.tag.length" class="ge-tag-list">
              <span v-for="(t, i) in form.tag" :key="i" class="ge-tag-item">
                {{ t }}
                <button type="button" class="ge-tag-remove" @click="removeTag(i)">
                  <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </span>
            </div>
          </div>

          <!-- Company -->
          <div class="ge-section">
            <label class="ge-label">制作公司</label>
            <div class="ge-tag-row">
              <input
                v-model="companyInput"
                type="text"
                class="ge-tag-input"
                placeholder="输入公司名"
                @keyup.enter="addCompany"
              />
              <button type="button" class="ge-tag-add-btn" @click="addCompany">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              </button>
            </div>
            <div v-if="form.company.length" class="ge-tag-list">
              <span v-for="(c, i) in form.company" :key="i" class="ge-tag-item">
                {{ c }}
                <button type="button" class="ge-tag-remove" @click="removeCompany(i)">
                  <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </span>
            </div>
          </div>

          <!-- Screenshots -->
          <div class="ge-section">
            <label class="ge-label">游戏截图</label>
            <div class="ge-screenshots-thumbs">
              <div
                v-for="(img, idx) in imagesBase64"
                :key="idx"
                class="ge-screenshot-thumb"
              >
                <el-image :src="img" fit="cover" />
                <button type="button" class="ge-scr-remove" @click="imageFileList.splice(idx, 1); imageBase64Map.delete(String(imageFileList[idx]?.uid))">
                  <svg width="8" height="8" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </button>
              </div>
              <el-upload
                :show-file-list="false"
                :auto-upload="false"
                accept="image/*"
                multiple
                :on-change="onImagesChange"
                class="ge-scr-add-upload"
              >
                <button type="button" class="ge-scr-add-btn">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                </button>
              </el-upload>
            </div>
          </div>

          <!-- Spacer -->
          <div class="ge-spacer"></div>

          <!-- Publish Button -->
          <div class="ge-publish-area">
            <button type="button" class="ge-publish-btn" :disabled="submitting" @click="handleSubmit">
              <span v-if="submitting" class="ge-btn-spinner"></span>
              <svg v-else class="ge-btn-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/>
              </svg>
              {{ submitting ? '发布中...' : mode === 'add' ? '发布游戏' : '保存修改' }}
            </button>
          </div>

          <!-- Auto-save -->
          <div class="ge-auto-save">
            <span v-if="isSaving" class="ge-as-saving">
              <span class="ge-as-spinner"></span> 保存中...
            </span>
            <span v-else-if="lastSavedTime" class="ge-as-saved">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><polyline points="20 6 9 17 4 12"/></svg>
              草稿已保存
            </span>
            <span v-else class="ge-as-idle">草稿自动保存</span>
          </div>
        </div>
      </aside>

      <!-- ===== Main Editor ===== -->
      <main class="ge-editor">
        <div class="ge-editor-inner">
          <!-- Three Name Inputs -->
          <div class="ge-name-grid">
            <div class="ge-name-field">
              <label class="ge-name-label">中文名 <span class="ge-label-desc">（选填）</span></label>
              <input
                v-model="form.cn_name"
                type="text"
                class="ge-name-input"
                placeholder="简体中文名"
                maxlength="50"
              />
              <div class="ge-name-underline"></div>
            </div>
            <div class="ge-name-field">
              <label class="ge-name-label">日文名 <span class="ge-label-desc">（选填）</span></label>
              <input
                v-model="form.jp_name"
                type="text"
                class="ge-name-input"
                placeholder="日文原名"
                maxlength="50"
              />
              <div class="ge-name-underline"></div>
            </div>
            <div class="ge-name-field">
              <label class="ge-name-label">英文名 <span class="ge-label-desc">（选填）</span></label>
              <input
                v-model="form.en_name"
                type="text"
                class="ge-name-input"
                placeholder="英文名"
                maxlength="50"
              />
              <div class="ge-name-underline"></div>
            </div>
          </div>

          <!-- Divider -->
          <div class="ge-divider"></div>

          <!-- Description -->
          <div class="ge-desc-section">
            <label class="ge-name-label">游戏简介</label>
            <p class="ge-desc-hint">介绍剧情、玩法与特色</p>
            <textarea
              v-model="form.content"
              class="ge-desc-textarea"
              placeholder="在这里描述游戏内容……"
              rows="12"
            ></textarea>
          </div>

          <!-- Card Preview (bottom of editor) -->
          <div class="ge-preview-section">
            <div class="ge-preview-header">
              <span class="ge-preview-label">卡片预览</span>
              <span class="ge-preview-note">发布后首页卡片效果</span>
            </div>
            <div class="ge-preview-card">
              <div class="ge-preview-cover">
                <el-image v-if="coverPreview" :src="coverPreview" fit="cover" class="ge-pc-img" />
                <div v-else class="ge-pc-ph">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
                  <span>封面</span>
                </div>
                <span class="ge-pc-badge">新发布</span>
              </div>
              <div class="ge-pc-info">
                <div class="ge-pc-name" :title="previewName">{{ previewName }}</div>
                <div v-if="previewSubNames.length" class="ge-pc-subnames">
                  <span v-for="n in previewSubNames" :key="n">{{ n }}</span>
                </div>
                <div v-if="previewTags.length" class="ge-pc-tags">
                  <span v-for="t in previewTags" :key="t" class="ge-pc-tag">{{ t }}</span>
                </div>
              </div>
            </div>
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
.gal-form-wrap {
  width: 100%;
}

.ge-layout {
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
.ge-sidebar {
  width: 230px;
  flex-shrink: 0;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(0, 0, 0, 0.08);
  position: sticky;
  top: 2rem;
  align-self: flex-start;
  max-height: calc(100vh - 6rem);
  overflow-y: auto;
}

.ge-sidebar-inner {
  padding: 1.5rem 1.25rem;
  display: flex;
  flex-direction: column;
  min-height: 100%;
  gap: 0.125rem;
}

.ge-sidebar-header {
  margin-bottom: 0.75rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.ge-sidebar-title {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--fish-text-3);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  margin: 0;
}

.ge-section {
  margin-bottom: 1rem;
}

.ge-label {
  display: block;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--fish-text-2);
  margin-bottom: 0.4rem;
  letter-spacing: 0.02em;
}

.ge-req {
  color: var(--el-color-danger);
}

.ge-hint {
  margin: 0.35rem 0 0;
  font-size: 0.65rem;
  color: var(--fish-text-3);
  line-height: 1.4;
}

/* ===== Cover Upload ===== */
.ge-cover-zone {
  width: 100%;
}

.ge-cover-preview {
  position: relative;
  width: 100%;
  aspect-ratio: 2 / 3;
  border-radius: 0.5rem;
  overflow: hidden;
  background: var(--fish-bg);
  border: 1px solid rgba(255, 255, 255, 0.06);
  cursor: default;
}

.ge-cover-img {
  width: 100%;
  height: 100%;
  display: block;
}

.ge-cover-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  background: rgba(0, 0, 0, 0.55);
  opacity: 0;
  transition: opacity 0.2s;
}

.ge-cover-preview:hover .ge-cover-overlay {
  opacity: 1;
}

.ge-cover-replace :deep(.el-upload) {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.7rem;
  cursor: pointer;
  background: none;
  border: none;
}

.ge-cover-replace:hover {
  color: #fff;
}

.ge-cover-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(225, 29, 72, 0.7);
  color: #fff;
  border: none;
  cursor: pointer;
  transition: background 0.2s;
  padding: 0;
}

.ge-cover-remove:hover {
  background: #E11D48;
}

.ge-cover-empty {
  width: 100%;
  aspect-ratio: 2 / 3;
  border-radius: 0.5rem;
  border: 1px dashed rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.ge-cover-empty:hover {
  border-color: var(--fish-accent-border);
  background: rgba(124, 123, 242, 0.04);
}

.ge-cover-upload-btn {
  width: 100%;
  height: 100%;
}

.ge-cover-upload-btn :deep(.el-upload) {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ge-cover-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: var(--fish-text-3);
  font-size: 0.72rem;
}

/* ===== Select ===== */
.ge-input {
  width: 100%;
  padding: 0.5rem 0.7rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.5rem;
  font-size: 0.8rem;
  background: rgba(255, 255, 255, 0.03);
  color: var(--fish-text-1);
  font-family: inherit;
  font-weight: 500;
  outline: none;
  transition: border-color 0.2s, background 0.2s;
  box-sizing: border-box;
}

.ge-input::placeholder {
  color: var(--fish-text-3);
  font-size: 0.75rem;
}

.ge-input:hover {
  border-color: rgba(124, 123, 242, 0.25);
  background: rgba(255, 255, 255, 0.05);
}

.ge-input:focus {
  border-color: var(--fish-accent);
  box-shadow: 0 0 0 2px rgba(124, 123, 242, 0.1);
}

/* ===== Platform Chips ===== */
.ge-chips {
  display: flex;
  gap: 0.35rem;
  flex-wrap: wrap;
}

.ge-chip {
  flex: 1;
  min-width: 60px;
  padding: 0.4rem 0.3rem;
  border-radius: 0.4rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  color: var(--fish-text-3);
  font-size: 0.7rem;
  font-family: inherit;
  cursor: pointer;
  text-align: center;
  transition: color 0.2s, border-color 0.2s, background 0.2s;
}

.ge-chip:hover {
  color: var(--fish-accent);
  border-color: rgba(124, 123, 242, 0.25);
}

.ge-chip.active {
  background: rgba(124, 123, 242, 0.12);
  border-color: var(--fish-accent);
  color: var(--fish-accent);
  font-weight: 600;
}

/* ===== Tag Input ===== */
.ge-tag-row {
  display: flex;
  gap: 0.35rem;
  width: 100%;
}

.ge-tag-input {
  flex: 1;
  min-width: 0;
  padding: 0.45rem 0.6rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 0.4rem;
  font-size: 0.75rem;
  background: rgba(255, 255, 255, 0.03);
  color: var(--fish-text-1);
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}

.ge-tag-input::placeholder {
  color: var(--fish-text-3);
  font-size: 0.7rem;
}

.ge-tag-input:focus {
  border-color: rgba(124, 123, 242, 0.4);
}

.ge-tag-add-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 30px;
  flex-shrink: 0;
  border-radius: 0.4rem;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.03);
  color: var(--fish-text-3);
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s, background 0.2s;
  padding: 0;
}

.ge-tag-add-btn:hover {
  color: var(--fish-accent);
  border-color: rgba(124, 123, 242, 0.3);
  background: rgba(124, 123, 242, 0.08);
}

.ge-tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  margin-top: 0.4rem;
}

.ge-tag-item {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.2rem 0.5rem;
  border-radius: 0.3rem;
  background: rgba(124, 123, 242, 0.08);
  border: 1px solid rgba(124, 123, 242, 0.15);
  color: var(--fish-accent);
  font-size: 0.65rem;
  font-weight: 500;
  line-height: 1.4;
}

.ge-tag-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  background: none;
  border: none;
  color: inherit;
  opacity: 0.5;
  cursor: pointer;
  transition: opacity 0.2s;
}

.ge-tag-remove:hover {
  opacity: 1;
}

/* ===== Screenshots ===== */
.ge-screenshots-thumbs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.ge-screenshot-thumb {
  position: relative;
  width: 54px;
  height: 54px;
  border-radius: 0.35rem;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
  background: var(--fish-bg);
}

.ge-screenshot-thumb :deep(.el-image) {
  width: 100%;
  height: 100%;
}

.ge-scr-remove {
  position: absolute;
  top: 1px;
  right: 1px;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0;
  transition: opacity 0.2s;
  padding: 0;
}

.ge-screenshot-thumb:hover .ge-scr-remove {
  opacity: 1;
}

.ge-scr-remove:hover {
  background: #E11D48;
}

.ge-scr-add-upload :deep(.el-upload) {
  display: flex;
}

.ge-scr-add-btn {
  width: 54px;
  height: 54px;
  border-radius: 0.35rem;
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

.ge-scr-add-btn:hover {
  border-color: var(--fish-accent-border);
  color: var(--fish-accent);
}

/* ===== Spacer ===== */
.ge-spacer {
  flex: 1;
  min-height: 0.75rem;
}

/* ===== Publish Button ===== */
.ge-publish-area {
  margin-bottom: 0.5rem;
}

.ge-publish-btn {
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

.ge-publish-btn:hover:not(:disabled) {
  background: #8F8EF5;
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(124, 123, 242, 0.25);
}

.ge-publish-btn:active:not(:disabled) {
  transform: scale(0.98);
}

.ge-publish-btn:disabled {
  background: rgba(124, 123, 242, 0.35);
  color: rgba(255, 255, 255, 0.5);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.ge-btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.2);
  border-top-color: #fff;
  border-radius: 50%;
  animation: ge-spin 0.7s linear infinite;
  flex-shrink: 0;
}

.ge-btn-icon {
  flex-shrink: 0;
}

@keyframes ge-spin {
  to { transform: rotate(360deg); }
}

/* ===== Auto Save ===== */
.ge-auto-save {
  padding-top: 0.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  display: flex;
  align-items: center;
}

.ge-as-saving {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.65rem;
  color: var(--fish-accent);
  font-weight: 500;
}

.ge-as-spinner {
  width: 8px;
  height: 8px;
  border: 1.5px solid rgba(124, 123, 242, 0.2);
  border-top-color: var(--fish-accent);
  border-radius: 50%;
  animation: ge-spin 0.8s linear infinite;
  flex-shrink: 0;
}

.ge-as-saved {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.65rem;
  color: var(--el-color-success);
  font-weight: 500;
}

.ge-as-idle {
  font-size: 0.65rem;
  color: var(--fish-text-3);
  font-weight: 400;
}

/* ============================================
   Main Editor
   ============================================ */
.ge-editor {
  flex: 1;
  min-width: 0;
}

.ge-editor-inner {
  padding: 1.75rem 2rem 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* ===== Name Grid ===== */
.ge-name-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.ge-name-field {
  position: relative;
}

.ge-name-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--fish-text-2);
  margin-bottom: 0.35rem;
}

.ge-label-desc {
  font-weight: 400;
  color: var(--fish-text-3);
  font-size: 0.7rem;
}

.ge-name-input {
  width: 100%;
  padding: 0.55rem 0;
  border: none;
  background: transparent;
  font-size: 1rem;
  font-weight: 600;
  color: var(--fish-text-1);
  outline: none;
  font-family: inherit;
  transition: color 0.2s;
}

.ge-name-input::placeholder {
  color: rgba(255, 255, 255, 0.15);
  font-weight: 500;
}

.ge-name-underline {
  height: 1.5px;
  background: linear-gradient(to right, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.03));
  border-radius: 1px;
  transition: background 0.3s;
  margin-top: 0;
}

.ge-name-input:focus ~ .ge-name-underline {
  background: linear-gradient(to right, var(--fish-accent), rgba(124, 123, 242, 0.25));
}

/* ===== Divider ===== */
.ge-divider {
  height: 1px;
  background: linear-gradient(to right, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.03), transparent);
}

/* ===== Description ===== */
.ge-desc-section {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.ge-desc-hint {
  margin: 0;
  font-size: 0.72rem;
  color: var(--fish-text-3);
  line-height: 1.4;
}

.ge-desc-textarea {
  width: 100%;
  min-height: 280px;
  padding: 0.75rem 0;
  border: none;
  background: transparent;
  font-size: 0.95rem;
  line-height: 1.8;
  color: var(--fish-text-1);
  font-family: inherit;
  resize: vertical;
  outline: none;
}

.ge-desc-textarea::placeholder {
  color: rgba(255, 255, 255, 0.12);
}

/* ===== Card Preview ===== */
.ge-preview-section {
  margin-top: 0.5rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}

.ge-preview-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.ge-preview-label {
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--fish-text-3);
  letter-spacing: 0.03em;
}

.ge-preview-note {
  font-size: 0.65rem;
  color: var(--fish-text-3);
}

.ge-preview-card {
  max-width: 240px;
  border-radius: 0.625rem;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(0, 0, 0, 0.15);
  transition: border-color 0.2s;
}

.ge-preview-card:hover {
  border-color: rgba(124, 123, 242, 0.2);
}

.ge-preview-cover {
  position: relative;
  aspect-ratio: 2 / 3;
  background: rgba(255, 255, 255, 0.02);
  overflow: hidden;
}

.ge-pc-img {
  width: 100%;
  height: 100%;
  display: block;
}

.ge-pc-ph {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--fish-text-3);
  font-size: 0.65rem;
}

.ge-pc-badge {
  position: absolute;
  right: 6px;
  bottom: 6px;
  padding: 2px 7px;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.65);
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.65rem;
  font-weight: 500;
  backdrop-filter: blur(4px);
  line-height: 1.3;
}

.ge-pc-info {
  padding: 0.625rem 0.75rem;
}

.ge-pc-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--fish-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.ge-pc-subnames {
  display: flex;
  flex-wrap: wrap;
  gap: 2px 8px;
  margin-top: 3px;
  font-size: 0.68rem;
  color: var(--fish-text-3);
}

.ge-pc-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.ge-pc-tag {
  padding: 1px 6px;
  border-radius: 4px;
  background: rgba(124, 123, 242, 0.08);
  border: 1px solid rgba(124, 123, 242, 0.12);
  color: var(--fish-accent);
  font-size: 0.6rem;
}

/* ============================================
   Responsive
   ============================================ */
@media (max-width: 960px) {
  .ge-layout {
    flex-direction: column;
  }

  .ge-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    position: static;
    max-height: none;
    overflow: visible;
  }

  .ge-sidebar-inner {
    padding: 1.25rem;
    min-height: auto;
  }

  .ge-spacer {
    display: none;
  }

  .ge-editor-inner {
    padding: 1.25rem;
  }

  .ge-name-grid {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }

  .ge-preview-card {
    max-width: 200px;
  }
}
</style>