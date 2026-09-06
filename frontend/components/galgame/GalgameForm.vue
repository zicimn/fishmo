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
 * 游戏发布/编辑共用表单。
 * - mode="add"：完整校验（至少一个名称 + 封面必填），提交 AddGal。
 * - mode="edit"：预填已发布字段；仅上传了新封面/新截图时才提交 cover/images（后端整体替换截图）。
 * - 布局：左侧分区表单 + 右侧 sticky 卡片实时预览（与首页 GameCard 同比例 2:3）。
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

const coverBase64 = ref('')
const coverPreview = ref('')
const imageFileList = ref<UploadUserFile[]>([])
const imageBase64Map = new Map<string, string>()
const imagesBase64 = computed(() =>
  imageFileList.value
    .map((f: UploadUserFile) => (f.uid != null ? imageBase64Map.get(String(f.uid)) : undefined))
    .filter((b: string | undefined): b is string => !!b),
)

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

// 编辑模式预填可回填字段（详情接口已返回三名称与作者 id，直接回填）
if (props.mode === 'edit' && props.initial) {
  const initial = props.initial
  form.cn_name = initial.cn_name || ''
  form.jp_name = initial.jp_name || ''
  form.en_name = initial.en_name || ''
  form.content = initial.content || ''
  form.company = initial.company || []
  // 仅回填合法枚举值：历史自由文本分类不在枚举内，留空则不随 edit 提交（后端保留原值）
  form.category = CATEGORY_OPTIONS.some((c) => c.value === initial.category)
    ? (initial.category as CategoryValue)
    : ''
  form.tag = initial.tag || []
  form.platfrom = (initial.platfrom || []) as PlatformValue[]
  coverPreview.value = initial.cover || ''
}

// ===== 实时预览数据 =====
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
  return tags.slice(0, 4)
})

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
    // 超限/读取失败：从已展示的 file-list 中移除，避免加入预览与提交
    imageFileList.value = imageFileList.value.filter((f: UploadUserFile) => f.uid !== uploadFile.uid)
    ElMessage.error(err instanceof Error ? err.message : '图片读取失败')
  }
}

function onImagesRemove(uploadFile: UploadFile) {
  imageBase64Map.delete(String(uploadFile.uid))
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

  // edit 模式：只携带显式变更的封面/截图，未变更则不传（后端保留原值）
  const payload: EditGal = { ...base }
  if (coverBase64.value) payload.cover = coverBase64.value
  if (imagesBase64.value.length) payload.images = imagesBase64.value
  return payload
}

