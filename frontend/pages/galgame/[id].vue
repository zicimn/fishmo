<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { useGalgameDetail, deleteGalgame } from '~/composables/useGalgame'
import { useAuthStore } from '~/stores/auth'
import { getErrDetail } from '~/utils/request'
import { extractCoverAccent } from '~/utils/color'

const route = useRoute()
const gameId = computed(() =>
  String(Array.isArray(route.params.id) ? route.params.id[0] : route.params.id),
)
const numericId = computed(() => Number(gameId.value))

const { data: game, pending, error, refresh } = useGalgameDetail(gameId)

const auth = useAuthStore()
const isOwner = computed(
  () => !!game.value && auth.userId != null && game.value.author_id === auth.userId,
)

// 添加游戏链接：右上角按钮 → 弹窗；未登录先跳登录页（携带 redirect 便于登录后回跳）
const linkAddVisible = ref(false)
const linkListRef = ref<{ refresh: () => void } | null>(null)

function openLinkAdd() {
  if (!auth.isLoggedIn()) {
    navigateTo(`/user?redirect=${encodeURIComponent(route.fullPath)}`)
    return
  }
  linkAddVisible.value = true
}

async function handleDelete() {
  if (!game.value) return
  try {
    await ElMessageBox.confirm('确定删除该游戏吗？删除后不可恢复。', '删除游戏', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await deleteGalgame(game.value.id)
    ElMessage.success('删除成功')
    navigateTo('/')
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '删除失败'))
  }
}

// 日期展示：后端返回 ISO 字符串
function formatDate(value?: string | null): string {
  if (!value) return '-'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleString('zh-CN', { hour12: false })
}

// 三名称展示：过滤空串且不与主名（name）重复
const subNames = computed(() => {
  if (!game.value) return []
  const main = game.value.name
  const set = new Set<string>()
  for (const n of [game.value.jp_name, game.value.en_name, game.value.cn_name]) {
    if (n && n !== main) set.add(n)
  }
  return [...set]
})

// 仅客户端可恢复登录态（localStorage）：作者操作区若直接按 isOwner 分支，SSR 首帧
// （无登录态，隐藏）与客户端水合（已登录，显示）会不一致，故先等挂载完成再按登录态显示。
const isMounted = ref(false)
const showOwnerActions = computed(() => isMounted.value && isOwner.value)

// 仅客户端：从封面提取辅助色写入 --cover-accent（CSS 变量），SSR 首帧使用默认紫蓝，
// 避免水合不匹配；提取失败时静默兜底为品牌主色（见 theme.css）。
onMounted(() => {
  isMounted.value = true
  const cover = game.value?.cover
  if (!cover) return
  extractCoverAccent(cover).then((c) => {
    if (c) document.documentElement.style.setProperty('--cover-accent', c)
  })
})
</script>

