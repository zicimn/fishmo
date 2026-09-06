<script setup lang="ts">
// 登录守卫（客户端判断，SSR 阶段放行）
definePageMeta({ middleware: 'auth' })

const route = useRoute()
const router = useRouter()

type TabName = 'galgame' | 'comment' | 'link'

// 初始 Tab 支持 URL 参数（个人主页等入口跳转 /manage?tab=comment 等）
const rawTab = route.query.tab
const rawTabStr = Array.isArray(rawTab) ? rawTab[0] : rawTab
const activeTab = ref<TabName>(rawTabStr === 'comment' || rawTabStr === 'link' ? rawTabStr : 'galgame')

// Tab 切换时同步 URL，便于分享/刷新保持
watch(activeTab, (tab: TabName) => {
  const q: Record<string, string> = {}
  if (tab !== 'galgame') q.tab = tab
  router.replace({ query: q })
})
</script>

<template>
  <div class="manage-page">
    <h2 class="page-title">我的管理</h2>
    <el-alert
      type="info"
      :closable="false"
      show-icon
      class="mb"
      title="管理我发布的游戏 / 评论 / 链接。编辑单个游戏请进入游戏管理页，评论与链接支持行内编辑。"
    />

    <el-tabs v-model="activeTab">
      <!-- ===== 我的游戏 ===== -->
      <el-tab-pane label="我的游戏" name="galgame">
        <MyGames />
      </el-tab-pane>

      <!-- ===== 我的评论 ===== -->
      <el-tab-pane label="我的评论" name="comment">
        <MyComments />
      </el-tab-pane>

      <!-- ===== 我的链接 ===== -->
      <el-tab-pane label="我的链接" name="link">
        <MyLinks />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<style scoped>
.page-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 16px;
  font-size: 24px;
  font-weight: 800;
  letter-spacing: 0.01em;
  color: var(--fish-text-1);
}
.page-title::before {
  content: '';
  width: 4px;
  height: 18px;
  border-radius: 3px;
  background: var(--fish-accent);
}
.mb {
  margin-bottom: 16px;
}
</style>
