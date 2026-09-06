import { defineNuxtPlugin } from '#app'
import ElementPlus, { ID_INJECTION_KEY, ZINDEX_INJECTION_KEY } from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn.mjs'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'

/**
 * Element Plus 全局注册（中文语言包）：
 * 全量注册对中后台管理站体积可接受，换取最稳的 SSR 兼容与模板可用性。
 * 同时补齐 SSR 所需的 ID / ZIndex provider，避免服务端渲染告警与 hydration 不一致。
 */
export default defineNuxtPlugin((nuxtApp) => {
  nuxtApp.vueApp.use(ElementPlus, { locale: zhCn })
  // 全局注册图标组件，模板中可直接使用 <el-icon><View /></el-icon>
  for (const [name, comp] of Object.entries(ElementPlusIconsVue)) {
    nuxtApp.vueApp.component(name, comp)
  }
  // SSR 注入：useId / useZIndex 需要这两个 provider
  nuxtApp.vueApp.provide(ID_INJECTION_KEY, { prefix: 1024, current: 0 })
  nuxtApp.vueApp.provide(ZINDEX_INJECTION_KEY, { current: 0 })
})
