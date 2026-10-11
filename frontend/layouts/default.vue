<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { useAuthStore } from '~/stores/auth'
import { SEARCH_OPTIONS, type SearchTypeValue } from '~/types'
import { api } from '~/utils/request'

const auth = useAuthStore()

// token 仅存于 localStorage（见 stores/auth），SSR 读不到登录态，后端始终按”未登录”渲染。
// 若模板直接按 auth.token 分支，客户端恢复登录态后会与 SSR 首帧不一致，触发水合警告。
// 因此这里用 mounted 门控：挂载前（SSR 与客户端首帧）统一渲染”未登录”，挂载后再按真实 token 切换。
const isMounted = ref(false)
onMounted(() => {
  isMounted.value = true
})
const isLoggedIn = computed(() => !!auth.token)
const showProfile = computed(() => isMounted.value && isLoggedIn.value)
const showLogin = computed(() => !isMounted.value || !isLoggedIn.value)
const showAdmin = computed(() => isMounted.value && isLoggedIn.value && auth.isAdmin)

const searchQuery = ref('')
const searchType = ref<SearchTypeValue>('name')
const searchOpen = ref(false)
const searchWrap = ref<HTMLElement | null>(null)
const isNavOpen = ref(false)

// 侧边栏用户首字母（无头像时显示）
const userInitial = computed(() => (auth.username || 'U').charAt(0).toUpperCase())

// ===== 显示设置面板 =====
const settingsOpen = ref(false)
const activeMenu = ref<'appearance' | 'background'>('appearance')
const brightness = ref(100)
const alphaVal = ref(30)
const shadowIntensity = ref(100)
const selectedBg = ref<string | null>(null)

// 设置面板关闭时重置状态
watch(settingsOpen, (open: boolean) => {
  if (!open) {
    activeMenu.value = 'appearance'
  }
})

// 点击"管理"菜单项：关闭设置面板并跳转到管理页面
function goToAdmin() {
  settingsOpen.value = false
  navigateTo('/admin')
}

// 静态发现 public/background/ 下的图片（SSR 安全，仅客户端生成 URL）
const bgImages = import.meta.glob<string>('/public/background/*.{jpg,jpeg,png,webp,avif}', {
  query: '?url',
  import: 'default',
  eager: true,
})
const bgList = computed(() => {
  const keys = Object.keys(bgImages).sort()
  return keys.map((k) => ({
    name: k.split('/').pop() || k,
    url: bgImages[k],
  }))
})

// 默认背景：2.png
const defaultBg = computed(() => {
  const found = bgList.value.find((img: { name: string; url: string }) => img.name === '2.png')
  return found?.url || null
})

function toggleSettings() {
  settingsOpen.value = !settingsOpen.value
}

function applyThemeSettings() {
  const root = document.documentElement
  const b = brightness.value / 100
  const a = alphaVal.value / 100
  const s = shadowIntensity.value / 100

  root.style.setProperty('--fish-brightness', String(b))
  root.style.setProperty('--fish-alpha', String(a))
  root.style.setProperty('--fish-shadow-intensity', String(s))

  // 始终深色模式
  root.style.setProperty(
    '--fish-shadow',
    `0 1px 2px rgba(0, 0, 0, ${0.6 * s}), 0 8px 24px -18px rgba(0, 0, 0, ${0.5 * s})`
  )
  root.style.setProperty(
    '--fish-shadow-hover',
    `0 1px 2px rgba(0, 0, 0, ${0.6 * s}), 0 16px 32px -20px rgba(0, 0, 0, ${0.55 * s})`
  )
  root.style.setProperty(
    '--fish-shadow-lg',
    `0 4px 8px rgba(0, 0, 0, ${0.06 * s}), 0 20px 40px -20px rgba(0, 0, 0, ${0.15 * s})`
  )
}

function saveThemeSettings() {
  try {
    localStorage.setItem('theme-brightness', String(brightness.value))
    localStorage.setItem('theme-alpha', String(alphaVal.value))
    localStorage.setItem('theme-shadow', String(shadowIntensity.value))
  } catch {
    /* localStorage 不可用时静默 */
  }
}

function applyBackground(url: string | null) {
  const root = document.documentElement
  if (url) {
    root.style.setProperty('--fish-bg-image', `url(${url})`)
  } else {
    root.style.setProperty('--fish-bg-image', 'none')
  }
}

