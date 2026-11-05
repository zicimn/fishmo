<script setup lang="ts">
import type { LinkItem, PageData } from '~/types'
import { describeError } from '~/utils/api'
import { formatDateTime } from '~/utils/date'

const props = defineProps<{
  gameId: number
}>()

const api = useApi()
const toast = useToast()
const confirm = useConfirm()
const { user } = useAuth()
const { openAuth } = useAuthDialog()

const page = ref(1)
const size = 10
const mounted = ref(false)
onMounted(() => {
  mounted.value = true
})

const { data, pending, error, refresh } = await useAsyncData<PageData<LinkItem>>(
  () => `links-${props.gameId}-${page.value}`,
  () =>
    api.get<PageData<LinkItem>>(`/api/v1/link/${props.gameId}`, {
      page: page.value,
      size,
    }),
  {
    watch: [page, () => props.gameId],
    default: () => ({ total: 0, items: [] }),
  },
)

const links = computed(() => data.value?.items ?? [])
const total = computed(() => data.value?.total ?? 0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / size)))

const dialogOpen = ref(false)
const editing = ref<LinkItem | null>(null)

watch(
  () => props.gameId,
  () => {
    page.value = 1
  },
)

function openAdd() {
  if (!mounted.value || !user.value) {
    openAuth('login')
    return
  }
  editing.value = null
  dialogOpen.value = true
}

function openEdit(link: LinkItem) {
  editing.value = link
  dialogOpen.value = true
}

function canManage(link: LinkItem): boolean {
  return mounted.value && Boolean(user.value) && user.value!.id === link.author_id
}

function sizeLabel(link: LinkItem): string {
  if (link.size == null) return ''
  return `${link.size} ${link.size_unit ?? ''}`.trim()
}

async function copyText(text: string, label: string) {
  if (!import.meta.client) return
  try {
    await navigator.clipboard.writeText(text)
    toast.success(`${label}已复制`)
  } catch {
    toast.error('复制失败，请手动选择文本')
  }
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
    refresh()
  } catch (err) {
    toast.error(describeError(err))
  }
}
</script>

<template>
  <section class="mt-10" aria-labelledby="links-heading">
    <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 id="links-heading" class="text-sm font-medium tracking-wide text-white/70">
          资源链接
          <span v-if="total" class="ml-1 text-[11px] text-white/30">{{ total }}</span>
        </h2>
        <p class="mt-1 text-[11px] text-white/30">由社区成员分享，请自行甄别文件来源。</p>
      </div>
      <button type="button" class="btn-ghost px-4 py-2" @click="openAdd">
        + 添加链接
      </button>
    </div>

    <div v-if="pending && links.length === 0" class="space-y-2" aria-hidden="true">
      <div
        v-for="n in 2"
        :key="n"
        class="h-16 animate-pulse rounded-2xl border border-white/10 bg-white/[0.05]"
      />
    </div>

    <div
      v-else-if="error && links.length === 0"
      class="glass-panel px-5 py-8 text-center"
    >
      <p class="text-xs text-white/45">链接暂时加载失败</p>
      <button type="button" class="btn-ghost mt-4 px-4 py-1.5" @click="refresh()">
        重试
      </button>
    </div>

    <div
      v-else-if="links.length === 0"
      class="glass-panel px-5 py-10 text-center"
    >
      <p class="text-xs text-white/40">还没有人分享资源链接。</p>
      <button
        v-if="mounted && user"
        type="button"
        class="mt-4 text-[11px] text-sky-200/70 transition hover:text-white"
        @click="openAdd"
      >
        成为第一个分享的人 →
      </button>
    </div>

    <ul v-else class="space-y-2">
      <li
        v-for="link in links"
        :key="link.id"
        class="group glass-panel flex flex-wrap items-center gap-3 px-4 py-3.5 transition hover:border-white/20"
      >
        <span
          class="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-white/[0.06] text-xs text-white/50 ring-1 ring-white/10"
          aria-hidden="true"
        >
          {{ (link.category || '链').charAt(0) }}
        </span>

        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-x-2 gap-y-1">
            <a
              :href="link.url"
              target="_blank"
              rel="noopener noreferrer nofollow"
              class="truncate text-xs font-medium text-sky-200/90 transition hover:text-sky-100"
            >
              {{ link.category || '资源链接' }}
            </a>
            <span v-if="sizeLabel(link)" class="text-[10px] text-white/30">
              {{ sizeLabel(link) }}
            </span>
            <span class="text-[10px] text-white/20">by {{ link.author.username }}</span>
          </div>
          <p v-if="link.content" class="mt-1 line-clamp-2 text-[11px] leading-relaxed text-white/40">
            {{ link.content }}
          </p>
          <p class="mt-1 text-[10px] text-white/20">
            {{ formatDateTime(link.updated_at) }}
          </p>
        </div>

        <div class="flex shrink-0 flex-wrap items-center gap-1.5">
          <button
            v-if="link.code"
            type="button"
            class="rounded-full border border-amber-300/20 bg-amber-400/10 px-2.5 py-1 text-[10px] text-amber-100/80 transition hover:bg-amber-400/15"
            title="点击复制提取码"
            @click="copyText(link.code, '提取码')"
          >
            提取码 {{ link.code }}
          </button>
          <a
            :href="link.url"
            target="_blank"
            rel="noopener noreferrer nofollow"
            class="rounded-full border border-white/10 bg-white/[0.05] px-3 py-1 text-[10px] text-white/60 transition hover:bg-white/[0.12] hover:text-white"
          >
            打开
          </a>
          <template v-if="canManage(link)">
            <button
              type="button"
              class="rounded-full px-2 py-1 text-[10px] text-white/30 transition hover:text-white/80"
              @click="openEdit(link)"
            >
              编辑
            </button>
            <button
              type="button"
              class="rounded-full px-2 py-1 text-[10px] text-white/30 transition hover:text-rose-200"
              @click="remove(link)"
            >
              删除
            </button>
          </template>
        </div>
      </li>
    </ul>

    <PaginationBar v-model:page="page" :total-pages="totalPages" />

    <LinkDialog
      :open="dialogOpen"
      :game-id="gameId"
      :link="editing"
      @close="dialogOpen = false"
      @saved="refresh()"
    />
  </section>
</template>