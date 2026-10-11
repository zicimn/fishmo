<script setup lang="ts">
useHead({
  title: '关于 - fishmo',
  meta: [
    { name: 'description', content: '关于 fishmo — Galgame 信息发布社区与文章博客平台' },
  ],
})
</script>

<template>
  <div class="about-layout">
    <!-- 页面标题 -->
    <header class="page-head">
      <h1 class="page-title">关于 fishmo</h1>
      <p class="page-subtitle">Galgame 信息发布社区与文章博客平台</p>
    </header>

    <!-- 网站简介 -->
    <section class="about-section">
      <h2 class="section-title">
        <el-icon><InfoFilled /></el-icon>
        网站简介
      </h2>
      <div class="section-body">
        <p>
          <strong>fishmo</strong> 是一个专注于 Galgame（美少女游戏）的信息发布社区与文章博客平台。
          在这里，你可以发现并分享丰富的游戏内容，也能撰写攻略、资讯、教程等文章，与同好交流互动。
        </p>
      </div>
    </section>

    <!-- 主要功能 -->
    <section class="about-section">
      <h2 class="section-title">
        <el-icon><Star /></el-icon>
        主要功能
      </h2>
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">🎮</div>
          <h3 class="feature-name">发布游戏信息</h3>
          <p class="feature-desc">
            分享游戏的名称、简介、封面、截图、标签、平台及下载链接，构建完整的游戏资料库。
          </p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">📝</div>
          <h3 class="feature-name">分享文章</h3>
          <p class="feature-desc">
            撰写攻略、资讯、公告、教程等内容，支持 Markdown 编辑与插图画廊。
          </p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">💬</div>
          <h3 class="feature-name">评论互动</h3>
          <p class="feature-desc">
            在游戏与文章下方发表评论，与社区成员交流心得与见解。
          </p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">⭐</div>
          <h3 class="feature-name">收藏游戏</h3>
          <p class="feature-desc">
            收藏感兴趣的游戏，建立个人游戏库，随时回顾。
          </p>
        </div>
      </div>
    </section>

    <!-- 技术栈 -->
    <section class="about-section">
      <h2 class="section-title">
        <el-icon><SetUp /></el-icon>
        技术栈
      </h2>
      <div class="tech-list">
        <span class="tech-tag">Nuxt 3</span>
        <span class="tech-tag">Vue 3</span>
        <span class="tech-tag">TypeScript</span>
        <span class="tech-tag">Element Plus</span>
        <span class="tech-tag">FastAPI</span>
        <span class="tech-tag">SQLAlchemy</span>
        <span class="tech-tag">MySQL</span>
        <span class="tech-tag">Redis</span>
        <span class="tech-tag">Cloudinary</span>
      </div>
    </section>

    <!-- 开源 -->
    <section class="about-section">
      <h2 class="section-title">
        <el-icon><Link /></el-icon>
        开源
      </h2>
      <div class="section-body">
        <p>
          本项目已在 GitHub 开源，欢迎查阅与贡献：
        </p>
        <a
          href="https://github.com/zicimn/fishmo"
          target="_blank"
          rel="noopener noreferrer"
          class="github-link"
        >
          <el-icon><Connection /></el-icon>
          github.com/zicimn/fishmo
        </a>
      </div>
    </section>

    <!-- 联系我们 -->
    <section class="about-section">
      <h2 class="section-title">
        <el-icon><Message /></el-icon>
        联系我们
      </h2>
      <div class="section-body">
        <p>如有问题、建议或合作意向，欢迎通过以下方式联系：</p>
        <div class="contact-item">
          <el-icon><ChatDotRound /></el-icon>
          <a href="mailto:fwioe77@gmail.com" class="contact-link">fwioe77#gmail.com</a>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.about-layout {
  max-width: 820px;
  margin: 0 auto;
}

/* ===== 页面头部 ===== */
.page-head {
  margin-bottom: var(--fish-space-xl);
}

.page-title {
  margin: 0 0 var(--fish-space-sm);
  font-size: var(--fish-text-4xl);
  font-weight: 800;
  letter-spacing: var(--fish-tracking-tight);
  color: var(--fish-accent);
  line-height: 1.2;
}