function selectBg(url: string | null) {
  selectedBg.value = url
  applyBackground(url)
  try {
    localStorage.setItem('theme-bg', url || '')
  } catch { /* 静默 */ }
}

function toggleSearch() {
  searchOpen.value = !searchOpen.value
  if (searchOpen.value) {
    nextTick(() => {
      const input = searchWrap.value?.querySelector<HTMLInputElement>('.flyout-input')
      input?.focus()
    })
  }
}

function handleSearch() {
  const kw = searchQuery.value.trim()
  if (!kw) return
  navigateTo({
    path: '/games',
    query: { keyword: kw, search_type: searchType.value },
  })
  searchQuery.value = ''
  searchOpen.value = false
}

function handleClickOutside(e: MouseEvent) {
  if (searchWrap.value && !searchWrap.value.contains(e.target as Node)) {
    searchOpen.value = false
  }
  // 设置面板交由 el-dialog 自带的遮罩层关闭处理
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') {
    searchOpen.value = false
    // 设置面板交由 el-dialog 自带的 ESC 关闭处理
  }
}

onMounted(() => {
  // 恢复用户保存的显示设置
  try {
    const sb = localStorage.getItem('theme-brightness')
    if (sb) brightness.value = Number(sb)
    const sa = localStorage.getItem('theme-alpha')
    if (sa) alphaVal.value = Number(sa)
    const ss = localStorage.getItem('theme-shadow')
    if (ss) shadowIntensity.value = Number(ss)
    const sbg = localStorage.getItem('theme-bg')
    if (sbg) {
      selectedBg.value = sbg
      applyBackground(sbg)
    } else if (defaultBg.value) {
      // 无保存的背景设置时，使用默认背景 2.png
      selectedBg.value = defaultBg.value
      applyBackground(defaultBg.value)
    }
  } catch {
    /* localStorage 不可用时静默 */
  }
  applyThemeSettings()

  document.addEventListener('mousedown', handleClickOutside)
  document.addEventListener('keydown', handleKeydown)
})

onUnmounted(() => {
  document.removeEventListener('mousedown', handleClickOutside)
  document.removeEventListener('keydown', handleKeydown)
})

function handleLogout() {
  auth.logout()
  ElMessage.success('已退出登录')
  navigateTo('/')
}

