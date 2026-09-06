<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { useAuthStore } from '~/stores/auth'
import { useColorMode } from '~/composables/useColorMode'

const auth = useAuthStore()
const { isDark, toggle } = useColorMode()

// token 仅存于 localStorage（见 stores/auth），SSR 读不到登录态，后端始终按“未登录”渲染。
// 若模板直接按 auth.token 分支，客户端恢复登录态后会与 SSR 首帧不一致，触发水合警告。
// 因此这里用 mounted 门控：挂载前（SSR 与客户端首帧）统一渲染“未登录”，挂载后再按真实 token 切换。
const isMounted = ref(false)
onMounted(() => {
  isMounted.value = true
})
const isLoggedIn = computed(() => !!auth.token)
const showProfile = computed(() => isMounted.value && isLoggedIn.value)
const showLogin = computed(() => !isMounted.value || !isLoggedIn.value)

const searchQuery = ref('')
const isNavOpen = ref(false)

// 侧边栏用户首字母（无头像时显示）
const userInitial = computed(() => (auth.username || 'U').charAt(0).toUpperCase())

function handleSearch() {
  if (!searchQuery.value.trim()) return
  // 后端列表接口暂无 keyword 搜索参数（仅 category 精确 / platform 枚举过滤），不虚构能力。
  // 待后端补充搜索接口后再接通。
  ElMessage.info('搜索功能需后端先补接口（列表接口暂无 keyword 参数）')
  searchQuery.value = ''
}

function handleLogout() {
  auth.logout()
  ElMessage.success('已退出登录')
  navigateTo('/')
}

function closeNav() {
  isNavOpen.value = false
}
</script>

<template>
  <div class="app-shell">
    <!-- ===== 固定顶栏导航 ===== -->
    <header class="topbar">
      <div class="topbar-inner">
        <NuxtLink to="/" class="brand" aria-label="fishmo 首页">
          <span class="brand-mark">
            <el-icon :size="16"><MagicStick /></el-icon>
          </span>
          <span class="brand-text">fishmo</span>
        </NuxtLink>

        <nav class="nav-links" @click="closeNav">
          <NuxtLink to="/" class="nav-link" exact-active-class="is-active">首页</NuxtLink>
          <NuxtLink to="/games" class="nav-link" exact-active-class="is-active">全部游戏</NuxtLink>
          <NuxtLink v-if="showProfile" to="/publish" class="nav-link" exact-active-class="is-active">
            发布游戏
          </NuxtLink>
          <NuxtLink v-if="showLogin" to="/user" class="nav-link" exact-active-class="is-active">
            登录 / 注册
          </NuxtLink>
        </nav>

        <div class="top-actions">
          <div class="search-box">
            <el-icon class="search-icon"><Search /></el-icon>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索游戏..."
              class="search-input"
              @keyup.enter="handleSearch"
            />
          </div>

          <button
            class="icon-btn"
            :title="isDark ? '切换亮色' : '切换暗色'"
            :aria-label="isDark ? '切换亮色' : '切换暗色'"
            @click="toggle"
          >
            <el-icon v-if="isDark"><Sunny /></el-icon>
            <el-icon v-else><Moon /></el-icon>
          </button>

          <template v-if="showProfile">
            <NuxtLink to="/user/profile" class="nav-profile">
              <el-avatar :size="30" :src="auth.avatar || undefined">{{ userInitial }}</el-avatar>
              <span class="nav-profile-name" :title="auth.username || ''">
                {{ auth.username || '我的主页' }}
              </span>
            </NuxtLink>
          </template>
          <NuxtLink v-else to="/user" class="btn-login">登录</NuxtLink>

          <button
            class="hamburger"
            :class="{ 'is-open': isNavOpen }"
            :aria-label="isNavOpen ? '收起菜单' : '展开菜单'"
            :aria-expanded="isNavOpen"
            @click="isNavOpen = !isNavOpen"
          >
            <span class="hamburger-bar" :class="{ 'is-open': isNavOpen }"></span>
            <span class="hamburger-bar" :class="{ 'is-open': isNavOpen }"></span>
            <span class="hamburger-bar" :class="{ 'is-open': isNavOpen }"></span>
          </button>
        </div>
      </div>
    </header>

    <!-- 移动端抽屉 -->
    <div v-if="isNavOpen" class="nav-mask" @click="closeNav" />
    <aside v-if="isNavOpen" class="nav-drawer">
      <nav class="drawer-links" @click="closeNav">
        <NuxtLink to="/" class="nav-link" exact-active-class="is-active">首页</NuxtLink>
        <NuxtLink to="/games" class="nav-link" exact-active-class="is-active">全部游戏</NuxtLink>
        <NuxtLink v-if="showProfile" to="/publish" class="nav-link" exact-active-class="is-active">
          发布游戏
        </NuxtLink>
        <NuxtLink v-if="showLogin" to="/user" class="nav-link" exact-active-class="is-active">
          登录 / 注册
        </NuxtLink>
        <button v-if="showProfile" class="drawer-logout" @click="handleLogout">退出登录</button>
      </nav>
    </aside>

    <!-- ===== 主内容 ===== -->
    <main class="content">
      <slot />
    </main>

    <footer class="layout-footer">
      <p>fishmo · 美少女游戏信息站</p>
    </footer>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100dvh;
  display: flex;
  flex-direction: column;
}