function validate(): boolean {
  // add 模式要求至少一个名称；edit 模式后端 EditGal 全可选、名称留空不覆盖，故放开
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

function handleSubmit() {
  if (!validate()) return
  emit('submit', buildPayload())
}
</script>

<template>
  <div class="gal-form-wrap">
    <el-form label-position="top" class="gal-form gal-main" @submit.prevent="handleSubmit">
      <el-alert
        v-if="mode === 'edit' && initial"
        type="info"
        :closable="false"
        show-icon
        class="mb"
      >
        <template #title>
          已回填当前名称（{{ initial.name }}），留空则保持不变。
        </template>
      </el-alert>

      <!-- ===== 基本信息 ===== -->
      <section class="f-section">
        <h3 class="f-section-title">基本信息</h3>
        <p class="f-section-desc">中文 / 日文 / 英文名称至少填写一个，用于站内检索与卡片展示。</p>
        <div class="form-grid">
          <el-form-item label="中文名（选填）">
            <el-input v-model="form.cn_name" placeholder="简体中文名" maxlength="50" />
          </el-form-item>
          <el-form-item label="日文名（选填）">
            <el-input v-model="form.jp_name" placeholder="日文原名" maxlength="50" />
          </el-form-item>
          <el-form-item label="英文名（选填）">
            <el-input v-model="form.en_name" placeholder="英文名" maxlength="50" />
          </el-form-item>
        </div>
        <div class="form-grid">
          <el-form-item label="作品类型（分类）">
            <el-select
              v-model="form.category"
              clearable
              placeholder="选择作品类型"
              style="width: 100%"
            >
              <el-option v-for="c in CATEGORY_OPTIONS" :key="c.value" :label="c.label" :value="c.value" />
            </el-select>
          </el-form-item>
          <el-form-item label="制作公司">
            <el-select
              v-model="form.company"
              multiple
              filterable
              allow-create
              default-first-option
              placeholder="输入后回车添加"
              style="width: 100%"
            >
              <el-option v-for="c in form.company" :key="c" :label="c" :value="c" />
            </el-select>
          </el-form-item>
        </div>
      </section>

      <!-- ===== 游戏简介 ===== -->
      <section class="f-section">
        <h3 class="f-section-title">游戏简介</h3>
        <p class="f-section-desc">介绍剧情、玩法与特色，展示在详情页「游戏简介」区块。</p>
        <el-input
          v-model="form.content"
          type="textarea"
          :rows="5"
          placeholder="介绍游戏内容……"
        />
      </section>

      <!-- ===== 标签与平台 ===== -->
      <section class="f-section">
        <h3 class="f-section-title">标签与平台</h3>
        <el-form-item label="标签">
          <el-select
            v-model="form.tag"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="输入后回车添加，如 治愈 / 致郁 / 纯爱"
            style="width: 100%"
          >
            <el-option v-for="t in form.tag" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
        <el-form-item label="支持平台">
          <div class="platform-chips">
            <button
              v-for="p in PLATFORM_OPTIONS"
              :key="p.value"
              type="button"
              class="p-chip"
              :class="{ active: form.platfrom.includes(p.value) }"
              @click="togglePlatform(p.value)"
            >
              {{ p.label }}
            </button>
          </div>
        </el-form-item>
      </section>

      <!-- ===== 封面与截图 ===== -->
      <section class="f-section">
        <h3 class="f-section-title">封面与截图</h3>
        <el-form-item label="封面图" :required="mode === 'add'">
          <el-upload
            class="cover-uploader"
            :show-file-list="false"
            :auto-upload="false"
            accept="image/*"
            :on-change="onCoverChange"
            :on-remove="onCoverRemove"
          >
            <div v-if="coverPreview" class="cover-box">
              <el-image :src="coverPreview" fit="cover" class="cover-img" />
              <div class="cover-mask">
                <el-icon :size="16"><RefreshLeft /></el-icon>
                <span>更换封面</span>
              </div>
            </div>
            <div v-else class="cover-placeholder">
              <el-icon :size="26"><Plus /></el-icon>
              <span>上传 2:3 封面</span>
            </div>
          </el-upload>
          <p class="f-hint">2:3 竖版封面：首页卡片与详情页主视觉均使用该比例，后端统一转为 WebP（≤5MB）。</p>
        </el-form-item>

        <el-form-item label="游戏截图">
          <el-upload
            v-model:file-list="imageFileList"
            list-type="picture-card"
            :auto-upload="false"
            accept="image/*"
            multiple
            :on-change="onImagesChange"
            :on-remove="onImagesRemove"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <p v-if="mode === 'edit'" class="f-hint">
            编辑时新上传的截图将整体替换原截图；不上传新截图则保持原截图不变。
          </p>
        </el-form-item>
      </section>

      <div class="form-actions">
        <el-button type="primary" native-type="submit" :loading="submitting">
          {{ mode === 'add' ? '发布游戏' : '保存修改' }}
        </el-button>
        <el-button @click="emit('cancel')">取消</el-button>
      </div>
    </el-form>

    <!-- ===== 右侧实时预览 ===== -->
    <aside class="gal-preview">
      <div class="preview-head">卡片预览</div>
      <div class="preview-card">
        <div class="preview-cover">
          <el-image v-if="coverPreview" :src="coverPreview" fit="cover" class="preview-cover-img" />
          <div v-else class="preview-cover-ph">
            <el-icon :size="22"><Picture /></el-icon>
            <span>封面占位</span>
          </div>
          <span class="preview-new">新发布</span>
        </div>
        <div class="preview-info">
          <div class="preview-name" :title="previewName">{{ previewName }}</div>
          <div v-if="previewSubNames.length" class="preview-subnames">
            <span v-for="n in previewSubNames" :key="n">{{ n }}</span>
          </div>
          <div v-if="previewTags.length" class="preview-tags">
            <span v-for="t in previewTags" :key="t" class="p-tag">{{ t }}</span>
          </div>
        </div>
      </div>
      <p class="preview-note">预览即首页游戏卡片样式，发布后自动生效。</p>
    </aside>
  </div>
</template>

<style scoped>
.mb {
  margin-bottom: 16px;
}

/* ===== 左侧表单 + 右侧预览双栏 ===== */
.gal-form-wrap {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220px;
  gap: 24px;
  align-items: start;
}
.gal-main {
  display: flex;
  flex-direction: column;
  gap: 20px;
  min-width: 0;
}

/* 分区卡片 */
.f-section {
  background: var(--fish-bg-2);
  border: 1px solid var(--fish-border);
  border-radius: var(--fish-radius);
  padding: 24px;
}
.f-section-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 700;
  color: var(--fish-text-1);
}
.f-section-title::before {
  content: '';
  width: 4px;
  height: 15px;
  border-radius: 3px;
  background: var(--fish-accent);
  flex-shrink: 0;
}
.f-section-desc {
  margin: 0 0 18px;
  font-size: 12px;
  color: var(--fish-text-3);
  line-height: 1.6;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0 16px;
}
.f-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--fish-text-3);
  line-height: 1.6;
}

