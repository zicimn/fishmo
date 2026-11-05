<script setup lang="ts">
import type { FavoriteStatus, GalDetail } from '~/types'
import { describeError } from '~/utils/api'
import { formatDate, formatDateTime } from '~/utils/date'

const route = useRoute()
const api = useApi()
const toast = useToast()
const { user, isLoggedIn } = useAuth()
const { openAuth } = useAuthDialog()

const id = computed(() => Number(route.params.id))

const { data: gal, pending, error, refresh } = await useAsyncData<GalDetail>(
  () => `gal-${id.value}`,
  () => api.get<GalDetail>(`/api/v1/galgame/${id.value}`),
  { watch: [id] },
)

useHead(() => ({
  title: gal.value ? `${gal.value.name} · Fishmo` : '游戏详情 · Fishmo',
  meta: gal.value?.content
    ? [{ name: 'description', content: gal.value.content.slice(0, 120) }]
    : [],
}))

const mounted = ref(false)
onMounted(() => {
  mounted.value = true
})

const favorite = ref(false)
const favoriteCount = ref(0)
const favoriteBusy = ref(false)

watch(
  gal,
  (value) => {
    if (!value) return
    favorite.value = value.is_favorited
    favoriteCount.value = value.favorite ?? 0
  },
  { immediate: true },
)

onMounted(async () => {
  if (!isLoggedIn.value || !gal.value) return
  try {
    const status = await api.get<FavoriteStatus>('/api/v1/favorite/visit', { gal_id: id.value })
    favorite.value = status.favorited
    favoriteCount.value = status.count
  } catch {
    // 收藏状态探测失败不影响浏览
  }
})

async function toggleFavorite() {
  if (!mounted.value) return
  if (!isLoggedIn.value) {
    openAuth('login')
    return
  }
  if (favoriteBusy.value) return
  favoriteBusy.value = true
  try {
    if (favorite.value) {
      await api.del('/api/v1/favorite/remove', { gal_id: id.value })
      toast.success('已取消收藏')
    } else {
      await api.post('/api/v1/favorite/add', undefined, { gal_id: id.value })
      toast.success('已加入收藏')
    }
    const status = await api.get<FavoriteStatus>('/api/v1/favorite/visit', { gal_id: id.value })
    favorite.value = status.favorited
    favoriteCount.value = status.count
  } catch (err) {
    toast.error(describeError(err))
  } finally {
    favoriteBusy.value = false
  }
}

async function share() {
  if (!import.meta.client) return
  const url = window.location.href
  try {
    if (navigator.share) {
      await navigator.share({ title: gal.value?.name ?? 'Fishmo', url })
      return
    }
    await navigator.clipboard.writeText(url)
    toast.success('页面链接已复制')
  } catch {
    // 用户取消分享不提示
  }
}

const canEdit = computed(
  () => mounted.value && Boolean(user.value) && user.value!.id === gal.value?.author_id,
)

const lightboxOpen = ref(false)
const lightboxIndex = ref(0)
const screenshots = computed(() => gal.value?.images ?? [])
const lightboxImages = computed(() => {
  const value = gal.value
  if (!value) return []
  return [...new Set([value.cover, ...value.images].filter(Boolean))] as string[]
})

function openImage(index: number) {
  lightboxIndex.value = index
  lightboxOpen.value = true
}

function openScreenshot(image: string) {
  const index = lightboxImages.value.indexOf(image)
  openImage(index >= 0 ? index : 0)
}

const nameEntries = computed(() => {
  const value = gal.value
  if (!value) return []
  return [
    { label: '原名', value: value.name },
    { label: '中文名', value: value.cn_name },
    { label: '日文名', value: value.jp_name },
    { label: '英文名', value: value.en_name },
  ].filter((item) => item.value && item.value !== value.name)
})
</script>