/* ========================================================
   固定顶栏
   ======================================================== */
.topbar {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 60px;
  background: rgba(11, 11, 15, 0.82);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--fish-border);
}

.topbar-inner {
  height: 100%;
  max-width: 1320px;
  margin: 0 auto;
  padding: 0 1.5rem;
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.brand {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  text-decoration: none;
  flex-shrink: 0;
}

.brand-mark {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, #6a69e6, #8f8ef5);
  color: #fff;
  box-shadow: 0 4px 12px -4px rgba(124, 123, 242, 0.5);
  flex-shrink: 0;
}

.brand-text {
  font-size: 1.1rem;
  font-weight: 800;
  letter-spacing: 0.01em;
  color: var(--fish-text-1);
  white-space: nowrap;
}

/* 导航链接 */
.nav-links {
  display: flex;
  align-items: center;
  gap: 4px;
}

.nav-link {
  padding: 7px 12px;
  border-radius: 8px;
  text-decoration: none;
  color: var(--fish-text-2);
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  transition: background-color 0.2s, color 0.2s;
}

.nav-link:hover {
  background: var(--fish-accent-soft);
  color: var(--fish-text-1);
}

.nav-link.is-active {
  background: var(--fish-accent-soft);
  color: var(--fish-accent);
  font-weight: 600;
}

/* 右侧操作区 */
.top-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 0.625rem;
  flex-shrink: 0;
}

.search-box {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 260px;
  height: 36px;
  padding: 0 0.75rem;
  background: var(--fish-bg-2);
  border: 1px solid var(--fish-border);
  border-radius: 999px;
  transition: border-color 0.2s, box-shadow 0.2s, background 0.2s;
}

.search-box:focus-within {
  border-color: var(--fish-accent);
  box-shadow: 0 0 0 3px var(--fish-accent-soft);
}

.search-icon {
  font-size: 15px;
  color: var(--fish-text-3);
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  min-width: 0;
  border: none;
  background: transparent;
  font-size: 0.875rem;
  color: var(--fish-text-1);
  outline: none;
  font-family: inherit;
}

.search-input::placeholder {
  color: var(--fish-text-3);
}

.icon-btn {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 999px;
  border: 1px solid var(--fish-border);
  background: var(--fish-bg-2);
  color: var(--fish-text-2);
  cursor: pointer;
  flex-shrink: 0;
  transition: color 0.2s, border-color 0.2s, background 0.2s;
}

.icon-btn:hover {
  color: var(--fish-accent);
  border-color: var(--fish-accent-border);
}