<template>
  <div class="detail-page">
    <el-skeleton v-if="pending" :rows="6" animated />
    <el-result
      v-else-if="error"
      icon="error"
      title="加载失败"
      sub-title="详情接口可能未返回（后端未跑通或游戏不存在）"
    >
      <template #extra>
        <el-button @click="refresh">重试</el-button>
      </template>
    </el-result>

    <template v-else-if="game">
      <!-- ===== 影院式 Hero：大封面背景 + 前景信息，主视觉为大图而非大按钮 ===== -->
      <section class="hero">
        <el-image :src="game.cover" fit="cover" class="hero-bg" loading="eager" />
        <div class="hero-scrim" />
        <div class="hero-inner">
          <div class="hero-cover-wrap">
            <el-image :src="game.cover" fit="cover" class="hero-cover" loading="eager">
              <template #error>
                <div class="hero-cover-fallback">无封面</div>
              </template>
            </el-image>
          </div>

          <div class="hero-body">
            <div class="hero-tags">
              <span v-if="game.category" class="hero-tag">{{ game.category }}</span>
              <span v-for="(p, i) in game.platfrom" :key="i" class="hero-tag">{{ p }}</span>
            </div>

            <h1 class="hero-title">{{ game.name }}</h1>

            <p v-if="subNames.length" class="hero-names">
              <span v-for="(n, i) in subNames" :key="i">{{ n }}</span>
            </p>

            <div class="hero-meta">
              <span class="hero-author">
                <el-avatar :size="22" :src="game.author_avatar || undefined">
                  {{ game.author_name.charAt(0).toUpperCase() || 'U' }}
                </el-avatar>
                {{ game.author_name }}
              </span>
              <span class="hero-stat">
                <el-icon><View /></el-icon>
                {{ game.views }} 浏览
              </span>
              <span class="hero-stat">
                <el-icon><Star /></el-icon>
                {{ game.likes }} 点赞
              </span>
              <span class="hero-stat">
                <el-icon><CollectionTag /></el-icon>
                {{ game.favorite }} 收藏
              </span>
              <span class="hero-stat">更新：{{ formatDate(game.update_at) }}</span>
            </div>

            <div v-if="showOwnerActions" class="owner-actions">
              <el-button type="primary" @click="navigateTo(`/manage/${game.id}`)">编辑游戏</el-button>
              <el-button type="danger" plain @click="handleDelete">删除游戏</el-button>
            </div>
          </div>
        </div>
      </section>

      <!-- ===== 主内容 + 信息侧栏 ===== -->
      <div class="detail-layout">
        <main class="detail-main">
          <!-- 游戏简介 -->
          <section class="block">
            <h2 class="block-title">游戏简介</h2>
            <p class="content">{{ game.content || '暂无简介' }}</p>
          </section>

          <!-- 截图画廊 -->
          <section v-if="game.images?.length" class="block">
            <h2 class="block-title">游戏截图</h2>
            <div class="gallery">
              <el-image
                v-for="(img, i) in game.images"
                :key="i"
                :src="img"
                :preview-src-list="game.images"
                :initial-index="i"
                fit="cover"
                class="gallery-img"
                lazy
              />
            </div>
          </section>

          <!-- 资源链接：信息式列表，非巨型下载 CTA；右上角提供添加链接入口 -->
          <section class="block">
            <div class="block-head">
              <h2 class="block-title">资源链接</h2>
              <el-button size="small" type="primary" plain @click="openLinkAdd">
                <el-icon><Plus /></el-icon>
                添加游戏链接
              </el-button>
            </div>
            <LinkList ref="linkListRef" :game-id="numericId" />
            <LinkAddDialog
              v-model="linkAddVisible"
              :game-id="numericId"
              @success="linkListRef?.refresh()"
            />
          </section>

          <!-- 评论 -->
          <section class="block">
            <h2 class="block-title">评论</h2>
            <CommentList :game-id="numericId" />
          </section>
        </main>

        <aside class="detail-side">
          <el-card shadow="never" class="side-card">
            <h3 class="side-title">游戏信息</h3>
            <dl class="side-list">
              <div v-if="game.category" class="side-row">
                <dt>分类</dt>
                <dd>{{ game.category }}</dd>
              </div>
              <div v-if="game.platfrom?.length" class="side-row">
                <dt>平台</dt>
                <dd>
                  <span v-for="(p, i) in game.platfrom" :key="i" class="side-chip">{{ p }}</span>
                </dd>
              </div>
              <div v-if="game.company?.length" class="side-row">
                <dt>制作公司</dt>
                <dd>
                  <span v-for="(c, i) in game.company" :key="i" class="side-chip">{{ c }}</span>
                </dd>
              </div>
              <div v-if="game.tag?.length" class="side-row">
                <dt>标签</dt>
                <dd>
                  <span v-for="(t, i) in game.tag" :key="i" class="side-chip">{{ t }}</span>
                </dd>
              </div>
              <div class="side-row">
                <dt>更新时间</dt>
                <dd>{{ formatDate(game.update_at) }}</dd>
              </div>
            </dl>
          </el-card>

          <el-card shadow="never" class="side-card">
            <h3 class="side-title">数据</h3>
            <div class="side-stats">
              <div class="side-stat">
                <el-icon><View /></el-icon>
                <span class="side-stat-num">{{ game.views }}</span>
                <span class="side-stat-label">浏览</span>
              </div>
              <div class="side-stat">
                <el-icon><Star /></el-icon>
                <span class="side-stat-num">{{ game.likes }}</span>
                <span class="side-stat-label">点赞</span>
              </div>
              <div class="side-stat">
                <el-icon><CollectionTag /></el-icon>
                <span class="side-stat-num">{{ game.favorite }}</span>
                <span class="side-stat-label">收藏</span>
              </div>
            </div>
          </el-card>
        </aside>
      </div>
    </template>
  </div>
</template>

<style scoped>
.detail-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

/* ========================================================
   影院式 Hero
   ======================================================== */
.hero {
  position: relative;
  border-radius: var(--fish-radius);
  overflow: hidden;
  border: 1px solid var(--fish-border);
  isolation: isolate;
}

.hero-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: -2;
  filter: blur(2px) brightness(0.55);
  transform: scale(1.06);
}