<template>
  <div class="mx-auto max-w-6xl px-4 pb-20 pt-8 sm:px-6">
    <nav class="flex items-center gap-2 text-[11px] text-white/30" aria-label="面包屑">
      <NuxtLink to="/" class="transition hover:text-white/70">首页</NuxtLink>
      <span>/</span>
      <NuxtLink to="/games" class="transition hover:text-white/70">全部游戏</NuxtLink>
      <span>/</span>
      <span class="truncate text-white/50">{{ gal?.name ?? '详情' }}</span>
    </nav>

    <div
      v-if="pending && !gal"
      class="mt-6 grid animate-pulse gap-8 lg:grid-cols-[300px_minmax(0,1fr)]"
      aria-hidden="true"
    >
      <div class="aspect-[2/3] rounded-3xl border border-white/10 bg-white/[0.05]" />
      <div class="space-y-4 pt-2">
        <div class="h-8 w-2/3 rounded bg-white/10" />
        <div class="h-3 w-1/3 rounded bg-white/5" />
        <div class="h-24 w-full rounded-2xl bg-white/[0.04]" />
      </div>
    </div>

    <EmptyState
      v-else-if="error && !gal"
      class="mt-10"
      title="无法打开这个游戏"
      :description="describeError(error)"
      image="/status/1.png"
      retryable
      @retry="refresh()"
    >
      <NuxtLink to="/games" class="btn-ghost mt-5">返回游戏列表</NuxtLink>
    </EmptyState>

    <template v-else-if="gal">
      <div class="mt-6 grid gap-8 lg:grid-cols-[300px_minmax(0,1fr)] lg:items-start">
        <!-- 封面与操作 -->
        <aside class="lg:sticky lg:top-24">
          <div
            class="group relative mx-auto w-full max-w-[300px] overflow-hidden rounded-3xl border border-white/10 bg-white/[0.05] shadow-[0_30px_80px_-30px_rgba(2,6,23,1)]"
          >
            <img
              v-if="gal.cover"
              :src="gal.cover"
              :alt="gal.name"
              class="aspect-[2/3] w-full cursor-zoom-in object-cover transition duration-500 group-hover:scale-[1.02]"
              @click="openImage(0)"
            />
            <div
              v-else
              class="flex aspect-[2/3] items-center justify-center bg-gradient-to-br from-sky-500/30 to-fuchsia-500/30 text-6xl text-white/20"
              aria-hidden="true"
            >
              {{ gal.name.charAt(0) }}
            </div>
            <span
              v-if="!gal.status"
              class="absolute left-3 top-3 rounded-full border border-amber-300/25 bg-amber-400/15 px-2.5 py-1 text-[10px] text-amber-100/90 backdrop-blur-md"
            >
              待审核 / 未公开
            </span>
          </div>

          <div class="mx-auto mt-4 flex max-w-[300px] flex-col gap-2">
            <button
              type="button"
              class="inline-flex items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-medium transition disabled:opacity-50"
              :class="
                favorite
                  ? 'border-rose-300/30 bg-rose-500/15 text-rose-100 hover:bg-rose-500/20'
                  : 'border-white/10 bg-white/[0.06] text-white/70 hover:bg-white/[0.12] hover:text-white'
              "
              :disabled="favoriteBusy"
              @click="toggleFavorite"
            >
              <span aria-hidden="true">{{ favorite ? '♥' : '♡' }}</span>
              {{ favorite ? '已收藏' : '收藏' }}
              <span class="text-[10px] tabular-nums opacity-60">{{ favoriteCount }}</span>
            </button>

            <div class="flex gap-2">
              <button type="button" class="btn-ghost flex-1" @click="share">分享</button>
              <NuxtLink v-if="canEdit" :to="`/manage/${gal.id}`" class="btn-ghost flex-1">
                编辑
              </NuxtLink>
            </div>
          </div>
        </aside>

        <!-- 主体信息 -->
        <main class="min-w-0">
          <header>
            <div class="flex flex-wrap items-center gap-2">
              <span
                v-if="gal.category"
                class="rounded-full border border-sky-300/20 bg-sky-400/10 px-2.5 py-1 text-[10px] text-sky-100/80"
              >
                {{ gal.category }}
              </span>
              <span
                v-for="platform in gal.platfrom"
                :key="platform"
                class="rounded-full border border-white/10 bg-white/[0.05] px-2.5 py-1 text-[10px] text-white/50"
              >
                {{ platform }}
              </span>
            </div>

            <h1 class="mt-3 text-2xl font-semibold leading-tight text-white sm:text-4xl">
              {{ gal.name }}
            </h1>

            <dl v-if="nameEntries.length" class="mt-3 flex flex-wrap gap-x-5 gap-y-1.5">
              <div v-for="entry in nameEntries" :key="entry.label" class="flex items-baseline gap-1.5 text-[11px]">
                <dt class="text-white/25">{{ entry.label }}</dt>
                <dd class="text-white/55">{{ entry.value }}</dd>
              </div>
            </dl>

            <div class="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-[11px] text-white/35">
              <span class="inline-flex items-center gap-1.5">
                <img
                  v-if="gal.author_avatar"
                  :src="gal.author_avatar"
                  alt=""
                  class="h-4 w-4 rounded-full object-cover ring-1 ring-white/10"
                />
                <NuxtLink :to="`/user/${gal.author_id}`" class="transition hover:text-white/70">
                  {{ gal.author_name }}
                </NuxtLink>
              </span>
              <span class="tabular-nums">{{ gal.views }} 次浏览</span>
              <span class="tabular-nums">{{ gal.favorite }} 人收藏</span>
              <time :datetime="gal.updated_at">更新于 {{ formatDate(gal.updated_at) }}</time>
            </div>
          </header>

          <section v-if="gal.company.length || gal.tag.length" class="mt-6 glass-panel p-4">
            <div v-if="gal.company.length" class="flex flex-wrap items-baseline gap-2">
              <span class="text-[10px] uppercase tracking-[0.2em] text-white/25">制作公司</span>
              <span v-for="company in gal.company" :key="company" class="text-xs text-white/60">
                {{ company }}
              </span>
            </div>
            <div v-if="gal.tag.length" class="mt-3 flex flex-wrap items-center gap-1.5">
              <span class="mr-1 text-[10px] uppercase tracking-[0.2em] text-white/25">TAGS</span>
              <span
                v-for="tag in gal.tag"
                :key="tag"
                class="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 text-[10px] text-white/45"
              >
                # {{ tag }}
              </span>
            </div>
          </section>

          <section class="mt-8">
            <h2 class="text-sm font-medium tracking-wide text-white/70">游戏简介</h2>
            <div
              v-if="gal.content"
              class="mt-3 whitespace-pre-line text-sm leading-8 text-white/60"
            >
              {{ gal.content }}
            </div>
            <p v-else class="mt-3 text-xs text-white/30">发布者还没有填写简介。</p>
          </section>

          <section v-if="screenshots.length" class="mt-8">
            <div class="flex items-baseline justify-between">
              <h2 class="text-sm font-medium tracking-wide text-white/70">游戏截图</h2>
              <span class="text-[10px] text-white/25">{{ screenshots.length }} 张</span>
            </div>
            <div class="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-3">
              <button
                v-for="(image, index) in screenshots"
                :key="`${image}-${index}`"
                type="button"
                class="group relative aspect-[16/10] overflow-hidden rounded-2xl border border-white/10 bg-white/[0.04]"
                @click="openScreenshot(image)"
              >
                <img
                  :src="image"
                  alt=""
                  loading="lazy"
                  class="h-full w-full object-cover transition duration-500 group-hover:scale-105"
                />
                <span class="absolute inset-0 bg-slate-950/0 transition group-hover:bg-slate-950/20" />
              </button>
            </div>
          </section>

          <LinkList :game-id="gal.id" />

          <CommentList :target-id="gal.id" type="galgame" />

          <p class="mt-10 text-[10px] text-white/20">
            最后更新：{{ formatDateTime(gal.updated_at) }}
          </p>
        </main>
      </div>

      <ImageLightbox
        v-model:index="lightboxIndex"
        :open="lightboxOpen"
        :images="lightboxImages"
        @close="lightboxOpen = false"
      />
    </template>
  </div>
</template>