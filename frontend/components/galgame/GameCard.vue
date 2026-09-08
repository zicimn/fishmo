<script setup lang="ts">
import type { GalItem } from '~/types'

defineProps<{ item: GalItem }>()
</script>

<template>
  <el-card class="game-card" shadow="never" :body-style="{ padding: '0' }">
    <NuxtLink :to="`/galgame/${item.id}`" class="card-link">
      <!-- 2:3 封面：美术优先，整卡可点；封面保持纯净，浏览量移入信息区 -->
      <div class="game-cover">
        <el-image :src="item.cover" fit="cover" class="cover-img" lazy>
          <template #error>
            <div class="cover-placeholder">
              <el-icon :size="26"><Picture /></el-icon>
              <span>无封面</span>
            </div>
          </template>
        </el-image>
      </div>

      <div class="game-info">
        <h3 class="game-name" :title="item.name">{{ item.name }}</h3>
        <div class="game-meta">
          <div class="game-author">
            <el-avatar :size="18" :src="item.avatar || undefined">
              {{ item.author.charAt(0).toUpperCase() || 'U' }}
            </el-avatar>
            <span class="author-name">{{ item.author }}</span>
          </div>
          <span class="game-views">
            <el-icon :size="12"><View /></el-icon>
            {{ item.views }}
          </span>
        </div>
      </div>
    </NuxtLink>
  </el-card>
</template>

<style scoped>
.game-card {
  height: 100%;
  border-radius: var(--fish-radius-sm);
  overflow: hidden;
  border-color: var(--fish-border);
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1),
    border-color 0.2s cubic-bezier(0.16, 1, 0.3, 1),
    box-shadow 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.game-card:hover {
  transform: translateY(-3px);
  border-color: var(--fish-accent-border);
  box-shadow: var(--fish-shadow-hover);
}

.card-link {
  display: flex;
  flex-direction: column;
  height: 100%;
  color: inherit;
  text-decoration: none;
}

/* 2:3 封面：纯净展示，hover 微缩放 + accent 底部光晕 */
.game-cover {
  position: relative;
  aspect-ratio: 2 / 3;
  overflow: hidden;
  background: var(--fish-bg-2);
}

.cover-img {
  width: 100%;
  height: 100%;
  display: block;
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.game-card:hover .cover-img {
  transform: scale(1.04);
}

/* hover 时封面底部 accent 光晕：视觉反馈增强 */
.game-cover::after {
  content: '';
  position: absolute;
  inset: 0;
  opacity: 0;
  transition: opacity 0.3s ease;
  background: linear-gradient(
    to top,
    rgba(143, 142, 245, 0.12) 0%,
    transparent 40%
  );
  pointer-events: none;
}

.game-card:hover .game-cover::after {
  opacity: 1;
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--fish-space-xs);
  color: var(--fish-text-3);
  font-size: var(--fish-text-sm);
}

/* 信息区：标题 + 作者/浏览量同行 */
.game-info {
  padding: var(--fish-space-sm) var(--fish-space-md) var(--fish-space-md);
  display: flex;
  flex-direction: column;
  gap: var(--fish-space-sm);
  flex: 1;
}

.game-name {
  margin: 0;
  font-size: var(--fish-text-base);
  font-weight: 600;
  line-height: var(--fish-leading-snug);
  color: var(--fish-text-1);
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  transition: color 0.2s;
}

.card-link:hover .game-name {
  color: var(--fish-accent);
}

/* 作者与浏览量同行：作者居左，浏览量居右 */
.game-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--fish-space-sm);
  min-width: 0;
}

.game-author {
  display: flex;
  align-items: center;
  gap: var(--fish-space-xs);
  min-width: 0;
  font-size: var(--fish-text-xs);
  color: var(--fish-text-3);
  overflow: hidden;
}

.author-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.game-views {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: var(--fish-text-xs);
  color: var(--fish-text-3);
  flex-shrink: 0;
}
</style>
