<script setup lang="ts">
import { ElMessage } from 'element-plus'
import type { AddLink } from '~/types'
import { addLink } from '~/composables/useLink'
import { isSafeLink } from '~/utils/link'
import { mbToBytes } from '~/utils/format'
import { getErrDetail } from '~/utils/request'

/**
 * 添加游戏链接弹窗：由游戏详情页「资源链接」区块右上角按钮打开，
 * 直接为当前游戏添加一条公开下载链接（任意登录用户可用，后端 add 不限制作者）。
 */
const props = defineProps<{ gameId: number }>()
const visible = defineModel<boolean>({ default: false })
const emit = defineEmits<{ success: [] }>()

// size 表单以 MB 为单位，提交时换算为字节（与 LinkManage 表单语义一致）
const form = reactive<AddLink>({ url: '', content: '', code: '', category: '', size: undefined })
const submitting = ref(false)

function reset() {
  form.url = ''
  form.content = ''
  form.code = ''
  form.category = ''
  form.size = undefined
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
      size: mbToBytes(form.size),
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
        <el-form-item label="大小（MB）">
          <el-input-number v-model="form.size" :min="0" :max="100000" style="width: 100%" />
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
</style>