.hero-scrim {
  position: absolute;
  inset: 0;
  z-index: -1;
  background: linear-gradient(
    90deg,
    rgba(11, 11, 15, 0.94) 0%,
    rgba(11, 11, 15, 0.72) 45%,
    rgba(11, 11, 15, 0.3) 100%
  );
}

.hero-inner {
  display: flex;
  gap: 28px;
  align-items: center;
  padding: 36px;
  min-height: 340px;
}

.hero-cover-wrap {
  flex-shrink: 0;
  width: 200px;
}

.hero-cover {
  width: 200px;
  height: 280px;
  border-radius: 10px;
  display: block;
  box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.7);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

.hero-cover-fallback {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--fish-bg-2);
  color: var(--fish-text-3);
  font-size: 13px;
  border-radius: 10px;
}

.hero-body {
  flex: 1;
  min-width: 0;
}

.hero-tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.hero-tag {
  padding: 3px 10px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.18);
  color: rgba(255, 255, 255, 0.92);
  font-size: 12px;
  font-weight: 600;
}

.hero-title {
  margin: 0 0 8px;
  font-size: 32px;
  font-weight: 800;
  line-height: 1.25;
  color: #f5f5f5;
}

.hero-names {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  margin: 0 0 16px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 14px;
}

.hero-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  color: rgba(255, 255, 255, 0.78);
  font-size: 14px;
}

.hero-author {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.hero-stat {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.owner-actions {
  margin-top: 20px;
  display: flex;
  gap: 12px;
}

/* ========================================================
   主内容 + 侧栏（桌面双栏）
   ======================================================== */
.detail-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 280px;
  gap: 24px;
  align-items: start;
}

.detail-main {
  display: flex;
  flex-direction: column;
  gap: 24px;
  min-width: 0;
}

.block {
  background: var(--fish-bg-2);
  border: 1px solid var(--fish-border);
  border-radius: var(--fish-radius);
  padding: 24px;
}

.block-title {
  margin: 0 0 14px;
  font-size: 17px;
  font-weight: 700;
  color: var(--fish-text-1);
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

.block-title::before {
  content: '';
  width: 4px;
  height: 16px;
  border-radius: 3px;
  background: var(--cover-accent, var(--fish-accent));
  flex-shrink: 0;
}

/* 区块标题行：标题居左、操作按钮居右上角 */
.block-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}
.block-head .block-title {
  margin: 0;
}

.content {
  margin: 0;
  font-size: 15px;
  line-height: 1.9;
  color: var(--fish-text-2);
  white-space: pre-wrap;
  word-break: break-word;
}

.gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 12px;
}

.gallery-img {
  width: 100%;
  aspect-ratio: 16 / 10;
  border-radius: 8px;
  cursor: zoom-in;
  transition: transform 0.2s ease;
}

.gallery-img:hover {
  transform: scale(1.02);
}

/* 信息侧栏 */
.detail-side {
  position: sticky;
  top: 76px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.side-card {
  border-radius: 10px;
}

.side-title {
  margin: 0 0 14px;
  font-size: 15px;
  font-weight: 700;
  color: var(--fish-text-1);
}

.side-list {
  margin: 0;
}

.side-row {
  display: flex;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--fish-border);
  font-size: 13px;
}

.side-row:last-child {
  border-bottom: none;
}

.side-row dt {
  flex-shrink: 0;
  width: 64px;
  color: var(--fish-text-3);
}

.side-row dd {
  margin: 0;
  color: var(--fish-text-2);
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  word-break: break-word;
}

.side-chip {
  padding: 2px 8px;
  border-radius: 6px;
  background: var(--fish-bg);
  border: 1px solid var(--fish-border);
  font-size: 12px;
}

.side-stats {
  display: flex;
  justify-content: space-between;
}

.side-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  flex: 1;
  color: var(--fish-text-3);
  font-size: 12px;
}

.side-stat-num {
  font-size: 18px;
  font-weight: 700;
  color: var(--fish-text-1);
}

/* ========================================================
   响应式：1024 平板折叠 / 390 移动
   ======================================================== */
@media (max-width: 1024px) {
  .detail-layout {
    grid-template-columns: 1fr;
  }

  .detail-side {
    position: static;
    order: -1;
  }
}

@media (max-width: 560px) {
  .hero-inner {
    flex-direction: column;
    align-items: flex-start;
    padding: 24px 20px;
    min-height: auto;
  }

  .hero-cover-wrap {
    width: 140px;
  }

  .hero-cover {
    width: 140px;
    height: 196px;
  }

  .hero-title {
    font-size: 24px;
  }

  .block {
    padding: 18px;
  }

  .gallery {
    grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  }
}
</style>
