<script setup lang="ts">
import type { AdminUser, PageData } from '~/types'
import { describeError } from '~/utils/api'
import { formatDate } from '~/utils/date'

const api = useAdminApi()
const toast = useToast()
const confirm = useConfirm()
const { user: me } = useAdminAuth()

useHead({ title: '用户管理 · Fishmo 管理端' })

const keywordInput = ref('')
const keyword = ref('')
const page = ref(1)
const size = 12

const { data, pending, error, refresh } = await useAsyncData<PageData<AdminUser>>(
  () => `admin-users-${keyword.value}-${page.value}`,
  () =>
    api.get<PageData<AdminUser>>('/api/admin/control/Users', {
      page: page.value,
      size,
      keyword: keyword.value || undefined,
    }),
  {
    watch: [keyword, page],
    default: () => ({ total: 0, items: [] }),
  },
)

const users = computed(() => data.value?.items ?? [])
const total = computed(() => data.value?.total ?? 0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / size)))

function applySearch() {
  page.value = 1
  keyword.value = keywordInput.value.trim()
}

function clearSearch() {
  keywordInput.value = ''
  applySearch()
}

async function toggleStatus(target: AdminUser) {
  if (target.is_admin) return
  const enable = target.status !== 1

  if (!enable) {
    const ok = await confirm.confirm({
      title: '禁用账号',
      message: `禁用「${target.username}」后，该账号无法登录和发布内容，其已发布的内容仍会保留。`,
      confirmText: '确认禁用',
      danger: true,
    })
    if (!ok) return
  }

  try {
    await api.put('/api/admin/control/UserStatus', undefined, {
      user_id: target.id,
      status: enable,
    })
    toast.success(enable ? '账号已启用' : '账号已禁用')
    refresh()
  } catch (err) {
    toast.error(describeError(err))
  }
}
</script>

<template>
  <div class="mx-auto max-w-6xl">
    <header class="flex flex-wrap items-end justify-between gap-4">
      <div>
        <p class="section-kicker">MEMBERS</p>
        <h2 class="mt-2 text-xl font-semibold text-white">用户管理</h2>
        <p class="mt-1.5 text-xs text-white/35">查看注册用户，禁用违规账号。</p>
      </div>
      <p class="text-[11px] text-white/30">
        共 <span class="tabular-nums text-white/55">{{ total }}</span> 位用户
      </p>
    </header>

    <form class="mt-5 flex flex-wrap gap-2" @submit.prevent="applySearch">
      <input
        v-model="keywordInput"
        type="search"
        maxlength="50"
        placeholder="搜索用户名或邮箱…"
        class="input-base w-full max-w-xs"
      />
      <button type="submit" class="btn-primary px-4 py-2">搜索</button>
      <button
        v-if="keyword"
        type="button"
        class="btn-ghost px-4 py-2"
        @click="clearSearch"
      >
        清除
      </button>
    </form>

    <div v-if="pending && users.length === 0" class="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="n in 6"
        :key="n"
        class="h-36 animate-pulse rounded-2xl border border-white/10 bg-white/[0.05]"
      />
    </div>

    <div v-else-if="error && users.length === 0" class="glass-panel mt-5 px-5 py-10 text-center">
      <p class="text-xs text-white/45">用户列表加载失败</p>
      <button type="button" class="btn-ghost mt-4 px-4 py-1.5" @click="refresh()">重试</button>
    </div>

    <div v-else-if="users.length === 0" class="glass-panel mt-5 px-5 py-12 text-center">
      <p class="text-xs text-white/35">
        {{ keyword ? `没有匹配「${keyword}」的用户。` : '还没有注册用户。' }}
      </p>
    </div>

    <ul v-else class="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      <li
        v-for="item in users"
        :key="item.id"
        class="glass-panel flex flex-col p-4 transition hover:border-white/20"
      >
        <div class="flex items-center gap-3">
          <img
            v-if="item.avatar"
            :src="item.avatar"
            :alt="item.username"
            class="h-10 w-10 rounded-full object-cover ring-1 ring-white/15"
          />
          <span
            v-else
            class="grid h-10 w-10 place-items-center rounded-full bg-gradient-to-br from-sky-500/30 to-fuchsia-500/30 text-xs text-white/80"
          >
            {{ item.username.charAt(0) }}
          </span>
          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-1.5">
              <p class="truncate text-xs font-medium text-white/85">{{ item.username }}</p>
              <span
                v-if="item.is_admin"
                class="rounded-full border border-sky-300/20 bg-sky-400/10 px-1.5 py-0.5 text-[9px] text-sky-100/80"
              >
                管理员
              </span>
              <span
                v-else-if="item.status !== 1"
                class="rounded-full border border-rose-400/20 bg-rose-500/10 px-1.5 py-0.5 text-[9px] text-rose-200/80"
              >
                已禁用
              </span>
              <span v-else class="text-[9px] text-emerald-200/50">正常</span>
            </div>
            <p class="mt-0.5 truncate text-[10px] text-white/30">{{ item.email }}</p>
          </div>
        </div>

        <p v-if="item.bio" class="mt-2.5 line-clamp-2 text-[10px] leading-relaxed text-white/30">
          {{ item.bio }}
        </p>

        <div class="mt-3 flex items-center gap-3 border-t border-white/5 pt-2.5 text-[10px] text-white/30">
          <span><span class="tabular-nums text-white/55">{{ item.gal_cnt }}</span> 游戏</span>
          <span><span class="tabular-nums text-white/55">{{ item.article_cnt }}</span> 文章</span>
          <span class="ml-auto">{{ formatDate(item.created_at) }} 加入</span>
        </div>

        <div class="mt-3">
          <span v-if="item.is_admin" class="text-[10px] text-white/20">
            {{ me?.id === item.id ? '当前登录账号' : '管理员账号不可禁用' }}
          </span>
          <button
            v-else
            type="button"
            class="w-full rounded-lg border py-1.5 text-[10px] transition"
            :class="
              item.status === 1
                ? 'border-rose-400/20 bg-rose-500/[0.08] text-rose-200/75 hover:bg-rose-500/15'
                : 'border-emerald-300/20 bg-emerald-400/10 text-emerald-100/80 hover:bg-emerald-400/15'
            "
            @click="toggleStatus(item)"
          >
            {{ item.status === 1 ? '禁用账号' : '启用账号' }}
          </button>
        </div>
      </li>
    </ul>

    <AdminPagination v-model:page="page" :total-pages="totalPages" :total="total" />
  </div>
</template>