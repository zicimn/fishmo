<script setup lang="ts">
import { useArticleDetail } from '~/composables/useArticle'
import { getErrDetail } from '~/utils/request'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'

const route = useRoute()
const articleId = computed(() =>
  String(Array.isArray(route.params.id) ? route.params.id[0] : route.params.id),
)
const numericId = computed(() => Number(articleId.value))

const { data: article, pending, error, refresh } = useArticleDetail(articleId)

// ===== Markdown 渲染 =====
const md = new MarkdownIt({ html: true, linkify: true, typographer: true })

const renderedContent = computed(() => {
  if (!article.value?.content) return ''
  const html = md.render(article.value.content)
  // DOMPurify 仅在浏览器环境可用，SSR 阶段跳过消毒
  if (import.meta.server) return html
  return DOMPurify.sanitize(html)
})

function formatDate(value?: string | null): string {
  if (!value) return '-'
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return value
  return d.toLocaleString('zh-CN', { hour12: false })
}

</script>

<template>
  <div class="article-detail-page">
    <el-skeleton v-if="pending" :rows="6" animated />
    <div v-else-if="error" class="empty-img">
      <img src="/status/1.png" alt="加载失败" />
      <p>加载失败，请稍后重试</p>
      <el-button size="small" @click="refresh">重试</el-button>
    </div>

    <template v-else-if="article">
      <!-- ===== 单一内容卡片 ===== -->
      <div class="article-card">
        <!-- ===== 封面区（条件渲染）：16:9 横幅封面 ===== -->
        <div v-if="article.cover" class="cover-wrapper">
          <div class="cover-inner">
            <el-image
              :src="article.cover"
              fit="cover"
              class="cover-image"
              lazy
            />
          </div>
        </div>

        <!-- ===== 文章头部 ===== -->
        <div class="article-header">
          <div v-if="article.category?.length" class="header-tags">
            <span v-for="(c, i) in article.category" :key="i" class="header-tag">{{ c }}</span>
          </div>

          <h1 class="article-title">{{ article.title }}</h1>

          <!-- 统计数据行 -->
          <div class="meta-row">
            <span class="meta-item meta-author">
              <el-avatar :size="22" :src="article.author_avatar || undefined">
                {{ article.author_name.charAt(0).toUpperCase() || 'U' }}
              </el-avatar>
              {{ article.author_name }}
            </span>

            <span class="meta-item">
              <el-icon><View /></el-icon>
              {{ article.views }}
            </span>

            <span class="meta-item">
              <el-icon><ChatDotSquare /></el-icon>
              {{ article.comment_count }}
            </span>

            <span class="meta-item">
              发布于 {{ formatDate(article.created_at) }}
            </span>

            <span v-if="article.updated_at !== article.created_at" class="meta-item">
              更新于 {{ formatDate(article.updated_at) }}
            </span>
          </div>

          </div>

        <!-- ===== 内容正文（Markdown 渲染） ===== -->
        <div class="content-area">
          <div
            v-if="renderedContent"
            class="content-body"
            v-html="renderedContent"
          />
          <p v-else class="content-empty">暂无内容</p>
        </div>

        <!-- ===== 标签区 ===== -->
        <div v-if="article.tag?.length" class="tags-section">
          <div class="tag-list">
            <NuxtLink
              v-for="(t, i) in article.tag"
              :key="i"
              :to="`/articles?tag=${encodeURIComponent(t)}`"
              class="tag-link"
            >
              {{ t }}
            </NuxtLink>
          </div>
        </div>

        <!-- ===== 插图区 ===== -->
        <div v-if="article.images?.length" class="images-section">
          <h2 class="section-title">插图</h2>
          <div class="gallery">
            <el-image
              v-for="(img, i) in article.images"
              :key="i"
              :src="img"
              :preview-src-list="article.images"
              :initial-index="i"
              fit="cover"
              class="gallery-img"
              lazy
            />
          </div>
        </div>

        <!-- ===== 评论区 ===== -->
        <div class="comments-section">
          <CommentList :game-id="numericId" type="article" />
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.article-detail-page {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--fish-space-lg);
}

/* ===== 单一内容卡片 ===== */
.article-card {
  background: transparent;
  border: 1px solid var(--fish-border);
  border-radius: var(--fish-radius);
  box-shadow: var(--fish-shadow);
  overflow: hidden;
}

/* ===== 封面区：16:9 横幅封面 ===== */
.cover-wrapper {
  position: relative;
  border-bottom: 1px solid var(--fish-border);
  padding: 0;
}

.cover-inner {
  position: relative;
  width: 100%;
  aspect-ratio: 21 / 9;
  max-height: 380px;
  overflow: hidden;
  background: var(--fish-bg);
}

