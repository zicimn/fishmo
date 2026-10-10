<script setup lang="ts">
import { ElMessage } from 'element-plus'
import type { AddGal, EditGal, ArticlePublish } from '~/types'
import { addGalgame } from '~/composables/useGalgame'
import { publishArticle } from '~/composables/useArticle'
import { getErrDetail } from '~/utils/request'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const router = useRouter()

type TabName = 'galgame' | 'article'

const rawTab = route.query.tab
const rawTabStr = Array.isArray(rawTab) ? rawTab[0] : rawTab
const activeTab = ref<TabName>(rawTabStr === 'article' ? 'article' : 'galgame')

const submitting = ref(false)

async function handleGalSubmit(payload: AddGal | EditGal) {
  submitting.value = true
  try {
    const res = await addGalgame(payload as AddGal)
    ElMessage.success('发布成功')
    navigateTo(`/galgame/${res.id}`)
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '发布失败'))
  } finally {
    submitting.value = false
  }
}

async function handleArticleSubmit(data: ArticlePublish) {
  submitting.value = true
  try {
    const res = await publishArticle(data)
    ElMessage.success('文章发布成功')
    navigateTo(`/article/${res.id}`)
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '发布失败'))
  } finally {
    submitting.value = false
  }
}

function handleCancel() {
  navigateTo('/')
}
</script>

<template>
  <div class="publish-page">
    <!-- ===== Page Header ===== -->
    <header class="page-head">
      <h2 class="page-title">发布</h2>
      <p class="page-desc">分享你的游戏资讯与文章</p>
    </header>

    <!-- ===== Tab Bar ===== -->
    <div class="tab-bar">
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'galgame' }"
        @click="activeTab = 'galgame'"
      >
        <svg class="tab-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="6" width="20" height="12" rx="2"/>
          <path d="M6 12h4"/>
          <path d="M14 12h4"/>
          <path d="M10 10v4"/>
        </svg>
        发布游戏
      </button>
      <button
        class="tab-btn"
        :class="{ active: activeTab === 'article' }"
        @click="activeTab = 'article'"
      >
        <svg class="tab-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <polyline points="10 9 9 9 8 9"/>
        </svg>
        发布文章
      </button>
    </div>

    <!-- ===== Game Form ===== -->
    <div v-show="activeTab === 'galgame'" class="form-container">
      <GalgameForm
        mode="add"
        :submitting="submitting"
        @submit="handleGalSubmit"
        @cancel="handleCancel"
      />
    </div>

    <!-- ===== Article Form ===== -->
    <div v-show="activeTab === 'article'" class="form-container">
      <ArticleForm
        mode="add"
        :submitting="submitting"
        @submit="handleArticleSubmit"
        @cancel="handleCancel"
      />
    </div>
  </div>
</template>

<style scoped>
.publish-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 2rem 3rem;
  min-height: 100dvh;
}

.page-head {
  margin-bottom: 1.5rem;
}

.page-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 6px;
  font-size: 1.6rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--fish-text-1);
}

.page-title::before {
  content: '';
  width: 4px;
  height: 20px;
  border-radius: 3px;
  background: var(--fish-accent);
}

.page-desc {
  margin: 0 0 0 14px;
  font-size: 0.85rem;
  color: var(--fish-text-3);
}

/* ===== Tab Bar ===== */
.tab-bar {
  display: flex;
  gap: 0;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid var(--fish-border);
}

.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 20px;
  border: none;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: var(--fish-text-3);
  font-family: inherit;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s;
  margin-bottom: -1px;
}

.tab-btn:hover {
  color: var(--fish-text-1);
}

.tab-btn.active {
  color: var(--fish-accent);
  border-bottom-color: var(--fish-accent);
}

.tab-btn .tab-icon {
  opacity: 0.7;
}

.tab-btn.active .tab-icon {
  opacity: 1;
}

.form-container {
  animation: fadeIn 0.25s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .publish-page {
    padding: 1.25rem 1rem;
  }

  .page-title {
    font-size: 1.3rem;
  }
}

@media (max-width: 600px) {
  .tab-btn {
    flex: 1;
    justify-content: center;
    padding: 10px 12px;
    font-size: 0.85rem;
  }

  .tab-btn .tab-icon {
    display: none;
  }
}
</style>