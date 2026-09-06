<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { useAuth } from '~/composables/useAuth'
import { getErrDetail } from '~/utils/request'

const route = useRoute()
const { login } = useAuth()

const form = reactive({ username: '', password: '' })
const loading = ref(false)

async function handleSubmit() {
  if (!form.username.trim() || !form.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }
  loading.value = true
  try {
    await login(form.username.trim(), form.password)
    ElMessage.success('登录成功')
    // 支持登录后回跳（auth 中间件传递的 redirect 参数）。
    // 仅允许站内相对路径，禁止协议相对地址（//evil.com）与反斜杠变体，防止开放重定向。
    const redirect = route.query.redirect
    const isInternalPath =
      typeof redirect === 'string' &&
      redirect.startsWith('/') &&
      !redirect.startsWith('//') &&
      !redirect.startsWith('/\\')
    navigateTo(isInternalPath ? redirect : '/')
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '登录失败，请稍后重试'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <el-form label-position="top" @submit.prevent="handleSubmit">
    <el-form-item label="用户名" required>
      <el-input v-model="form.username" placeholder="请输入用户名" autocomplete="username" />
    </el-form-item>
    <el-form-item label="密码" required>
      <el-input
        v-model="form.password"
        type="password"
        show-password
        placeholder="请输入密码"
        autocomplete="current-password"
        @keyup.enter="handleSubmit"
      />
    </el-form-item>
    <el-button type="primary" native-type="submit" :loading="loading" class="w-full">
      登录
    </el-button>
  </el-form>
</template>

<style scoped>
.w-full {
  width: 100%;
}
</style>
