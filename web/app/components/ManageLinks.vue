<script setup lang="ts">
import type { LinkItem, PageData } from '~/types'
import { describeError } from '~/utils/api'
import { formatDateTime } from '~/utils/date'

const api = useApi()
const toast = useToast()
const confirm = useConfirm()
const { user } = useAuth()

const page = ref(1)
const size = 10

const { data, pending, error, refresh } = await useAsyncData<PageData<LinkItem>>(
  () => `manage-links-${user.value?.id ?? 0}-${page.value}`,
  () =>
    api.get<PageData<LinkItem>>(`/api/v1/link/user/${user.value?.id}`, {
      page: page.value,
      size,
    }),
  {
    server: false,
    watch: [page, () => user.value?.id],
    default: () => ({ total: 0, items: [] }),
  },
)

const links = computed(() => data.value?.items ?? [])
const total = computed(() => data.value?.total ?? 0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / size)))

const dialogOpen = ref(false)
const editing = ref<LinkItem | null>(null)

function openEdit(link: LinkItem) {
  editing.value = link
  dialogOpen.value = true
}

async function remove(link: LinkItem) {
  const ok = await confirm.confirm({
    title: '删除链接',
    message: '删除后其他访客将无法再看到这条资源链接。',
    confirmText: '确认删除',
    danger: true,
  })
  if (!ok) return
  try {
    await api.del('/api/v1/link/delete', { link_id: link.id })
    toast.success('链接已删除')
    if (links.value.length === 1 && page.value > 1) page.value -= 1
    else refresh()
  } catch (err) {
    toast.error(describeError(err))
  }
}

function copy(text: string, label: string) {
  if (!import.meta.client) return
  navigator.clipboard
    .writeText(text)
    .then(() => toast.success(`${label}已复制`))
    .catch(() => toast.error('复制失败'))
}
</script>

<template>
  <section>
    <div class="flex flex-wrap items-center justify-between gap-3">
      <p class="text-[11px] text-white/35">
        共 <span class="tabular-nums text-white/60">{{ total }}</span> 条链接
      </p>
      <p class="text-[10px] text-white/25">链接编辑入口需要先在游戏详情页添加。</p>
    </div>

    <div v-if="pending && links.length === 0" class="mt-5 space-y-2">
      <div
        v-for="n in 3"
        :key="n"
        class="h-16 animate-pulse rounded-2xl border border-white/10 bg-white/[0.05]"
      />
    </div>

    <div v-else-if="error && links.length === 0" class="glass-panel mt-5 px-5 py-10 text-center">
      <p class="text-xs text-white/45">链接列表加载失败</p>
      <button type="button" class="btn-ghost mt-4 px-4 py-1.5" @click="refresh()">重试</button>
    </div>

    <div v-else-if="links.length === 0" class="glass-panel mt-5 px-5 py-12 text-center">
      <p class="text-xs text-white/40">你还没有分享过资源链接。</p>
      <NuxtLink to="/games" class="btn-ghost mt-5">去游戏页添加</NuxtLink>
    </div>

    <ul v-else class="mt-5 space-y-2">
      <li
        v-for="link in links"
        :key="link.id"
        class="glass-panel flex flex-wrap items-center gap-3 px-4 py-3"
      >
        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-2">
            <NuxtLink
              :to="`/galgame/${link.game_id}`"
              class="text-[10px] text-sky-200/60 transition hover:text-sky-100"
            >
              游戏 #{{ link.game_id }}
            </NuxtLink>
            <span v-if="link.category" class="text-[10px] text-white/35">{{ link.category }}</span>
            <span v-if="link.size != null" class="text-[10px] text-white/25">
              {{ link.size }} {{ link.size_unit }}
            </span>
            <span class="text-[10px] text-white/20">{{ formatDateTime(link.updated_at) }}</span>
          </div>
          <p class="mt-1 truncate text-xs text-white/55">{{ link.url }}</p>
          <p v-if="link.content" class="mt-0.5 line-clamp-1 text-[10px] text-white/30">
            {{ link.content }}
          </p>
          <button
            v-if="link.code"
            type="button"
            class="mt-1.5 rounded-full border border-amber-300/20 bg-amber-400/10 px-2 py-0.5 text-[10px] text-amber-100/80"
            @click="copy(link.code, '提取码')"
          >
            提取码 {{ link.code }}
          </button>
        </div>

        <div class="flex shrink-0 items-center gap-1.5">
          <a
            :href="link.url"
            target="_blank"
            rel="noopener noreferrer nofollow"
            class="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[10px] text-white/55 transition hover:bg-white/[0.1] hover:text-white"
          >
            打开
          </a>
          <button
            type="button"
            class="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-1.5 text-[10px] text-white/55 transition hover:bg-white/[0.1] hover:text-white"
            @click="openEdit(link)"
          >
            编辑
          </button>
          <button
            type="button"
            class="rounded-lg border border-rose-400/20 bg-rose-500/[0.08] px-3 py-1.5 text-[10px] text-rose-200/70 transition hover:bg-rose-500/15"
            @click="remove(link)"
          >
            删除
          </button>
        </div>
      </li>
    </ul>

    <PaginationBar v-model:page="page" :total-pages="totalPages" />

    <LinkDialog
      :open="dialogOpen"
      :game-id="editing?.game_id ?? 0"
      :link="editing"
      @close="dialogOpen = false"
      @saved="refresh()"
    />
  </section>
</template>