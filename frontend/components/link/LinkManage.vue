<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import type { AddLink, EditLink, LinkItems, SizeUnit } from '~/types'
import { useLinkList, addLink, reviewLink, deleteLink } from '~/composables/useLink'
import { isSafeLink } from '~/utils/link'
import { formatLinkSize, bytesToSizeUnit } from '~/utils/format'
import { getErrDetail } from '~/utils/request'

const props = defineProps<{ gameId: number }>()
const { data, pending, error, refresh } = useLinkList(props.gameId)

// size 单位选项
const sizeUnitOptions: SizeUnit[] = ['KB', 'MB', 'GB']

// 新增链接：size 浮点数值 + size_unit 单位选择器，直接提交
const form = reactive<AddLink>({ url: '', content: '', code: '', category: '', size: undefined, size_unit: 'MB' })
const adding = ref(false)

// 行内编辑：editingId 为正在编辑的链接 id（来自列表项），editForm 为回显后的编辑内容
const editForm = reactive<EditLink>({ content: '', code: '', category: '', size: undefined, size_unit: 'MB' })
const editingId = ref<number | null>(null)
const managing = ref(false)

async function handleAdd() {
  if (!form.url.trim()) {
    ElMessage.warning('请输入下载链接 URL')
    return
  }
  if (!isSafeLink(form.url.trim())) {
    ElMessage.warning('链接协议不支持，仅允许 http/https/magnet/ed2k/ftp/thunder/bt')
    return
  }
  adding.value = true
  try {
    await addLink(props.gameId, {
      url: form.url.trim(),
      content: form.content || null,
      code: form.code || null,
      category: form.category || null,
      size: form.size != null ? form.size : null,
      size_unit: form.size != null ? (form.size_unit || 'MB') : null,
    })
    ElMessage.success('链接添加成功')
    form.url = ''
    form.content = ''
    form.code = ''
    form.category = ''
    form.size = null
    form.size_unit = 'MB'
    refresh()
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '添加失败'))
  } finally {
    adding.value = false
  }
}

// 回显到编辑表单：新数据直接取 size + size_unit，旧数据（无 unit）按字节自动换算
function fillEdit(entry: LinkItems) {
  editingId.value = entry.item.id
  editForm.content = entry.item.content || ''
  editForm.code = entry.item.code || ''
  editForm.category = entry.item.category || ''
  if (entry.item.size_unit) {
    editForm.size = entry.item.size ?? undefined
    editForm.size_unit = entry.item.size_unit
  } else {
    // 旧数据：size 为字节，自动换算合适单位
    const converted = bytesToSizeUnit(entry.item.size)
    editForm.size = converted.size
    editForm.size_unit = converted.size_unit
  }
  ElMessage.info('已填入编辑表单，可在下方修改后点击「保存修改」')
}

function cancelEdit() {
  editingId.value = null
  editForm.content = ''
  editForm.code = ''
  editForm.category = ''
  editForm.size = null
  editForm.size_unit = 'MB'
}

async function handleReview() {
  if (editingId.value == null) {
    ElMessage.warning('请先在列表中点击某条链接的「编辑」')
    return
  }
  managing.value = true
  try {
    await reviewLink(editingId.value, {
      content: editForm.content || null,
      code: editForm.code || null,
      category: editForm.category || null,
      size: editForm.size != null ? editForm.size : null,
      size_unit: editForm.size != null ? (editForm.size_unit || 'MB') : null,
    })
    ElMessage.success('链接已更新')
    cancelEdit()
    refresh()
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '更新失败'))
  } finally {
    managing.value = false
  }
}

async function handleDelete(entry: LinkItems) {
  try {
    await ElMessageBox.confirm('确定删除该链接吗？', '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await deleteLink(entry.item.id)
    ElMessage.success('链接已删除')
    if (editingId.value === entry.item.id) cancelEdit()
    refresh()
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '删除失败'))
  }
}
</script>