.icon-btn :deep(.el-icon) {
  font-size: 17px;
}

/* 登录态：头像 + 用户名 */
.nav-profile {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  height: 36px;
  padding: 0 8px 0 4px;
  border-radius: 999px;
  background: var(--fish-bg-2);
  border: 1px solid var(--fish-border);
  text-decoration: none;
  transition: border-color 0.2s;
}

.nav-profile:hover {
  border-color: var(--fish-accent-border);
}

.nav-profile-name {
  max-width: 110px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--fish-text-1);
}

.btn-login {
  display: inline-flex;
  align-items: center;
  height: 36px;
  padding: 0 1rem;
  border-radius: 999px;
  background: var(--fish-accent);
  color: #fff;
  font-size: 0.85rem;
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
  transition: background-color 0.2s;
}

.btn-login:hover {
  background: var(--fish-accent-strong);
}

/* 汉堡按钮 */
.hamburger {
  display: none;
  width: 36px;
  height: 36px;
  border: 1px solid var(--fish-border);
  border-radius: 8px;
  background: var(--fish-bg-2);
  cursor: pointer;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  flex-shrink: 0;
}

.hamburger-bar {
  display: block;
  width: 15px;
  height: 2px;
  border-radius: 2px;
  background: var(--fish-text-1);
  transform-origin: center;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.3s;
}

.hamburger-bar.is-open:nth-child(1) {
  transform: translateY(6px) rotate(45deg);
}

.hamburger-bar.is-open:nth-child(2) {
  opacity: 0;
  transform: scaleX(0);
}

.hamburger-bar.is-open:nth-child(3) {
  transform: translateY(-6px) rotate(-45deg);
}

/* ========================================================
   移动端抽屉
   ======================================================== */
.nav-mask {
  position: fixed;
  inset: 0;
  z-index: 110;
  background: rgba(0, 0, 0, 0.5);
}

.nav-drawer {
  position: fixed;
  top: 60px;
  right: 0;
  bottom: 0;
  z-index: 111;
  width: 260px;
  padding: 1rem;
  background: var(--fish-bg-2);
  border-left: 1px solid var(--fish-border);
  box-shadow: -12px 0 32px -16px rgba(0, 0, 0, 0.4);
  overflow-y: auto;
}

.drawer-links {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.drawer-links .nav-link {
  font-size: 15px;
  padding: 10px 12px;
}

.drawer-logout {
  margin-top: 12px;
  padding: 10px 12px;
  border: none;
  border-top: 1px solid var(--fish-border);
  border-radius: 0;
  background: none;
  text-align: left;
  color: var(--el-color-danger);
  font-size: 14px;
  font-family: inherit;
  cursor: pointer;
}

/* ========================================================
   内容 / 页脚
   ======================================================== */
.content {
  flex: 1;
  width: 100%;
  max-width: 1320px;
  margin: 0 auto;
  padding: 2rem 1.5rem 3rem;
}

.layout-footer {
  flex-shrink: 0;
  text-align: center;
  color: var(--fish-text-3);
  font-size: 13px;
  padding: 1.25rem 1rem;
  border-top: 1px solid var(--fish-border);
  background: var(--fish-bg);
}

.layout-footer p {
  margin: 0;
}

/* ========================================================
   响应式：1024 平板 / 390 移动
   ======================================================== */
@media (max-width: 1024px) {
  .nav-links {
    display: none;
  }

  .hamburger {
    display: inline-flex;
  }

  .search-box {
    width: 200px;
  }
}

@media (max-width: 560px) {
  .topbar-inner {
    padding: 0 1rem;
    gap: 0.75rem;
  }

  .nav-profile-name {
    display: none;
  }

  .nav-profile {
    width: 36px;
    padding: 0;
    justify-content: center;
  }

  .search-box {
    width: 130px;
  }

  .content {
    padding: 1.25rem 1rem 2.5rem;
  }
}
</style>
