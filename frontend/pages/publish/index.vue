<script setup lang="ts">
import { ElMessage } from 'element-plus'
import type { AddGal, EditGal } from '~/types'
import { addGalgame } from '~/composables/useGalgame'
import { getErrDetail } from '~/utils/request'

// 登录守卫（客户端判断，SSR 阶段不做跳转）
definePageMeta({ middleware: 'auth' })

const submitting = ref(false)

async function handleSubmit(payload: AddGal | EditGal) {
  submitting.value = true
  try {
    // 发布模式表单始终产出 AddGal
    const res = await addGalgame(payload as AddGal)
    ElMessage.success('发布成功')
    navigateTo(`/galgame/${res.id}`)
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '发布失败'))
  } finally {
    submitting.value = false
  }
}
</script>

<template>
  <div class="publish-page">
    <header class="page-head">
      <h2 class="page-title">发布游戏</h2>
      <p class="page-desc">发布即公开（作者即发布者）。右侧可实时预览首页卡片效果。</p>
    </header>

    <GalgameForm mode="add" :submitting="submitting" @submit="handleSubmit" @cancel="navigateTo('/')" />
  </div>
</template>

<style scoped>
.publish-page {
  max-width: 1100px;
  margin: 0 auto;
}
.page-head {
  margin-bottom: 20px;
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
</style>
