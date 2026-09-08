<script setup lang="ts">
import { useLinkList } from '~/composables/useLink'
import { isSafeLink } from '~/utils/link'
import { formatLinkSize } from '~/utils/format'

const props = defineProps<{ gameId: number }>()
const { data, pending, error, refresh } = useLinkList(props.gameId)

// 暴露刷新方法：详情页新增链接成功后由父组件调用，让列表实时更新
defineExpose({ refresh })
</script>

<template>
  <section class="link-section">
    <h3 class="section-title">下载链接（{{ data?.total ?? 0 }}）</h3>

    <el-skeleton v-if="pending" :rows="3" animated />
    <el-alert
      v-else-if="error"
      title="链接加载失败，请稍后重试"
      type="error"
      :closable="false"
      show-icon
    />
    <ClientOnly v-else-if="!data?.items?.length">
      <!-- EP el-empty 内置 SVG 的 el-id 在 SSR/客户端各自计数，直接 SSR 会水合不一致，故空态插图仅客户端渲染 -->
      <el-empty description="暂无下载链接" :image-size="80" />
    </ClientOnly>
    <ul v-else class="link-list">
      <li v-for="(entry, idx) in data.items" :key="idx" class="link-item">
        <div class="link-main">
          <a
            v-if="isSafeLink(entry.item.url)"
            :href="entry.item.url"
            target="_blank"
            rel="noopener noreferrer"
            class="link-url"
          >
            <el-icon><Link /></el-icon>
            {{ entry.item.url }}
          </a>
          <span v-else class="link-url unsafe">{{ entry.item.url }}</span>
          <div v-if="entry.item.category || entry.item.size" class="link-badges">
            <el-tag v-if="entry.item.category" size="small" type="info">分类：{{ entry.item.category }}</el-tag>
            <el-tag v-if="entry.item.size" size="small" type="warning">大小：{{ formatLinkSize(entry.item.size, entry.item.size_unit) }}</el-tag>
          </div>
          <p v-if="entry.item.content" class="link-content">{{ entry.item.content }}</p>
        </div>
        <div class="link-account">
          <el-avatar :size="20" :src="entry.account.avatar || undefined">
            {{ entry.account.username.charAt(0).toUpperCase() || 'U' }}
          </el-avatar>
          <span class="name">{{ entry.account.username }}</span>
        </div>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.section-title {
  margin: 0 0 16px;
  font-size: 18px;
  font-weight: 700;
}
.link-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.link-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid rgba(24, 24, 27, 0.08);
  border-radius: 0.75rem;
  margin-bottom: 10px;
  background: #fafafa;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1),
    background 0.3s cubic-bezier(0.16, 1, 0.3, 1),
    border-color 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}
.link-item:hover {
  transform: translateY(-2px);
  background: #ffffff;
  border-color: var(--fish-accent-border);
}
html.dark .link-item {
  border-color: rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
}
html.dark .link-item:hover {
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.16);
}
.link-main {
  flex: 1;
  min-width: 0;
}
.link-url {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: var(--el-color-primary);
  text-decoration: none;
  word-break: break-all;
}
.link-url:hover {
  text-decoration: underline;
}
.link-url.unsafe,
.link-url.unsafe:hover {
  color: var(--el-text-color-regular);
  text-decoration: none;
  cursor: default;
}
.link-badges {
  margin-top: 8px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.link-content {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  line-height: 1.6;
}
.link-account {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}
.name {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
</style>