async function goRandomGame() {
  try {
    const res = await api<{ msg: string; id: number | null }>('/api/v1/galgame/rvisit')
    if (res.id != null) {
      navigateTo(`/galgame/${res.id}`)
    } else {
      ElMessage.info('暂无公开游戏')
    }
  } catch {
    ElMessage.error('获取随机游戏失败')
  }
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
            <img src="/favicon.ico" alt="fishmo" class="brand-icon" />
          </span>
          <span class="brand-text">fishmo</span>
        </NuxtLink>

        <nav class="nav-links" @click="closeNav">
          <NuxtLink to="/" class="nav-link" exact-active-class="is-active">首页</NuxtLink>
          <NuxtLink to="/games" class="nav-link" exact-active-class="is-active">全部游戏</NuxtLink>
          <a class="nav-link nav-random" title="随机一游" @click.prevent="goRandomGame">
            <el-icon><Refresh /></el-icon>
            随机
          </a>
          <NuxtLink to="/articles" class="nav-link" exact-active-class="is-active">
            <el-icon><Document /></el-icon>
            文章
          </NuxtLink>
          <NuxtLink to="/about" class="nav-link" exact-active-class="is-active">关于</NuxtLink>
          <NuxtLink v-if="showProfile" to="/publish" class="nav-link" exact-active-class="is-active">
            发布
          </NuxtLink>
          <NuxtLink v-if="showLogin" to="/user" class="nav-link" exact-active-class="is-active">
            登录 / 注册
          </NuxtLink>
        </nav>

        <div class="top-actions">
          <!-- 搜索：小圆圈图标 → 点击展开悬浮搜索框 -->
          <div ref="searchWrap" class="search-wrap">
            <button
              class="icon-btn search-toggle"
              :class="{ 'is-active': searchOpen }"
              title="搜索"
              aria-label="搜索"
              @click="toggleSearch"
            >
              <el-icon><Search /></el-icon>
            </button>

            <Transition name="search-fade">
              <div v-if="searchOpen" class="search-flyout">
                <div class="search-flyout-inner">
                  <input
                    v-model="searchQuery"
                    type="text"
                    placeholder="搜索游戏..."
                    class="flyout-input"
                    @keyup.enter="handleSearch"
                  />
                  <el-select
                    v-model="searchType"
                    size="small"
                    class="flyout-select"
                    @keyup.enter="handleSearch"
                  >
                    <el-option
                      v-for="opt in SEARCH_OPTIONS"
                      :key="opt.value"
                      :label="opt.label"
                      :value="opt.value"
                    />
                  </el-select>
                  <button class="flyout-go" title="搜索" @click="handleSearch">
                    <el-icon><ArrowRight /></el-icon>
                  </button>
                </div>
              </div>
            </Transition>
          </div>

          <!-- 显示设置：齿轮图标 → 点击弹出居中悬浮面板 -->
          <div class="settings-wrap">
            <button
              class="icon-btn"
              :class="{ 'is-active': settingsOpen }"
              title="显示设置"
              aria-label="显示设置"
              @click="toggleSettings"
            >
              <el-icon><Setting /></el-icon>
            </button>

            <el-dialog
              v-model="settingsOpen"
              width="520px"
              align-center
              append-to-body
              :show-close="false"
              class="settings-dialog"
              destroy-on-close
            >
              <div class="settings-layout">
                <!-- 左侧菜单 -->
                <aside class="settings-sidebar">
                  <button
                    class="settings-menu-item"
                    :class="{ 'is-active': activeMenu === 'appearance' }"
                    @click="activeMenu = 'appearance'"
                  >
                    <el-icon><Brush /></el-icon>
                    外观
                  </button>
                  <button
                    class="settings-menu-item"
                    :class="{ 'is-active': activeMenu === 'background' }"
                    @click="activeMenu = 'background'"
                  >
                    <el-icon><Picture /></el-icon>
                    背景
                  </button>
                  <div v-if="showAdmin" class="settings-menu-divider" />
                  <button
                    v-if="showAdmin"
                    class="settings-menu-item settings-menu-item--admin"
                    @click="goToAdmin"
                  >
                    <el-icon><SetUp /></el-icon>
                    管理
                    <el-icon class="admin-arrow"><ArrowRight /></el-icon>
                  </button>
                </aside>

                <!-- 右侧内容 -->
                <div class="settings-content">
                  <template v-if="activeMenu === 'appearance'">
                    <h3 class="settings-content-title">外观</h3>

                    <div class="settings-item">
                      <div class="settings-label"><span>亮度增强</span></div>
                      <el-switch
                        :model-value="brightness > 100"
                        class="settings-switch"
                        @update:model-value="(v: boolean) => { brightness = v ? 150 : 100; applyThemeSettings(); saveThemeSettings() }"
                      />
                    </div>

                    <div class="settings-item">
                      <div class="settings-label">
                        <span>透明度</span>
                        <span class="settings-value">{{ alphaVal }}%</span>
                      </div>
                      <el-slider
                        v-model="alphaVal"
                        :min="0"
                        :max="100"
                        @input="applyThemeSettings"
                        @change="saveThemeSettings"
                      />
                    </div>

                    <div class="settings-item">
                      <div class="settings-label">
                        <span>阴影强度</span>
                        <span class="settings-value">{{ shadowIntensity }}%</span>
                      </div>
                      <el-slider
                        v-model="shadowIntensity"
                        :min="0"
                        :max="200"
                        @input="applyThemeSettings"
                        @change="saveThemeSettings"
                      />
                    </div>
                  </template>

                  <!-- 背景选择 -->
                  <template v-if="activeMenu === 'background'">
                    <h3 class="settings-content-title">背景</h3>
                    <div class="bg-grid">
                      <button
                        class="bg-thumb"
                        :class="{ 'is-active': selectedBg === null }"
                        @click="selectBg(null)"
                      >
                        <span class="bg-none-icon">无</span>
                      </button>
                      <button
                        v-for="img in bgList"
                        :key="img.name"
                        class="bg-thumb"
                        :class="{ 'is-active': selectedBg === img.url }"
                        @click="selectBg(img.url)"
                      >
                        <img :src="img.url" :alt="img.name" class="bg-thumb-img" />
                      </button>
                    </div>
                  </template>

                </div>
              </div>
            </el-dialog>
          </div>

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
        <a class="nav-link" href="#" @click.prevent="goRandomGame">
          <el-icon><Refresh /></el-icon>
          随机
        </a>
        <NuxtLink to="/articles" class="nav-link" exact-active-class="is-active" @click="closeNav">
          <el-icon><Document /></el-icon>
          文章
        </NuxtLink>
        <NuxtLink to="/about" class="nav-link" exact-active-class="is-active" @click="closeNav">关于</NuxtLink>
        <NuxtLink v-if="showProfile" to="/publish" class="nav-link" exact-active-class="is-active">
          发布
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
  background: rgba(11, 11, 15, var(--fish-alpha, 0.3));
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
  /* background: linear-gradient(135deg, #6a69e6, #8f8ef5); */
  background: transparent;
  color: #fff;
  /* box-shadow: 0 4px 12px -4px rgba(124, 123, 242, 0.5); */
  box-shadow: none;
  flex-shrink: 0;
}

