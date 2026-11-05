<script setup lang="ts">
import type { AddGalPayload, GalDetail } from '~/types'
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

const { data: gal, pending, error, refresh } = await useAsyncData<GalDetail>(
  () => `manage-gal-${id.value}`,
  () => api.get<GalDetail>(`/api/v1/galgame/${id.value}`),
  { server: false, watch: [id] },
)

const forbidden = computed(
  () => mounted.value && ready.value && Boolean(gal.value) && Boolean(user.value) && user.value!.id !== gal.value!.author_id,
)

const submitting = ref(false)

useHead({ title: '编辑游戏 · Fishmo' })

async function save(payload: AddGalPayload) {
  if (submitting.value || !gal.value) return
  submitting.value = true
  try {
    await api.put('/api/v1/galgame/edit', payload, { id: gal.value.id })
    toast.success('修改已保存')
    router.push(`/galgame/${gal.value.id}`)
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
      <span class="text-white/50">编辑游戏</span>
    </nav>

    <header class="mt-4">
      <p class="section-kicker">EDIT GAME</p>
      <h1 class="mt-2 text-2xl font-semibold text-white">编辑游戏信息</h1>
      <p class="mt-2 text-xs text-white/35">修改后会立即生效；已通过审核的作品保持公开状态。</p>
    </header>

    <div v-if="!mounted || (pending && !gal)" class="mt-6 animate-pulse space-y-4" aria-hidden="true">
      <div class="h-64 rounded-3xl border border-white/10 bg-white/[0.05]" />
    </div>

    <EmptyState
      v-else-if="forbidden"
      class="mt-8"
      title="没有编辑权限"
      description="只有作品发布者可以编辑这个页面。"
      image="/status/1.png"
    >
      <NuxtLink to="/manage" class="btn-ghost mt-5">返回个人中心</NuxtLink>
    </EmptyState>

    <EmptyState
      v-else-if="error && !gal"
      class="mt-8"
      title="无法加载游戏"
      :description="describeError(error)"
      image="/status/1.png"
      retryable
      @retry="refresh()"
    >
      <NuxtLink to="/manage" class="btn-ghost mt-5">返回个人中心</NuxtLink>
    </EmptyState>

    <GalgameForm
      v-else-if="gal"
      class="mt-6"
      mode="edit"
      :initial="gal"
      :submitting="submitting"
      @submit="save"
      @cancel="cancel"
    />
  </div>
</template>