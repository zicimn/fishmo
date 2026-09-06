<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import type { AddGal, EditGal } from '~/types'
import { useGalgameDetail, editGalgame, deleteGalgame } from '~/composables/useGalgame'
import { useAuthStore } from '~/stores/auth'
import { getErrDetail } from '~/utils/request'

// 登录守卫
definePageMeta({ middleware: 'auth' })

const route = useRoute()
const gameId = computed(() =>
  Number(Array.isArray(route.params.id) ? route.params.id[0] : route.params.id),
)
const { data: game, pending, error, refresh } = useGalgameDetail(gameId)

const auth = useAuthStore()
const isOwner = computed(
  () => !!game.value && auth.userId != null && game.value.author_id === auth.userId,
)
// 作者判断依赖客户端登录态（localStorage，SSR 时为空）：若直接按 isOwner 分支，
// 作者硬刷新 /manage 时服务端渲染“非作者提示”而客户端水合为编辑表单，会水合不一致。
// 故整个作者相关区块等挂载后再渲染。
const isMounted = ref(false)
onMounted(() => {
  isMounted.value = true
})
const saving = ref(false)

async function handleSubmit(payload: AddGal | EditGal) {
  if (!game.value) return
  saving.value = true
  try {
    // 编辑模式表单始终产出 EditGal
    await editGalgame(game.value.id, payload as EditGal)
    ElMessage.success('保存成功')
    refresh()
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '保存失败'))
  } finally {
    saving.value = false
  }
}

async function handleDelete() {
  if (!game.value) return
  try {
    await ElMessageBox.confirm('确定删除该游戏吗？删除后不可恢复。', '删除游戏', {
      type: 'warning',
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await deleteGalgame(game.value.id)
    ElMessage.success('删除成功')
    navigateTo('/')
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '删除失败'))
  }
}
</script>

<template>
  <div class="manage-game-page">
    <header class="page-head">
      <h2 class="page-title">管理游戏 #{{ gameId }}</h2>
      <p class="page-desc">编辑游戏信息、管理该游戏的下载链接。</p>
    </header>

    <el-skeleton v-if="pending" :rows="6" animated />
    <el-result
      v-else-if="error"
      icon="error"
      title="加载失败"
      sub-title="游戏可能不存在或后端未跑通"
    >
      <template #extra>
        <el-button @click="refresh">重试</el-button>
      </template>
    </el-result>

    <template v-else-if="game">
      <el-alert
        v-if="isMounted && !isOwner"
        type="error"
        :closable="false"
        show-icon
        title="你不是该游戏的作者，无法编辑或管理。"
        class="mb"
      />

      <template v-else-if="isMounted">
        <GalgameForm mode="edit" :initial="game" :submitting="saving" @submit="handleSubmit" />
        <div class="delete-zone">
          <el-button type="danger" plain @click="handleDelete">删除该游戏</el-button>
        </div>
        <LinkManage :game-id="game.id" />
      </template>
    </template>
  </div>
</template>

<style scoped>
.manage-game-page {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}
.page-head {
  margin-bottom: 0;
}
.page-title {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 6px;
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
.page-desc {
  margin: 0;
  font-size: 13px;
  color: var(--fish-text-3);
}
.mb {
  margin-bottom: 0;
}
.delete-zone {
  display: flex;
  justify-content: flex-end;
}
</style>