/* 平台 chips */
.platform-chips {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.p-chip {
  padding: 7px 16px;
  border-radius: 999px;
  border: 1px solid var(--fish-border);
  background: var(--fish-bg);
  color: var(--fish-text-2);
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s, background 0.2s;
}
.p-chip:hover {
  color: var(--fish-accent);
  border-color: var(--fish-accent-border);
}
.p-chip.active {
  background: var(--fish-accent-soft);
  border-color: var(--fish-accent);
  color: var(--fish-accent);
  font-weight: 600;
}

/* 2:3 封面上传 */
.cover-uploader :deep(.el-upload) {
  border: 1px dashed var(--fish-border-strong);
  border-radius: 10px;
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.2s, box-shadow 0.2s;
  background: var(--fish-bg);
  display: block;
}
.cover-uploader :deep(.el-upload:hover) {
  border-color: var(--fish-accent);
  box-shadow: 0 0 0 3px var(--fish-accent-soft);
}
.cover-box {
  position: relative;
  width: 200px;
  aspect-ratio: 2 / 3;
}
.cover-img {
  width: 100%;
  height: 100%;
  display: block;
}
.cover-mask {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  background: rgba(11, 11, 15, 0.55);
  color: #fff;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.2s;
}
.cover-box:hover .cover-mask {
  opacity: 1;
}
.cover-placeholder {
  width: 200px;
  aspect-ratio: 2 / 3;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: var(--fish-text-3);
  font-size: 13px;
}

/* 操作区 */
.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 4px;
}

/* ===== 右侧预览 ===== */
.gal-preview {
  position: sticky;
  top: 80px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.preview-head {
  font-size: 13px;
  font-weight: 700;
  color: var(--fish-text-2);
}
.preview-card {
  background: var(--fish-bg-2);
  border: 1px solid var(--fish-border);
  border-radius: var(--fish-radius);
  overflow: hidden;
  box-shadow: var(--fish-shadow);
  transition: border-color 0.2s;
}
.preview-card:hover {
  border-color: var(--fish-accent-border);
}
.preview-cover {
  position: relative;
  aspect-ratio: 2 / 3;
  background: var(--fish-bg);
}
.preview-cover-img {
  width: 100%;
  height: 100%;
  display: block;
}
.preview-cover-ph {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--fish-text-3);
  font-size: 12px;
}
.preview-new {
  position: absolute;
  right: 8px;
  bottom: 8px;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(11, 11, 15, 0.72);
  color: rgba(255, 255, 255, 0.9);
  font-size: 12px;
  font-weight: 500;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}
.preview-info {
  padding: 12px 14px 14px;
}
.preview-name {
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
  color: var(--fish-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.preview-subnames {
  display: flex;
  flex-wrap: wrap;
  gap: 2px 10px;
  margin-top: 4px;
  font-size: 12px;
  color: var(--fish-text-3);
}
.preview-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
.p-tag {
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--fish-accent-soft);
  border: 1px solid var(--fish-accent-border);
  color: var(--fish-accent);
  font-size: 11px;
}
.preview-note {
  margin: 0;
  font-size: 12px;
  color: var(--fish-text-3);
  line-height: 1.6;
}

/* ===== 响应式：预览折叠到下方 ===== */
@media (max-width: 1024px) {
  .gal-form-wrap {
    grid-template-columns: 1fr;
  }
  .gal-preview {
    position: static;
    order: -1;
    max-width: 260px;
  }
}
</style>
