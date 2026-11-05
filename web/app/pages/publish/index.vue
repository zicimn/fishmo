<script setup lang="ts">
import type { AddGalPayload, ArticlePayload } from '~/types'
import { describeError } from '~/utils/api'

definePageMeta({ middleware: 'auth' })

const route = useRoute()
const router = useRouter()
const api = useApi()
const toast = useToast()

type Tab = 'game' | 'article'
const tab = computed<Tab>(() => (route.query.tab === 'article' ? 'article' : 'game'))

function switchTab(value: Tab) {
  router.replace({ query: { ...route.query, tab: value } })
}

const submitting = ref(false)
const articleForm = ref<{ clearDraft: () => void } | null>(null)

useHead(() => ({
  title: tab.value === 'article' ? '写文章 · Fishmo' : '发布游戏 · Fishmo',
}))

async function publishGame(payload: AddGalPayload) {
  if (submitting.value) return
  submitting.value = true
  try {
    const data = await api.post<{ id: number }>('/api/v1/galgame/add', payload)
    toast.success('发布成功，等待管理员审核')
    router.push(`/galgame/${data.id}`)
  } catch (err) {
    toast.error(describeError(err))
  } finally {
    submitting.value = false
  }
}

async function publishArticle(payload: ArticlePayload) {
  if (submitting.value) return
  submitting.value = true
  try {
    const data = await api.post<{ id: number }>('/api/v1/article/add', payload)
    articleForm.value?.clearDraft()
    toast.success('文章已发布')
    router.push(`/article/${data.id}`)
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
    <header>
      <p class="section-kicker">CREATE</p>
      <h1 class="mt-2 text-2xl font-semibold text-white sm:text-3xl">
        {{ tab === 'article' ? '写一篇文章' : '发布一部游戏' }}
      </h1>
      <p class="mt-2 text-xs text-white/35">
        {{
          tab === 'article'
            ? '文章发布后立即公开，支持 Markdown 与插图画廊。'
            : '游戏提交后需要管理员审核，通过后才会出现在公开列表中。'
        }}
      </p>
    </header>

    <div class="mt-6 inline-flex rounded-xl border border-white/10 bg-white/[0.04] p-1">
      <button
        type="button"
        class="rounded-lg px-5 py-2 text-xs transition"
        :class="tab === 'game' ? 'bg-white/[0.12] text-white' : 'text-white/40 hover:text-white/70'"
        @click="switchTab('game')"
      >
        发布游戏
      </button>
      <button
        type="button"
        class="rounded-lg px-5 py-2 text-xs transition"
        :class="tab === 'article' ? 'bg-white/[0.12] text-white' : 'text-white/40 hover:text-white/70'"
        @click="switchTab('article')"
      >
        写文章
      </button>
    </div>

    <div class="mt-6">
      <GalgameForm
        v-if="tab === 'game'"
        mode="add"
        :submitting="submitting"
        @submit="publishGame"
        @cancel="cancel"
      />
      <ArticleForm
        v-else
        ref="articleForm"
        mode="add"
        :submitting="submitting"
        @submit="publishArticle"
        @cancel="cancel"
      />
    </div>
  </div>
</template>