<template>
  <div class="link-manage">
    <!-- ===== 链接列表 ===== -->
    <h3 class="lm-title">现有链接（{{ data?.total ?? 0 }}）</h3>
    <el-skeleton v-if="pending" :rows="3" animated />
    <el-alert
      v-else-if="error"
      title="链接加载失败"
      type="error"
      :closable="false"
      show-icon
      class="mb"
    />
    <ClientOnly v-else-if="!data?.items?.length">
      <el-empty description="暂无下载链接" :image-size="70" />
    </ClientOnly>

    <ul v-else class="lm-list">
      <li v-for="entry in data.items" :key="entry.item.id" class="lm-item">
        <div class="lm-main">
          <a
            v-if="isSafeLink(entry.item.url)"
            :href="entry.item.url"
            target="_blank"
            rel="noopener noreferrer"
            class="lm-url"
          >
            <el-icon><Link /></el-icon>
            {{ entry.item.url }}
          </a>
          <span v-else class="lm-url unsafe">
            <el-icon><Link /></el-icon>
            {{ entry.item.url }}
          </span>
          <div class="lm-badges">
            <el-tag v-if="entry.item.category" size="small" type="info">
              分类：{{ entry.item.category }}
            </el-tag>
            <el-tag v-if="entry.item.size" size="small" type="warning">
              大小：{{ formatLinkSize(entry.item.size, entry.item.size_unit) }}
            </el-tag>
            <span v-if="entry.item.code" class="lm-code">提取码 {{ entry.item.code }}</span>
          </div>
          <p v-if="entry.item.content" class="lm-content">{{ entry.item.content }}</p>
        </div>
        <div class="lm-actions">
          <el-button size="small" plain @click="fillEdit(entry)">编辑</el-button>
          <el-button size="small" plain type="danger" @click="handleDelete(entry)">删除</el-button>
        </div>
      </li>
    </ul>

    <!-- ===== 添加新链接 ===== -->
    <h3 class="lm-title">添加新链接</h3>
    <el-form label-position="top" class="lm-form" @submit.prevent="handleAdd">
      <el-form-item label="下载地址" required>
        <el-input v-model="form.url" placeholder="https:// 或 magnet: 链接" />
      </el-form-item>
      <div class="lm-grid">
        <el-form-item label="分类">
          <el-input v-model="form.category" placeholder="如 网盘 / 磁力 / BT" />
        </el-form-item>
        <el-form-item label="大小">
          <div class="size-group">
            <el-input-number v-model="form.size" :min="0" :max="999999" :precision="2" :step="0.1" style="flex: 1" />
            <el-select v-model="form.size_unit" style="width: 80px; flex-shrink: 0">
              <el-option v-for="u in sizeUnitOptions" :key="u" :label="u" :value="u" />
            </el-select>
          </div>
        </el-form-item>
      </div>
      <el-form-item label="备注">
        <el-input v-model="form.content" type="textarea" :rows="2" placeholder="解压码 / 版本说明等" />
      </el-form-item>
      <el-form-item label="提取码（可选）">
        <el-input v-model="form.code" placeholder="网盘提取码" maxlength="255" />
      </el-form-item>
      <el-button type="primary" native-type="submit" :loading="adding">添加链接</el-button>
    </el-form>

    <!-- ===== 编辑链接 ===== -->
    <h3 class="lm-title">编辑链接</h3>
    <el-form label-position="top" class="lm-form" @submit.prevent="handleReview">
      <div class="lm-grid">
        <el-form-item label="分类">
          <el-input v-model="editForm.category" placeholder="如 网盘 / 磁力 / BT" />
        </el-form-item>
        <el-form-item label="大小">
          <div class="size-group">
            <el-input-number v-model="editForm.size" :min="0" :max="999999" :precision="2" :step="0.1" style="flex: 1" />
            <el-select v-model="editForm.size_unit" style="width: 80px; flex-shrink: 0">
              <el-option v-for="u in sizeUnitOptions" :key="u" :label="u" :value="u" />
            </el-select>
          </div>
        </el-form-item>
      </div>
      <el-form-item label="备注">
        <el-input v-model="editForm.content" type="textarea" :rows="2" placeholder="解压码 / 版本说明等" />
      </el-form-item>
      <el-form-item label="提取码（可选）">
        <el-input v-model="editForm.code" placeholder="网盘提取码" maxlength="255" />
      </el-form-item>
      <div class="lm-edit-actions">
        <el-button
          type="primary"
          native-type="submit"
          :loading="managing"
          :disabled="editingId == null"
        >
          保存修改
        </el-button>
        <el-button :disabled="editingId == null" @click="cancelEdit">取消</el-button>
      </div>
      <p class="lm-hint">在列表中点击某条链接的「编辑」填充表单后，再点击「保存修改」。删除可直接在列表中操作。</p>
    </el-form>
  </div>
</template>

<style scoped>
.link-manage {
  background: var(--fish-bg-2);
  border: 1px solid var(--fish-border);
  border-radius: var(--fish-radius);
  padding: 24px;
  box-shadow: var(--fish-shadow);
}
.mb {
  margin-bottom: 12px;
}

.lm-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 14px;
  font-size: 16px;
  font-weight: 700;
  color: var(--fish-text-1);
}
.lm-title::before {
  content: '';
  width: 4px;
  height: 15px;
  border-radius: 3px;
  background: var(--fish-accent);
  flex-shrink: 0;
}
.lm-title + .lm-form,
.lm-title + .lm-list,
.lm-title + .lm-title {
  margin-top: 0;
}

/* 链接列表 */
.lm-list {
  list-style: none;
  margin: 0 0 24px;
  padding: 0;
}
.lm-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid var(--fish-border);
  border-radius: 10px;
  margin-bottom: 10px;
  background: var(--fish-bg);
  transition: border-color 0.2s, transform 0.2s;
}
.lm-item:hover {
  border-color: var(--fish-accent-border);
  transform: translateY(-1px);
}
.lm-main {
  flex: 1;
  min-width: 0;
}
.lm-url {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: var(--fish-accent);
  text-decoration: none;
  word-break: break-all;
}
.lm-url:hover {
  text-decoration: underline;
}
.lm-url.unsafe,
.lm-url.unsafe:hover {
  color: var(--fish-text-3);
  text-decoration: none;
  cursor: default;
}
.lm-badges {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  margin-top: 8px;
}
.lm-code {
  font-size: 12px;
  color: var(--fish-text-3);
}
.lm-content {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--fish-text-2);
  line-height: 1.6;
}
.lm-actions {
  flex-shrink: 0;
  display: flex;
  gap: 6px;
}

/* 表单 */
.lm-form {
  margin-bottom: 24px;
}
.lm-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 16px;
}
.size-group {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.lm-edit-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.lm-hint {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--fish-text-3);
}

@media (max-width: 560px) {
  .lm-grid {
    grid-template-columns: 1fr;
  }
  .lm-item {
    flex-direction: column;
  }
  .lm-actions {
    align-self: flex-end;
  }
}
</style>
