<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import type { UploadFile } from 'element-plus'
import type { UserProfile, AccountUpdate } from '~/types'
import { useAuth } from '~/composables/useAuth'
import { readImageAsBase64 } from '~/utils/file'
import { getErrDetail } from '~/utils/request'

const { fetchProfile, updateProfile, deleteAccount } = useAuth()

const profile = ref<UserProfile | null>(null)
const loading = ref(false)
const saving = ref(false)
const avatarPreview = ref('')
const avatarBase64 = ref('')

const form = reactive({
  username: '',
  email: '',
  bio: '',
  password: '',
})

async function loadProfile() {
  loading.value = true
  try {
    profile.value = await fetchProfile()
    form.username = profile.value.username
    form.email = profile.value.email
    form.bio = profile.value.bio || ''
    avatarPreview.value = profile.value.avatar || ''
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '加载用户信息失败'))
  } finally {
    loading.value = false
  }
}

onMounted(loadProfile)

async function onAvatarChange(uploadFile: UploadFile) {
  const raw = uploadFile.raw
  if (!raw) return
  try {
    const b64 = await readImageAsBase64(raw)
    avatarBase64.value = b64
    avatarPreview.value = b64
  } catch (err) {
    ElMessage.error(err instanceof Error ? err.message : '图片读取失败')
  }
}

function onAvatarRemove() {
  avatarBase64.value = ''
  avatarPreview.value = profile.value?.avatar || ''
}

async function handleSave() {
  if (form.username.length < 2 || form.username.length > 20) {
    ElMessage.warning('用户名长度需为 2-20 字符')
    return
  }
  // 邮箱为账户必填字段：为空或格式非法会导致后端 EmailStr 校验 422，这里先行拦截
  const email = form.email.trim()
  if (!email || !/^\S+@\S+\.\S+$/.test(email)) {
    ElMessage.warning('请输入有效的邮箱地址')
    return
  }
  if (form.password && (form.password.length < 6 || form.password.length > 20)) {
    ElMessage.warning('密码长度需为 6-20 字符')
    return
  }
  saving.value = true
  try {
    const payload: AccountUpdate = {
      username: form.username,
      email,
      bio: form.bio,
      password: form.password || undefined,
      avatar: avatarBase64.value || undefined,
    }
    const res = await updateProfile(payload)
    profile.value = { ...profile.value!, ...res }
    avatarBase64.value = ''
    form.password = ''
    ElMessage.success('资料更新成功')
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '保存失败'))
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm(
      '确定删除账号吗？若已发布游戏将无法删除（后端外键限制），且删除操作不可恢复。',
      '删除账号',
      { type: 'warning', confirmButtonText: '确认删除', cancelButtonText: '取消' },
    )
  } catch {
    return
  }
  try {
    await deleteAccount()
    ElMessage.success('账号已删除')
    navigateTo('/')
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '删除失败'))
  }
}
</script>

<template>
  <div v-loading="loading">
    <ClientOnly v-if="!loading && !profile">
      <el-empty description="未获取到用户信息" />
    </ClientOnly>
    <template v-else>
      <el-form label-position="top" @submit.prevent="handleSave">
        <el-form-item label="头像">
          <el-upload
            class="avatar-uploader"
            :show-file-list="false"
            :auto-upload="false"
            accept="image/*"
            :on-change="onAvatarChange"
            :on-remove="onAvatarRemove"
          >
            <img v-if="avatarPreview" :src="avatarPreview" class="avatar-preview" alt="头像" />
            <el-icon v-else class="avatar-uploader-icon"><Plus /></el-icon>
          </el-upload>
        </el-form-item>
        <el-form-item label="用户名" required>
          <el-input v-model="form.username" placeholder="2-20 个字符" maxlength="20" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" type="email" placeholder="用于登录与接收通知" />
        </el-form-item>
        <el-form-item label="个人简介">
          <el-input v-model="form.bio" type="textarea" :rows="3" placeholder="介绍一下自己" />
        </el-form-item>
        <el-form-item label="修改密码（留空则不改）">
          <el-input v-model="form.password" type="password" show-password placeholder="6-20 个字符" />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="saving">
          保存修改
        </el-button>
      </el-form>

      <el-divider />

      <div class="danger-zone">
        <el-button type="danger" plain @click="handleDelete">删除账号</el-button>
      </div>
    </template>
  </div>
</template>

<style scoped>
.avatar-uploader :deep(.el-upload) {
  border: 1px dashed rgba(226, 232, 240, 0.7);
  border-radius: 0.75rem;
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  background: rgba(255, 255, 255, 0.5);
}
html.dark .avatar-uploader :deep(.el-upload) {
  border-color: rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.04);
}
.avatar-uploader :deep(.el-upload:hover) {
  border-color: var(--el-color-primary);
}
.avatar-preview {
  width: 120px;
  height: 120px;
  object-fit: cover;
  display: block;
}
.avatar-uploader-icon {
  width: 120px;
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  color: #71717a;
}
.danger-zone {
  text-align: right;
}
</style>
