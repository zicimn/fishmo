import tailwindcss from '@tailwindcss/vite'

// 两种后端地址（为什么 SSR 与浏览器要分开，见 app/composables/useApiBase.ts）：
// - 本地开发：前后端各自直连，后端 CORS 已放行 3000 / 3001；
// - 生产：浏览器走 nginx 同源的 /api，SSR 仍直连后端。
const API_BASE_LOCAL = 'http://127.0.0.1:8000'
const API_BASE_NGINX = '/api'

// Galgame 社区前台：需要 SEO，保留 SSR；管理端在 admin/ 独立应用（3001）。
export default defineNuxtConfig({
  compatibilityDate: '2026-10-31',
  devtools: { enabled: false },

  devServer: { port: 3000 },

  css: ['~/assets/css/main.css'],
  vite: { plugins: [tailwindcss()] },

  runtimeConfig: {
    apiBaseServer: API_BASE_LOCAL,
    public: {
      apiBase: API_BASE_LOCAL,
      adminBase: 'http://localhost:3001',
    },
  },

  $production: {
    runtimeConfig: {
      apiBaseServer: API_BASE_LOCAL,
      public: { apiBase: API_BASE_NGINX },
    },
  },

  app: {
    head: {
      title: 'Fishmo · Galgame 社区',
      htmlAttrs: { lang: 'zh-CN' },
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        {
          name: 'description',
          content: 'Fishmo — Galgame 信息发布社区与文章博客平台。',
        },
        { name: 'theme-color', content: '#020617' },
      ],
      link: [{ rel: 'icon', type: 'image/x-icon', href: '/favicon.ico' }],
    },
  },

  nitro: {
    // 背景图等静态资源较多，压缩后传输
    compressPublicAssets: true,
  },
})