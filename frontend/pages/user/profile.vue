<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { useAuth } from '~/composables/useAuth'
import { useAuthStore } from '~/stores/auth'
import { getErrDetail } from '~/utils/request'
import type { UserProfile } from '~/types'

// 登录守卫：客户端判断，SSR 阶段放行（token 未从 localStorage 恢复），未登录跳 /user 登录
definePageMeta({ middleware: 'auth' })

const authStore = useAuthStore()
const { fetchProfile } = useAuth()

type MenuName = 'games' | 'comments' | 'links' | 'settings'

// 左侧透明菜单项（图标为全局注册的 Element Plus 图标组件名）
const menuItems: { name: MenuName; label: string; icon: string }[] = [
  { name: 'games', label: '游戏', icon: 'Trophy' },
  { name: 'comments', label: '评论', icon: 'ChatDotRound' },
  { name: 'links', label: '链接', icon: 'Link' },
  { name: 'settings', label: '设置', icon: 'Setting' },
]

const activeTab = ref<MenuName>('games')

// ===== 卡片 A：个人资料（头像 + 用户名 + 邮箱 + 简介） =====
const profile = ref<UserProfile | null>(null)
const loading = ref(false)

async function loadProfile(showError = true) {
  loading.value = true
  try {
    profile.value = await fetchProfile()
  } catch (e: any) {
    if (showError) ElMessage.error(getErrDetail(e, '加载用户信息失败'))
  } finally {
    loading.value = false
  }
}

onMounted(() => loadProfile())

function switchTab(tab: MenuName) {
  activeTab.value = tab
  // 静默刷新卡片 A：设置中改完资料后切回其它 tab，信息立即更新
  loadProfile(false)
}

function handleLogout() {
  authStore.logout()
  ElMessage.success('已退出登录')
  navigateTo('/')
}
</script>

<template>
  <div class="profile-page">
    <el-skeleton v-if="loading && !profile" :rows="4" animated />
    <ClientOnly v-else-if="!profile">
      <el-empty description="未获取到用户信息">
        <template #extra>
          <el-button @click="loadProfile()">重试</el-button>
        </template>
      </el-empty>
    </ClientOnly>

    <template v-else>
      <!-- ===== 卡片 A：头像 + 个人信息（顶部，单卡片） ===== -->
      <section class="profile-card">
        <div class="avatar-ring">
          <el-avatar :size="80" :src="profile.avatar || undefined">
            {{ profile.username.charAt(0).toUpperCase() || 'U' }}
          </el-avatar>
        </div>
        <div class="pc-info">
          <div class="pc-head">
            <span class="pc-name" :title="profile.username">{{ profile.username }}</span>
            <el-tag v-if="authStore.userId" size="small" effect="plain" class="uid-tag">
              UID {{ authStore.userId }}
            </el-tag>
          </div>
          <p class="pc-email">
            <el-icon><Message /></el-icon>
            {{ profile.email }}
          </p>
          <p class="pc-bio" :class="{ muted: !profile.bio }">
            {{ profile.bio || '这个人很神秘，还没有填写简介。' }}
          </p>
        </div>
      </section>

      <!-- ===== 下方：左侧透明菜单 + 右侧内容 ===== -->
      <div class="dash-body">
        <nav class="dash-menu">
          <button
            v-for="item in menuItems"
            :key="item.name"
            class="menu-item"
            :class="{ active: activeTab === item.name }"
            @click="switchTab(item.name)"
          >
            <el-icon class="menu-icon"><component :is="item.icon" /></el-icon>
            <span class="menu-label">{{ item.label }}</span>
          </button>

          <button class="menu-item menu-logout" @click="handleLogout">
            <el-icon class="menu-icon"><SwitchButton /></el-icon>
            <span class="menu-label">退出登录</span>
          </button>
        </nav>

        <main class="dash-content">
          <MyGames v-if="activeTab === 'games'" />
          <MyComments v-else-if="activeTab === 'comments'" />
          <MyLinks v-else-if="activeTab === 'links'" />
          <el-card v-else shadow="never" class="settings-card">
            <template #header>
              <span class="card-title">编辑资料</span>
            </template>
            <ProfileForm />
          </el-card>
        </main>
      </div>
    </template>
  </div>
</template>

<style scoped>
.profile-page {
  max-width: 1100px;
  margin: 0 auto;
  padding: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ========================================================
   卡片 A：头像 + 个人信息
   ======================================================== */
.profile-card {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 28px 32px;
  background: var(--fish-bg-2);
  border: 1px solid var(--fish-border);
  border-radius: var(--fish-radius);
  box-shadow: var(--fish-shadow);
}
.avatar-ring {
  flex-shrink: 0;
  padding: 3px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6a69e6, #8f8ef5);
  box-shadow: 0 8px 24px -8px rgba(124, 123, 242, 0.5);
}
.avatar-ring :deep(.el-avatar) {
  display: block;
  border-radius: 50%;
}
.pc-info {
  flex: 1;
  min-width: 0;
}
.pc-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.pc-name {
  font-size: 22px;
  font-weight: 800;
  letter-spacing: 0.3px;
  color: var(--fish-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.uid-tag {
  border-radius: 999px;
  flex-shrink: 0;
}
.pc-email {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin: 0 0 8px;
  font-size: 14px;
  color: var(--fish-accent);
  font-weight: 500;
}
.pc-bio {
  margin: 0;
  font-size: 14px;
  line-height: 1.8;
  color: var(--fish-text-2);
  word-break: break-word;
}
.pc-bio.muted {
  color: var(--fish-text-3);
}

/* ========================================================
   下方双栏：透明菜单 + 内容
   ======================================================== */
.dash-body {
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

/* ----- 左侧透明菜单（无卡片背景） ----- */
.dash-menu {
  position: sticky;
  top: 88px;
  flex-shrink: 0;
  width: 180px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 10px 14px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--fish-text-2);
  font-family: inherit;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}
.menu-item:hover {
  background: var(--fish-accent-soft);
  color: var(--fish-text-1);
}
.menu-item.active {
  color: var(--fish-accent);
  background: var(--fish-accent-soft);
  font-weight: 600;
}
.menu-icon {
  font-size: 16px;
  flex-shrink: 0;
}
.menu-logout {
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid var(--fish-border);
  color: var(--el-color-danger);
}
.menu-logout:hover {
  background: var(--el-color-danger-light-9);
  color: var(--el-color-danger);
}

/* ----- 右侧内容 ----- */
.dash-content {
  flex: 1;
  min-width: 0;
}

/* 设置卡片：标准实底卡片，与站点主体一致 */
.settings-card {
  --el-card-bg-color: var(--fish-bg-2);
  --el-card-border-color: var(--fish-border);
  background: var(--fish-bg-2);
  border: 1px solid var(--fish-border);
  border-radius: var(--fish-radius);
  box-shadow: var(--fish-shadow);
}
.card-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--fish-text-1);
}

/* ===== 响应式：窄屏折叠为上下结构 ===== */
@media (max-width: 768px) {
  .profile-card {
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 24px 20px;
  }
  .pc-head {
    justify-content: center;
  }
  .dash-body {
    flex-direction: column;
    gap: 16px;
  }
  .dash-menu {
    position: static;
    width: 100%;
    flex-direction: row;
    flex-wrap: wrap;
    justify-content: center;
  }
  .menu-item {
    width: auto;
  }
  .menu-logout {
    margin-top: 0;
    padding-top: 10px;
    border-top: none;
  }
}
</style>
