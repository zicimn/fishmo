import tailwindcss from '@tailwindcss/vite'

export default defineNuxtConfig({
  compatibilityDate: '2026-10-31',

  // 管理端是纯后台工具：关闭 SSR，登录态全部放在浏览器
  ssr: false,

  devServer: {
    port: 3001,
  },

  css: ['~/assets/css/main.css'],

  vite: {
    plugins: [tailwindcss()],
  },

  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://127.0.0.1:8000',
      siteBase: process.env.NUXT_PUBLIC_SITE_BASE || 'http://localhost:3000',
    },
  },

  app: {
    head: {
      title: 'Fishmo 管理端',
      htmlAttrs: { lang: 'zh-CN' },
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'robots', content: 'noindex, nofollow' },
      ],
    },
  },

  nitro: {
    compressPublicAssets: true,
  },
})