.brand-icon {
  width:  30px;
  height: 30px;
  border-radius: 6px;
  display: block;
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

/* ===== 搜索：圆图标 + 悬浮飞出面板 ===== */
.search-wrap {
  position: relative;
}

.search-toggle {
  position: relative;
  z-index: 1;
}

.search-toggle.is-active {
  color: var(--fish-accent);
  border-color: var(--fish-accent-border);
  background: var(--fish-accent-soft);
}

.search-flyout {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 380px;
  z-index: 200;
  background: var(--fish-bg-overlay, var(--fish-bg-2));
  border: 1px solid var(--fish-border);
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45), 0 4px 12px rgba(0, 0, 0, 0.3);
  padding: 8px;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

.search-flyout-inner {
  display: flex;
  align-items: center;
  gap: 6px;
}

.flyout-input {
  flex: 1;
  min-width: 0;
  height: 36px;
  padding: 0 12px;
  border: 1px solid var(--fish-border);
  border-radius: 10px;
  background: var(--fish-bg);
  font-size: 0.875rem;
  font-family: inherit;
  color: var(--fish-text-1);
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.flyout-input:focus {
  border-color: var(--fish-accent);
  box-shadow: 0 0 0 3px var(--fish-accent-soft);
}

.flyout-input::placeholder {
  color: var(--fish-text-3);
}

.flyout-select {
  width: 100px;
  flex-shrink: 0;
}

.flyout-select :deep(.el-select__wrapper) {
  height: 36px;
  border-radius: 10px;
  border: 1px solid var(--fish-border);
  background: var(--fish-bg);
  box-shadow: none;
  padding: 0 8px;
  transition: border-color 0.2s;
}

.flyout-select :deep(.el-select__wrapper.is-hovering),
.flyout-select :deep(.el-select__wrapper:hover) {
  border-color: var(--fish-accent-border);
}

.flyout-select :deep(.el-select__wrapper.is-focused) {
  border-color: var(--fish-accent);
  box-shadow: 0 0 0 3px var(--fish-accent-soft);
}

.flyout-select :deep(.el-select__selected-item) {
  font-size: 0.8125rem;
  color: var(--fish-text-1);
}

.flyout-select :deep(.el-select__caret) {
  color: var(--fish-text-3);
  font-size: 14px;
}

.flyout-go {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  border: none;
  background: var(--fish-accent);
  color: #fff;
  cursor: pointer;
  flex-shrink: 0;
  font-size: 16px;
  transition: background-color 0.2s;
}

.flyout-go:hover {
  background: var(--fish-accent-strong);
}

/* 飞出面板过渡动画 */
.search-fade-enter-active,
.search-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}

.search-fade-enter-from,
.search-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

/* ===== 设置面板（el-dialog 覆盖） ===== */
.settings-wrap {
  position: relative;
}

.settings-wrap .is-active {
  color: var(--fish-accent);
  border-color: var(--fish-accent-border);
  background: var(--fish-accent-soft);
}

/* 覆盖 el-dialog 默认样式 */
.settings-dialog {
  background: var(--fish-bg-overlay, var(--fish-bg-2)) !important;
  border: 1px solid var(--fish-border) !important;
  border-radius: 16px !important;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.45), 0 4px 12px rgba(0, 0, 0, 0.3) !important;
  overflow: hidden;
}

.settings-dialog :deep(.el-dialog__header) {
  display: none;
}

.settings-dialog :deep(.el-dialog__body) {
  padding: 0;
}

