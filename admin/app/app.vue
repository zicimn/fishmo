<template>
  <div class="relative min-h-screen">
    <div class="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      <div class="absolute inset-0 bg-slate-950" />
      <div class="absolute -left-40 -top-40 h-[28rem] w-[28rem] rounded-full bg-sky-500/[0.08] blur-3xl" />
      <div class="absolute -bottom-40 right-0 h-[30rem] w-[30rem] rounded-full bg-fuchsia-500/[0.06] blur-3xl" />
      <div
        class="absolute inset-0 opacity-[0.35]"
        style="background-image: radial-gradient(rgba(148,163,184,0.12) 1px, transparent 1px); background-size: 32px 32px;"
      />
    </div>

    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>

    <AdminToast />
    <AdminConfirm />
  </div>
</template>