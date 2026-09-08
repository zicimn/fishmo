<script setup lang="ts">
import { ElMessage } from 'element-plus'
import type { AddLink, SizeUnit } from '~/types'
import { addLink } from '~/composables/useLink'
import { isSafeLink } from '~/utils/link'
import { getErrDetail } from '~/utils/request'

/**
 * 添加游戏链接弹窗：由游戏详情页「资源链接」区块右上角按钮打开，
 * 直接为当前游戏添加一条公开下载链接（任意登录用户可用，后端 add 不限制作者）。
 */
const props = defineProps<{ gameId: number }>()
const visible = defineModel<boolean>({ default: false })
const emit = defineEmits<{ success: [] }>()

// size 为浮点数值 + size_unit 单位选择器，直接提交无需换算
const sizeUnitOptions: SizeUnit[] = ['KB', 'MB', 'GB']
const form = reactive<AddLink>({ url: '', content: '', code: '', category: '', size: undefined, size_unit: 'MB' })
const submitting = ref(false)

function reset() {
  form.url = ''
  form.content = ''
  form.code = ''
  form.category = ''
  form.size = undefined
  form.size_unit = 'MB'
}

async function handleSubmit() {
  if (!form.url.trim()) {
    ElMessage.warning('请输入下载链接 URL')
    return
  }
  if (!isSafeLink(form.url.trim())) {
    ElMessage.warning('链接协议不支持，仅允许 http/https/magnet/ed2k/ftp/thunder/bt')
    return
  }
  submitting.value = true
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
    visible.value = false
    emit('success')
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '添加失败'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <el-dialog
    v-model="visible"
    title="添加游戏链接"
    width="460px"
    :close-on-click-modal="!submitting"
    :close-on-press-escape="!submitting"
    :show-close="!submitting"
    destroy-on-close
    @closed="reset"
  >
    <el-form label-position="top" @submit.prevent="handleSubmit">
      <el-form-item label="下载地址" required>
        <el-input v-model="form.url" placeholder="https:// 或 magnet: 链接" />
      </el-form-item>
      <div class="form-grid">
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
    </el-form>
    <template #footer>
      <el-button :disabled="submitting" @click="visible = false">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">添加链接</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.form-grid {
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
</style>