.cover-image {
  width: 100%;
  height: 100%;
  display: block;
}

/* 封面底部渐变遮罩：过渡到内容区 */
.cover-wrapper::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 48px;
  background: linear-gradient(to top, var(--fish-bg-1, #0B0B0F), transparent);
  pointer-events: none;
  z-index: 1;
}

/* ===== 文章头部 ===== */
.article-header {
  padding: var(--fish-space-xl) var(--fish-space-xl) 0;
  display: flex;
  flex-direction: column;
  gap: var(--fish-space-md);
}

.article-title {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  line-height: var(--fish-leading-tight);
  color: var(--fish-accent);
  text-align: center;
  letter-spacing: var(--fish-tracking-tight);
}

/* ===== 分类标签 ===== */
.header-tags {
  display: flex;
  gap: var(--fish-space-sm);
  flex-wrap: wrap;
  justify-content: center;
}

.header-tag {
  padding: 3px 10px;
  border-radius: 999px;
  background: var(--fish-accent-soft);
  border: 1px solid var(--fish-accent-border);
  color: var(--fish-accent);
  font-size: var(--fish-text-xs);
  font-weight: 600;
  line-height: 1.4;
}

/* ===== 统计数据行 ===== */
.meta-row {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: var(--fish-space-md);
  color: var(--fish-text-3);
  font-size: var(--fish-text-sm);
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.meta-author {
  color: var(--fish-text-2);
  gap: var(--fish-space-sm);
}

/* ===== 内容正文 ===== */
.content-area {
  padding: var(--fish-space-lg) var(--fish-space-xl);
}

.content-body {
  font-size: 16px;
  line-height: var(--fish-leading-relaxed);
  color: var(--fish-text-1);
  max-width: 85ch;
  margin: 0 auto;
  word-wrap: break-word;
  overflow-x: auto;
}

.content-empty {
  margin: 0;
  text-align: center;
  color: var(--fish-text-3);
  font-size: var(--fish-text-base);
  padding: var(--fish-space-2xl) 0;
}

/* ===== Prose 排版样式（:deep 穿透 v-html） ===== */

/* 段落 */
.content-body :deep(p) {
  margin: 0 0 1em;
  line-height: 1.8;
}

.content-body :deep(p:last-child) {
  margin-bottom: 0;
}

/* 标题 */
.content-body :deep(h1) {
  font-size: 24px;
  font-weight: 700;
  margin: 2em 0 0.75em;
  line-height: var(--fish-leading-tight);
  color: var(--fish-text-1);
  letter-spacing: var(--fish-tracking-tight);
}

.content-body :deep(h2) {
  font-size: 20px;
  font-weight: 700;
  margin: 1.75em 0 0.5em;
  line-height: var(--fish-leading-tight);
  color: var(--fish-text-1);
  letter-spacing: var(--fish-tracking-tight);
}

.content-body :deep(h3) {
  font-size: 18px;
  font-weight: 650;
  margin: 1.5em 0 0.4em;
  line-height: var(--fish-leading-snug);
  color: var(--fish-text-1);
}

.content-body :deep(h4) {
  font-size: 16px;
  font-weight: 650;
  margin: 1.25em 0 0.35em;
  line-height: var(--fish-leading-snug);
  color: var(--fish-text-1);
}

/* 粗体 / 斜体 */
.content-body :deep(strong) {
  font-weight: 700;
}

.content-body :deep(em) {
  font-style: italic;
}

/* 链接 */
.content-body :deep(a) {
  color: var(--fish-accent);
  text-decoration: none;
  transition: text-decoration 0.2s;
}

.content-body :deep(a:hover) {
  text-decoration: underline;
}

/* 无序列表 */
.content-body :deep(ul) {
  list-style: disc;
  padding-left: 1.5em;
  margin: 0 0 1em;
}

.content-body :deep(ul ul) {
  list-style: circle;
}

.content-body :deep(ul ul ul) {
  list-style: square;
}

/* 有序列表 */
.content-body :deep(ol) {
  list-style: decimal;
  padding-left: 1.5em;
  margin: 0 0 1em;
}

/* 列表项 */
.content-body :deep(li) {
  margin-bottom: 0.35em;
  line-height: 1.75;
}

.content-body :deep(li:last-child) {
  margin-bottom: 0;
}

/* 代码块 */
.content-body :deep(pre) {
  padding: 1em 1.25em;
  background: rgba(0, 0, 0, 0.2);
  border-radius: var(--fish-radius-sm);
  overflow-x: auto;
  margin: 0 0 1em;
  border: 1px solid var(--fish-border);
  line-height: 1.6;
}

/* 行内代码 */
.content-body :deep(code) {
  background: var(--fish-accent-soft);
  color: var(--fish-accent);
  padding: 0.2em 0.4em;
  border-radius: 4px;
  font-size: 0.875em;
  word-break: break-word;
}

/* 代码块内的代码（还原为无背景） */
.content-body :deep(pre code) {
  background: transparent;
  color: var(--fish-text-2);
  padding: 0;
  border-radius: 0;
  font-size: 0.9em;
  word-break: normal;
}

/* 块引用 */
.content-body :deep(blockquote) {
  border-left: 3px solid var(--fish-accent);
  padding: 0.5em 1em;
  margin: 1.5em 0;
  color: var(--fish-text-2);
  background: var(--fish-accent-soft);
  border-radius: 0 var(--fish-radius-sm) var(--fish-radius-sm) 0;
}

.content-body :deep(blockquote p:last-child) {
  margin-bottom: 0;
}

/* 水平线 */
.content-body :deep(hr) {
  margin: 2em 0;
  border: none;
  height: 1px;
  background: linear-gradient(
    to right,
    transparent,
    var(--fish-border-strong),
    transparent
  );
}

/* 图片 */
.content-body :deep(img) {
  max-width: 100%;
  border-radius: var(--fish-radius-sm);
  display: block;
  margin: 1.5em auto;
  height: auto;
}

/* 表格 */
.content-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0 0 1em;
  font-size: 0.95em;
}

.content-body :deep(th),
.content-body :deep(td) {
  border: 1px solid var(--fish-border);
  padding: 0.5em 0.75em;
  text-align: left;
}

.content-body :deep(th) {
  background: var(--fish-bg-2);
  font-weight: 650;
  color: var(--fish-text-1);
}

.content-body :deep(td) {
  color: var(--fish-text-2);
}

/* ===== 标签区 ===== */
.tags-section {
  padding: 0 var(--fish-space-lg) var(--fish-space-lg);
}

.tag-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--fish-space-sm);
}

