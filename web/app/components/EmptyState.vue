<script setup lang="ts">
withDefaults(
  defineProps<{
    title: string
    description?: string
    image?: string
    retryable?: boolean
  }>(),
  {
    description: '',
    image: '',
    retryable: false,
  },
)

const emit = defineEmits<{ (e: 'retry'): void }>()
</script>

<template>
  <div class="mx-auto flex max-w-xl flex-col items-center rounded-3xl border border-white/10 bg-white/[0.06] px-6 py-14 text-center backdrop-blur-2xl">
    <img
      v-if="image"
      :src="image"
      alt=""
      class="mb-5 w-56 max-w-[70%] rounded-2xl opacity-80"
    />
    <p class="text-sm text-white/65">{{ title }}</p>
    <p v-if="description" class="mt-2 max-w-md text-xs leading-relaxed text-white/35">
      {{ description }}
    </p>
    <slot />
    <button
      v-if="retryable"
      type="button"
      class="mt-6 rounded-full border border-white/15 bg-white/10 px-5 py-2 text-xs font-medium text-white/80 transition hover:bg-white/15 hover:text-white"
      @click="emit('retry')"
    >
      重试
    </button>
  </div>
</template>