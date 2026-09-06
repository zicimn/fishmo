// Nuxt 3 配置
export default defineNuxtConfig({
  devtools: { enabled: true },

  // 组件：关闭目录前缀，组件名直接用文件名（如 components/user/LoginForm.vue → <LoginForm />）。
  // Nuxt 默认会加上目录前缀（UserLoginForm），导致模板里的短名被当作未知自定义元素渲染成空标签。
  components: [
    {
      path: '~/components',
      pathPrefix: false,
    },
  ],

  // 模块：Pinia 状态管理
  modules: ['@pinia/nuxt'],

  // 全局样式：Element Plus 样式 → Element Plus 深色 css-vars → 自定义主题覆盖（后者覆盖前者）
  css: [
    'element-plus/dist/index.css',
    'element-plus/theme-chalk/dark/css-vars.css',
    '~/assets/css/theme.css',
  ],

  // 运行时配置：默认 baseURL 为空 = 请求发到 Nuxt 自身（同源 /api），由下方 Nitro 代理转发到后端，
  // 从而彻底规避浏览器跨域 CORS 问题。如确需浏览器直连后端，再设置 NUXT_PUBLIC_API_BASE 覆盖。
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || '',
    },
  },

  // API 代理（开发与生产构建都生效）：/api/** 转发到 FastAPI 后端。
  // 代理目标可用环境变量 NUXT_API_BASE 覆盖，默认 http://localhost:8000。
  // 注意：不要同时配置 nitro.devProxy，二者同指 /api 会在开发模式互相冲突、改写路径。
  routeRules: {
    '/api/**': {
      proxy: `${process.env.NUXT_API_BASE || 'http://localhost:8000'}/api/**`,
    },
  },

  typescript: {
    strict: true,
    // 构建时执行 vue-tsc 类型检查，保证交付代码无类型错误
    typeCheck: true,
  },

  app: {
    // 页面切换：仅淡入淡出 200ms（动画规则见 assets/css/theme.css）
    pageTransition: { name: 'page-fade', mode: 'out-in' },
    head: {
      title: 'fishmo · 美少女游戏信息站',
      // 深色为主（《fishmo 视觉定位》Dark 游戏门户）；浅色为可切换的次级主题。
      // 深色 class="dark" 挂在 <html> 上。SSR 首帧不带 dark（与客户端首帧一致避免水合不匹配）；
      // 下方内联脚本在 paint 前默认加 dark，仅当 localStorage 显式存 'light' 时才保持浅色。
      htmlAttrs: { lang: 'zh-CN' },
      meta: [
        { charset: 'utf-8' },
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'fishmo 美少女游戏（galgame）信息发布平台' },
        { name: 'theme-color', content: '#0b0b0f' },
      ],
      script: [
        {
          innerHTML:
            "(function(){try{var m=localStorage.getItem('fishmo-color-mode');if(m!=='light'){document.documentElement.classList.add('dark')}}catch(e){document.documentElement.classList.add('dark')}})()",
        },
      ],
      // 字体：Google Fonts（运行时浏览器加载，非构建期）；国内网络不可达时由 theme.css 的系统字体栈兜底
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+JP:wght@400;500;700&family=Noto+Sans+SC:wght@400;500;700&display=swap',
        },
      ],
    },
  },
})