.tag-link {
  padding: 4px 12px;
  border-radius: var(--fish-radius-xs);
  background: var(--fish-accent-soft);
  border: 1px solid var(--fish-accent-border);
  font-size: var(--fish-text-sm);
  color: var(--fish-accent);
  text-decoration: none;
  cursor: pointer;
  transition: color 0.2s, background 0.2s, border-color 0.2s;
}

.tag-link:hover {
  background: var(--fish-accent);
  color: #fff;
  border-color: var(--fish-accent);
}

/* ===== 通用区块标题 ===== */
.section-title {
  display: flex;
  align-items: center;
  gap: var(--fish-space-sm);
  margin: 0 0 var(--fish-space-md);
  font-size: var(--fish-text-lg);
  font-weight: 700;
  color: var(--fish-text-1);
}

.section-title::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 16px;
  border-radius: 3px;
  background: var(--fish-accent);
  flex-shrink: 0;
}

/* ===== 插图区 ===== */
.images-section {
  padding: 0 var(--fish-space-lg) var(--fish-space-lg);
}

.gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: var(--fish-space-sm);
}

.gallery-img {
  width: 100%;
  aspect-ratio: 16 / 10;
  border-radius: var(--fish-radius-sm);
  cursor: zoom-in;
  transition: transform 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.gallery-img:hover {
  transform: scale(1.02);
}

/* ===== 评论区 ===== */
.comments-section {
  padding: 0 var(--fish-space-lg) var(--fish-space-lg);
}

/* ===== 空/错误状态 ===== */
.empty-img {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 48px 0;
}

.empty-img img {
  width: 240px;
  max-width: 70%;
  border-radius: 12px;
  opacity: 0.85;
}

.empty-img p {
  margin: 0;
  font-size: 15px;
  color: var(--fish-text-3);
}

/* ===== 响应式 ===== */
@media (max-width: 560px) {
  .article-title {
    font-size: var(--fish-text-2xl);
  }

  .meta-row {
    gap: var(--fish-space-sm);
    font-size: var(--fish-text-xs);
  }

  .article-header {
    padding: var(--fish-space-lg) var(--fish-space-md) 0;
  }

  .content-area {
    padding: var(--fish-space-md);
  }

  .content-body {
    font-size: 15px;
  }

  .tags-section,
  .images-section,
  .comments-section {
    padding-left: var(--fish-space-md);
    padding-right: var(--fish-space-md);
  }

  .cover-wrapper {
    padding: 0;
  }

  .cover-inner {
    aspect-ratio: 16 / 9;
    max-height: 260px;
  }

  .gallery {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>