.page-subtitle {
  margin: 0;
  font-size: var(--fish-text-lg);
  color: var(--fish-text-2);
  font-weight: 500;
}

/* ===== 通用区块 ===== */
.about-section {
  margin-bottom: var(--fish-space-xl);
  padding: var(--fish-space-lg);
  border: 1px solid var(--fish-border);
  border-radius: var(--fish-radius);
  background: var(--fish-card);
  box-shadow: var(--fish-shadow);
}

.section-title {
  display: flex;
  align-items: center;
  gap: var(--fish-space-sm);
  margin: 0 0 var(--fish-space-md);
  font-size: var(--fish-text-xl);
  font-weight: 700;
  color: var(--fish-text-1);
  line-height: var(--fish-leading-tight);
}

.section-title .el-icon {
  color: var(--fish-accent);
  font-size: 20px;
}

.section-body {
  color: var(--fish-text-2);
  font-size: var(--fish-text-base);
  line-height: var(--fish-leading-relaxed);
}

.section-body p {
  margin: 0 0 var(--fish-space-sm);
}

.section-body p:last-child {
  margin-bottom: 0;
}

.section-body strong {
  color: var(--fish-text-1);
  font-weight: 600;
}

/* ===== 功能网格 ===== */
.features-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--fish-space-md);
}

.feature-card {
  padding: var(--fish-space-md);
  border: 1px solid var(--fish-border);
  border-radius: var(--fish-radius-sm);
  background: var(--fish-bg-2);
  transition: border-color 0.25s cubic-bezier(0.16, 1, 0.3, 1),
    transform 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

.feature-card:hover {
  border-color: var(--fish-accent-border);
  transform: translateY(-2px);
}

.feature-icon {
  font-size: 28px;
  margin-bottom: var(--fish-space-sm);
}

.feature-name {
  margin: 0 0 var(--fish-space-xs);
  font-size: var(--fish-text-lg);
  font-weight: 600;
  color: var(--fish-text-1);
}

.feature-desc {
  margin: 0;
  font-size: var(--fish-text-sm);
  color: var(--fish-text-2);
  line-height: var(--fish-leading-normal);
}

/* ===== 技术标签 ===== */
.tech-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--fish-space-sm);
}

.tech-tag {
  display: inline-flex;
  align-items: center;
  padding: 6px 14px;
  border-radius: 999px;
  border: 1px solid var(--fish-border);
  background: transparent;
  color: var(--fish-text-2);
  font-size: var(--fish-text-sm);
  font-weight: 500;
  transition: border-color 0.2s, color 0.2s, background 0.2s;
}

.tech-tag:hover {
  border-color: var(--fish-accent-border);
  color: var(--fish-accent);
  background: var(--fish-accent-soft);
}

/* ===== GitHub 链接 ===== */
.github-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border-radius: var(--fish-radius-sm);
  border: 1px solid var(--fish-accent-border);
  background: var(--fish-accent-soft);
  color: var(--fish-accent);
  font-size: var(--fish-text-base);
  font-weight: 600;
  text-decoration: none;
  transition: background 0.2s, border-color 0.2s, color 0.2s;
}

.github-link:hover {
  background: var(--fish-accent);
  border-color: var(--fish-accent);
  color: #fff;
}

.github-link .el-icon {
  font-size: 18px;
}

/* ===== 联系方式 ===== */
.contact-item {
  display: inline-flex;
  align-items: center;
  gap: var(--fish-space-sm);
  padding: 10px 18px;
  border-radius: var(--fish-radius-sm);
  border: 1px solid var(--fish-border);
  background: var(--fish-bg-2);
}

.contact-item .el-icon {
  color: var(--fish-accent);
  font-size: 18px;
}

.contact-link {
  color: var(--fish-text-1);
  font-size: var(--fish-text-base);
  font-weight: 500;
  text-decoration: none;
  transition: color 0.2s;
}

.contact-link:hover {
  color: var(--fish-accent);
}

/* ===== 响应式 ===== */
@media (max-width: 560px) {
  .features-grid {
    grid-template-columns: 1fr;
  }

  .about-section {
    padding: var(--fish-space-md);
  }

  .page-title {
    font-size: var(--fish-text-3xl);
  }
}
</style>
