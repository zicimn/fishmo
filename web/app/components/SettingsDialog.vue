<script setup lang="ts">
import { BACKGROUNDS, useAppearance } from '~/composables/useAppearance'

defineProps<{ open: boolean }>()
const emit = defineEmits<{ (e: 'close'): void }>()

const { user, isAdmin } = useAuth()
const {
  background,
  brightness,
  alpha,
  setBackground,
  setBrightness,
  setAlpha,
  reset,
} = useAppearance()

const runtime = useRuntimeConfig()
const route = useRoute()
const adminBase = computed(() => runtime.public.adminBase || 'http://localhost:3001')

const tab = ref<'appearance' | 'background'>('appearance')

function close() {
  emit('close')
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape') close()
}

watch(
  () => route.fullPath,
  () => close(),
)

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => window.removeEventListener('keydown', onKeydown))

watch(
  () => brightness.value,
  (value) => setBrightness(value),
)
watch(
  () => alpha.value,
  (value) => setAlpha(value),
)
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[95] overflow-y-auto bg-slate-950/70 px-4 py-10 backdrop-blur-sm"
      @click.self="close"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label="设置"
        class="mx-auto flex w-full max-w-2xl flex-col overflow-hidden rounded-3xl border border-white/10 bg-slate-900/90 shadow-[0_24px_80px_-24px_rgba(2,6,23,0.95)] backdrop-blur-2xl md:flex-row"
      >
        <!-- 左侧菜单 -->
        <aside class="flex shrink-0 flex-row gap-1 border-b border-white/10 p-3 md:w-44 md:flex-col md:border-b-0 md:border-r">
          <button
            v-for="item in ([
              { key: 'appearance', label: '外观' },
              { key: 'background', label: '背景' },
            ] as const)"
            :key="item.key"
            type="button"
            class="rounded-xl px-3 py-2 text-left text-xs transition"
            :class="
              tab === item.key
                ? 'bg-white/[0.1] text-white'
                : 'text-white/45 hover:bg-white/[0.05] hover:text-white/75'
            "
            @click="tab = item.key"
          >
            {{ item.label }}
          </button>

          <div class="hidden flex-1 md:block" />

          <NuxtLink
            v-if="isAdmin"
            :to="adminBase"
            target="_blank"
            class="mt-1 flex items-center justify-between rounded-xl border-t border-white/10 px-3 py-2 text-xs text-sky-100/70 transition hover:bg-white/[0.06] hover:text-white md:mt-2"
          >
            管理端
            <span aria-hidden="true">→</span>
          </NuxtLink>
        </aside>

        <!-- 内容区 -->
        <div class="min-w-0 flex-1 p-5 sm:p-6">
          <div class="flex items-start justify-between gap-4">
            <div>
              <p class="text-[10px] uppercase tracking-[0.3em] text-sky-200/50">Settings</p>
              <h2 class="mt-1.5 text-lg font-semibold text-white">
                {{ tab === 'appearance' ? '外观调节' : '背景主题' }}
              </h2>
            </div>
            <button
              type="button"
              aria-label="关闭"
              class="grid h-8 w-8 place-items-center rounded-full border border-white/10 bg-white/[0.06] text-white/50 transition hover:bg-white/[0.12] hover:text-white"
              @click="close"
            >
              ×
            </button>
          </div>

          <template v-if="tab === 'appearance'">
            <label class="mt-6 block">
              <span class="flex items-center justify-between text-[11px] text-white/45">
                <span>背景亮度</span>
                <span class="tabular-nums text-white/30">{{ brightness.toFixed(2) }}</span>
              </span>
              <input
                v-model.number="brightness"
                type="range"
                min="0.4"
                max="1.2"
                step="0.05"
                class="mt-2 w-full accent-sky-400"
              />
            </label>

            <label class="mt-5 block">
              <span class="flex items-center justify-between text-[11px] text-white/45">
                <span>深色遮罩浓度</span>
                <span class="tabular-nums text-white/30">{{ alpha.toFixed(2) }}</span>
              </span>
              <input
                v-model.number="alpha"
                type="range"
                min="0.2"
                max="0.85"
                step="0.05"
                class="mt-2 w-full accent-sky-400"
              />
            </label>

            <p class="mt-5 rounded-xl border border-white/5 bg-white/[0.03] px-3 py-2 text-[11px] leading-relaxed text-white/35">
              设置保存在当前浏览器。亮度调高、遮罩调低会让背景更清晰，但可能影响文字对比度。
            </p>

            <div class="mt-5 flex justify-end">
              <button type="button" class="btn-ghost" @click="reset">恢复默认</button>
            </div>
          </template>

          <template v-else>
            <div class="mt-5 grid grid-cols-3 gap-3">
              <button
                v-for="item in BACKGROUNDS"
                :key="item"
                type="button"
                class="group relative aspect-[4/3] overflow-hidden rounded-xl border transition"
                :class="
                  background === item
                    ? 'border-sky-300/60 ring-2 ring-sky-400/25'
                    : 'border-white/10 hover:border-white/30'
                "
                :aria-label="`使用背景 ${item}`"
                @click="setBackground(item)"
              >
                <img :src="item" alt="" loading="lazy" class="h-full w-full object-cover" />
                <span
                  v-if="background === item"
                  class="absolute right-1.5 top-1.5 grid h-5 w-5 place-items-center rounded-full bg-sky-400 text-[10px] font-bold text-slate-950"
                >
                  ✓
                </span>
              </button>
            </div>

            <p class="mt-5 rounded-xl border border-white/5 bg-white/[0.03] px-3 py-2 text-[11px] leading-relaxed text-white/35">
              背景图来自 <code class="text-white/50">public/background/</code>。修改后立即生效并保存在本地。
            </p>
          </template>
        </div>
      </div>
    </div>
  </Teleport>
</template>