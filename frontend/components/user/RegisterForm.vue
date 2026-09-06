<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { useAuth, useEmail } from '~/composables/useAuth'
import { getErrDetail } from '~/utils/request'

const emit = defineEmits<{ registered: [] }>()

const { register } = useAuth()
const { sendCode } = useEmail()

const form = reactive({
  username: '',
  password: '',
  confirmPassword: '',
  email: '',
  bio: '',
  code: '',
})
const loading = ref(false)
const sending = ref(false)
const countdown = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

function clearTimer() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}
onUnmounted(clearTimer)

async function handleSendCode() {
  if (!form.email) {
    ElMessage.warning('请先填写邮箱')
    return
  }
  sending.value = true
  try {
    await sendCode(form.email)
    ElMessage.success('验证码已发送，请查收邮箱')
    countdown.value = 60
    clearTimer()
    timer = setInterval(() => {
      countdown.value -= 1
      if (countdown.value <= 0) clearTimer()
    }, 1000)
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '验证码发送失败'))
  } finally {
    sending.value = false
  }
}

async function handleSubmit() {
  if (form.username.length < 2 || form.username.length > 20) {
    ElMessage.warning('用户名长度需为 2-20 字符')
    return
  }
  if (form.password.length < 6 || form.password.length > 20) {
    ElMessage.warning('密码长度需为 6-20 字符')
    return
  }
  if (form.password !== form.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  if (!form.code.trim()) {
    ElMessage.warning('请输入邮箱验证码')
    return
  }
  loading.value = true
  try {
    await register(
      {
        username: form.username,
        password: form.password,
        email: form.email,
        bio: form.bio || null,
      },
      form.code.trim(),
    )
    ElMessage.success('注册成功，请登录')
    emit('registered')
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '注册失败'))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <el-form label-position="top" @submit.prevent="handleSubmit">
    <el-form-item label="用户名" required>
      <el-input v-model="form.username" placeholder="2-20 个字符" maxlength="20" />
    </el-form-item>
    <el-form-item label="邮箱" required>
      <div class="email-row">
        <el-input v-model="form.email" placeholder="用于接收验证码" />
        <el-button :loading="sending" :disabled="countdown > 0" @click="handleSendCode">
          {{ countdown > 0 ? `${countdown}s 后重发` : '发送验证码' }}
        </el-button>
      </div>
    </el-form-item>
    <el-form-item label="邮箱验证码" required>
      <el-input v-model="form.code" placeholder="请输入收到的 6 位验证码" maxlength="6" />
    </el-form-item>
    <el-form-item label="密码" required>
      <el-input v-model="form.password" type="password" show-password placeholder="6-20 个字符" />
    </el-form-item>
    <el-form-item label="确认密码" required>
      <el-input
        v-model="form.confirmPassword"
        type="password"
        show-password
        placeholder="再次输入密码"
        @keyup.enter="handleSubmit"
      />
    </el-form-item>
    <el-form-item label="个人简介（可选）">
      <el-input v-model="form.bio" type="textarea" :rows="2" placeholder="一句话介绍自己" />
    </el-form-item>
    <el-button type="primary" native-type="submit" :loading="loading" class="w-full">
      注册
    </el-button>
  </el-form>
</template>

<style scoped>
.w-full {
  width: 100%;
}
.email-row {
  display: flex;
  gap: 8px;
  width: 100%;
}
</style>
