<script setup lang="ts">
import type { ArticleDetail, ArticlePayload } from '~/types'
import { describeError } from '~/utils/api'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const router = useRouter()
const api = useApi()
const toast = useToast()
const { user, ready } = useAuth()

const id = computed(() => Number(route.params.id))
const mounted = ref(false)
onMounted(() => {
  mounted.value = true
})

const { data: article, pending, error, refresh } = await useAsyncData<ArticleDetail>(
  () => `manage-article-${id.value}`,
  () => api.get<ArticleDetail>(`/api/v1/article/${id.value}`),
  { server: false, watch: [id] },
)

const forbidden = computed(
  () =>
    mounted.value &&
    ready.value &&
    Boolean(article.value) &&
    Boolean(user.value) &&
    user.value!.id !== article.value!.author_id &&
    !user.value!.is_admin,
)

const submitting = ref(false)

useHead({ title: '编辑文章 · Fishmo' })

async function save(payload: ArticlePayload) {
  if (submitting.value || !article.value) return
  submitting.value = true
  try {
    await api.put('/api/v1/article/edit', payload, { id: article.value.id })
    toast.success('文章已更新')
    router.push(`/article/${article.value.id}`)
  } catch (err) {
    toast.error(describeError(err))
  } finally {
    submitting.value = false
  }
}

function cancel() {
  router.back()
}
</script>

<template>
  <div class="mx-auto max-w-6xl px-4 pb-20 pt-10 sm:px-6">
    <nav class="flex items-center gap-2 text-[11px] text-white/30" aria-label="面包屑">
      <NuxtLink to="/manage" class="transition hover:text-white/70">个人中心</NuxtLink>
      <span>/</span>
      <NuxtLink :to="`/article/${id}`" class="transition hover:text-white/70">文章</NuxtLink>
      <span>/</span>
      <span class="text-white/50">编辑</span>
    </nav>

    <header class="mt-4">
      <p class="section-kicker">EDIT ARTICLE</p>
      <h1 class="mt-2 text-2xl font-semibold text-white">编辑文章</h1>
      <p class="mt-2 text-xs text-white/35">编辑不会自动保存草稿；离开前请确认已提交。</p>
    </header>

    <div v-if="!mounted || (pending && !article)" class="mt-6 animate-pulse" aria-hidden="true">
      <div class="h-96 rounded-3xl border border-white/10 bg-white/[0.05]" />
    </div>

    <EmptyState
      v-else-if="forbidden"
      class="mt-8"
      title="没有编辑权限"
      description="只有文章作者或管理员可以编辑这篇文章。"
      image="/status/1.png"
    >
      <NuxtLink to="/manage" class="btn-ghost mt-5">返回个人中心</NuxtLink>
    </EmptyState>

    <EmptyState
      v-else-if="error && !article"
      class="mt-8"
      title="无法加载文章"
      :description="describeError(error)"
      image="/status/1.png"
      retryable
      @retry="refresh()"
    >
      <NuxtLink to="/manage" class="btn-ghost mt-5">返回个人中心</NuxtLink>
    </EmptyState>

    <ArticleForm
      v-else-if="article"
      class="mt-6"
      mode="edit"
      :initial="article"
      :submitting="submitting"
      @submit="save"
      @cancel="cancel"
    />
  </div>
</template>