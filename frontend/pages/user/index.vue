<script setup lang="ts">
import { useAuthStore } from '~/stores/auth'

const route = useRoute()
const auth = useAuthStore()

type TabName = 'login' | 'register'

// 初始 tab 只由 URL 决定，保证 SSR 与客户端首帧渲染一致，避免水合不匹配。
const activeTab = ref<TabName>(route.query.mode === 'register' ? 'register' : 'login')

// 登录/注册与「我的资料」分离：已登录用户或旧链接 /user?mode=profile 统一跳转独立资料页。
// localStorage 仅浏览器可读，故在 onMounted 中跳转。
onMounted(() => {
  if (auth.token || route.query.mode === 'profile') {
    navigateTo('/user/profile')
  }
})

function handleRegistered() {
  activeTab.value = 'login'
}
</script>

<template>
  <div class="user-page">
    <el-card shadow="never" class="user-card">
      <template #header>
        <span class="card-title">登录 / 注册</span>
      </template>

      <el-tabs v-model="activeTab">
        <el-tab-pane label="登录" name="login">
          <LoginForm />
        </el-tab-pane>
        <el-tab-pane label="注册" name="register">
          <RegisterForm @registered="handleRegistered" />
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.user-page {
  max-width: 560px;
  margin: 0 auto;
  padding: 16px 0;
}
.card-title {
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.3px;
}
</style>
