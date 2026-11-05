<script setup lang="ts">
const { open, mode, closeAuth } = useAuthDialog()
const route = useRoute()
const router = useRouter()

watch(
  () => open.value,
  (value) => {
    if (!import.meta.client) return
    document.body.style.overflow = value ? 'hidden' : ''
  },
)

onBeforeUnmount(() => {
  if (import.meta.client) document.body.style.overflow = ''
})

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && open.value) closeAuth()
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

async function onSuccess() {
  closeAuth()
  const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : ''
  // 只接受站内路径，避免被构造的 redirect 带去外站
  if (redirect.startsWith('/') && !redirect.startsWith('//')) {
    await router.replace(redirect)
    return
  }
  await refreshNuxtData()
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[100] overflow-y-auto overscroll-contain bg-slate-950/70 px-4 py-10 backdrop-blur-sm"
      @click.self="closeAuth"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="登录或注册"
        class="mx-auto w-full max-w-md rounded-3xl border border-white/10 bg-slate-900/85 p-6 shadow-[0_24px_80px_-24px_rgba(2,6,23,0.95)] backdrop-blur-2xl sm:p-8"
      >
        <div class="flex items-start justify-between gap-4">
          <div>
            <p class="text-[10px] uppercase tracking-[0.3em] text-sky-200/50">Account</p>
            <h2 class="mt-2 text-xl font-semibold tracking-tight text-white">
              {{ mode === 'login' ? '登录 Fishmo' : '注册一个账号' }}
            </h2>
            <p class="mt-1.5 text-xs leading-relaxed text-white/40">
              {{
                mode === 'login'
                  ? '评论、收藏与发布需要登录账号。'
                  : '注册后即可发布游戏、写文章并参与评论。'
              }}
            </p>
          </div>
          <button
            type="button"
            aria-label="关闭"
            class="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-white/10 bg-white/[0.06] text-white/50 transition hover:bg-white/[0.12] hover:text-white"
            @click="closeAuth"
          >
            <svg viewBox="0 0 20 20" fill="none" class="h-3.5 w-3.5" aria-hidden="true">
              <path
                d="M4 4l12 12M16 4L4 16"
                stroke="currentColor"
                stroke-width="1.6"
                stroke-linecap="round"
              />
            </svg>
          </button>
        </div>

        <AuthForm v-model:mode="mode" @success="onSuccess" />
      </div>
    </div>
  </Teleport>
</template>