/* 深色模式微光边框 */
.settings-dialog {
  box-shadow: 0 0 0 1px rgba(143, 142, 245, 0.08),
              0 12px 40px rgba(0, 0, 0, 0.45),
              0 4px 12px rgba(0, 0, 0, 0.3) !important;
}

.settings-layout {
  display: flex;
  width: 100%;
  min-height: 320px;
}

/* 左侧菜单 */
.settings-sidebar {
  width: 120px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 16px 8px;
  border-right: 1px solid var(--fish-border);
  background: rgba(0, 0, 0, 0.05);
}

.settings-layout {
  display: flex;
  width: 100%;
  min-height: 320px;
}

/* 左侧菜单 */
.settings-sidebar {
  width: 120px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 16px 8px;
  border-right: 1px solid var(--fish-border);
  background: var(--fish-bg);
}

.settings-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 10px 12px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--fish-text-2);
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
  text-align: left;
}

.settings-menu-item:hover {
  background: var(--fish-accent-soft);
  color: var(--fish-text-1);
}

.settings-menu-item.is-active {
  background: var(--fish-accent-soft);
  color: var(--fish-accent);
  font-weight: 600;
}

.settings-menu-item .el-icon {
  font-size: 16px;
  flex-shrink: 0;
}

/* 管理菜单项上方分隔线 */
.settings-menu-divider {
  height: 1px;
  margin: 6px 8px;
  background: var(--fish-border);
}

.settings-menu-item--admin {
  color: var(--el-color-warning);
}

.settings-menu-item--admin:hover {
  background: rgba(245, 158, 11, 0.08);
  color: var(--el-color-warning);
}

.admin-arrow {
  margin-left: auto;
  font-size: 14px;
  opacity: 0.6;
  transition: transform 0.2s, opacity 0.2s;
}

.settings-menu-item--admin:hover .admin-arrow {
  transform: translateX(2px);
  opacity: 1;
}

/* 右侧内容 */
.settings-content {
  flex: 1;
  padding: 20px 24px;
  overflow-y: auto;
}

.settings-content-title {
  margin: 0 0 20px;
  font-size: 15px;
  font-weight: 700;
  color: var(--fish-text-1);
}

.settings-item + .settings-item {
  margin-top: 18px;
}

.settings-label {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 13px;
  color: var(--fish-text-2);
}

.settings-value {
  font-size: 12px;
  color: var(--fish-text-3);
  font-variant-numeric: tabular-nums;
}

/* 设置面板内 el-slider 暗色适配 */
.settings-dialog :deep(.el-slider__runway) {
  height: 4px;
  background: var(--fish-border);
}

.settings-dialog :deep(.el-slider__bar) {
  height: 4px;
  background: var(--fish-accent);
}

.settings-dialog :deep(.el-slider__button) {
  width: 16px;
  height: 16px;
  border: 2px solid var(--fish-accent);
}

.settings-dialog :deep(.el-slider__button-wrapper) {
  width: 24px;
  height: 24px;
}

.settings-dialog :deep(.el-slider__button-wrapper:hover .el-slider__button),
.settings-dialog :deep(.el-slider__button-wrapper.hover .el-slider__button) {
  transform: scale(1.15);
}

/* 背景选择网格 */
.bg-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
}

.bg-thumb {
  position: relative;
  aspect-ratio: 16 / 10;
  border-radius: 8px;
  overflow: hidden;
  border: 2px solid var(--fish-border);
  background: var(--fish-bg);
  cursor: pointer;
  padding: 0;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.bg-thumb:hover {
  border-color: var(--fish-accent-border);
  box-shadow: 0 0 0 2px var(--fish-accent-soft);
}

.bg-thumb.is-active {
  border-color: var(--fish-accent);
  box-shadow: 0 0 0 2px var(--fish-accent-soft);
}

.bg-thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.bg-none-icon {
  display: grid;
  place-items: center;
  width: 100%;
  height: 100%;
  font-size: 13px;
  color: var(--fish-text-3);
  background: var(--fish-bg-2);
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

  .search-flyout {
    width: 340px;
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

  .search-flyout {
    width: calc(100vw - 32px);
    right: -8px;
  }

  .settings-dialog {
    width: calc(100vw - 32px) !important;
    max-width: 480px;
  }

  .settings-sidebar {
    width: 90px;
    padding: 12px 6px;
  }

  .settings-content {
    padding: 16px;
  }

  .content {
    padding: 1.25rem 1rem 2.5rem;
  }
}
</style>
