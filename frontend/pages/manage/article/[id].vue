<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import type { ArticlePublish } from '~/types'
import { useArticleDetail, editArticle, deleteArticle } from '~/composables/useArticle'
import { useAuthStore } from '~/stores/auth'
import { getErrDetail } from '~/utils/request'

// 登录守卫
definePageMeta({ middleware: 'auth' })

const route = useRoute()
const articleId = computed(() =>
  String(Array.isArray(route.params.id) ? route.params.id[0] : route.params.id),
)
const { data: article, pending, error, refresh } = useArticleDetail(articleId)

const auth = useAuthStore()
const isOwner = computed(
  () => !!article.value && auth.userId != null && article.value.author_id === auth.userId,
)
// 作者判断依赖客户端登录态（localStorage，SSR 时为空）：若直接按 isOwner 分支，
// 作者硬刷新 /manage/article/:id 时服务端渲染"非作者提示"而客户端水合为编辑表单，会水合不一致。
// 故整个作者相关区块等挂载后再渲染。
const isMounted = ref(false)
onMounted(() => {
  isMounted.value = true
})
const saving = ref(false)

/** 将 ArticleDetail 转换为 ArticleForm 可接受的 initial 格式 */
function detailToInitial(detail: NonNullable<ReturnType<typeof useArticleDetail>['data']['value']>): Partial<ArticlePublish> {
  return {
    title: detail.title,
    content: detail.content,
    cover: detail.cover || undefined,
    tag: detail.tag || [],
    category: detail.category || [],
    images: detail.images || [],
  }
}

async function handleSubmit(payload: ArticlePublish) {
  if (!article.value) return
  saving.value = true
  try {
    await editArticle(article.value.id, payload)
    ElMessage.success('保存成功')
    refresh()
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '保存失败'))
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  if (!article.value) return
  try {
    await ElMessageBox.confirm('确定删除该文章吗？删除后不可恢复。', '删除文章', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await deleteArticle(article.value.id)
    ElMessage.success('删除成功')
    navigateTo('/manage?tab=article')
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '删除失败'))
  }
}
</script>

<template>
  <div class="manage-article-page">
    <header class="page-head">
      <h2 class="page-title">管理文章 #{{ articleId }}</h2>
      <p class="page-desc">编辑文章信息。</p>
    </header>

    <el-skeleton v-if="pending" :rows="6" animated />
    <div v-else-if="error" class="empty-img">
      <img src="/status/1.png" alt="加载失败" />
      <p>加载失败，请稍后重试</p>
      <el-button size="small" @click="refresh">重试</el-button>
    </div>

    <template v-else-if="article">
      <el-alert
        v-if="isMounted && !isOwner"
        type="error"
        :closable="false"
        show-icon
        title="你不是该文章的作者，无法编辑。"
        class="mb"
      />

      <template v-else-if="isMounted">
        <!-- ===== 页面导航 ===== -->
        <div class="nav-bar">
          <el-button size="small" @click="navigateTo(`/article/${article.id}`)">
            <el-icon><ArrowLeft /></el-icon>
            返回详情
          </el-button>
        </div>

        <ArticleForm
          mode="edit"
          :initial="detailToInitial(article)"
          :submitting="saving"
          @submit="handleSubmit"
        />
        <div class="delete-zone">
          <el-button type="danger" plain @click="handleDelete">删除该文章</el-button>
        </div>
      </template>
    </template>
  </div>
</template>

<style scoped>
.manage-article-page {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.page-head {
  margin-bottom: 0;
}
.page-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 6px;
  font-size: 24px;
  font-weight: 800;
  letter-spacing: 0.01em;
  color: var(--fish-text-1);
}
.page-title::before {
  content: '';
  width: 4px;
  height: 18px;
  border-radius: 3px;
  background: var(--fish-accent);
}
.page-desc {
  margin: 0;
  font-size: 13px;
  color: var(--fish-text-3);
}
.mb {
  margin-bottom: 0;
}
.nav-bar {
  display: flex;
  gap: 8px;
}
.delete-zone {
  display: flex;
  justify-content: flex-end;
}
.empty-img {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 0;
}
.empty-img img {
  width: 240px;
  max-width: 70%;
  border-radius: 12px;
  opacity: 0.85;
}
.empty-img p {
  margin: 0;
  font-size: 15px;
  color: var(--fish-text-3);
}
</style>