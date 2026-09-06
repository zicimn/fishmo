<script setup lang="ts">
import type { GalItem } from '~/types'

defineProps<{ item: GalItem }>()
</script>

<template>
  <el-card class="game-card" shadow="never" :body-style="{ padding: '0' }">
    <NuxtLink :to="`/galgame/${item.id}`" class="card-link">
      <!-- 2:3 封面：美术优先，整卡可点 -->
      <div class="game-cover">
        <el-image :src="item.cover" fit="cover" class="cover-img" lazy>
          <template #error>
            <div class="cover-placeholder">
              <el-icon :size="26"><Picture /></el-icon>
              <span>无封面</span>
            </div>
          </template>
        </el-image>
        <div class="cover-views">
          <el-icon :size="13"><View /></el-icon>
          {{ item.views }}
        </div>
      </div>

      <div class="game-info">
        <h3 class="game-name" :title="item.name">{{ item.name }}</h3>
        <div class="game-author">
          <el-avatar :size="20" :src="item.avatar || undefined">
            {{ item.author.charAt(0).toUpperCase() || 'U' }}
          </el-avatar>
          <span class="author-name">{{ item.author }}</span>
        </div>
      </div>
    </NuxtLink>
  </el-card>
</template>

<style scoped>
.game-card {
  height: 100%;
  border-radius: 10px;
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
  display: block;
  height: 100%;
  color: inherit;
  text-decoration: none;
}

/* 2:3 封面 */
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
  transition: transform 0.3s ease;
}

.game-card:hover .cover-img {
  transform: scale(1.04);
}

.cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  color: var(--fish-text-3);
  font-size: 13px;
}

.cover-views {
  position: absolute;
  right: 8px;
  bottom: 8px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 999px;
  background: rgba(11, 11, 15, 0.72);
  color: rgba(255, 255, 255, 0.9);
  font-size: 12px;
  font-weight: 500;
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
}

.game-info {
  padding: 12px 14px 14px;
}

.game-name {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.4;
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

.game-author {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
  font-size: 12px;
  color: var(--fish-text-3);
}

.author-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
