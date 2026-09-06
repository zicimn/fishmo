<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import type { LinkItems } from '~/types'
import { useUserLinkList, reviewLink, deleteLink } from '~/composables/useLink'
import { useAuthStore } from '~/stores/auth'
import { isSafeLink } from '~/utils/link'
import { formatBytes, bytesToMb, mbToBytes } from '~/utils/format'
import { getErrDetail } from '~/utils/request'

/** 我的链接：分页管理列表 + 行内编辑（供个人主页「链接」tab 与 /manage 复用）。 */
const auth = useAuthStore()
const SIZE = 20
const page = ref(1)

const query = computed<{ userId?: number; page?: number; size?: number }>(() => ({
  userId: auth.userId ?? undefined,
  page: page.value,
  size: SIZE,
}))
const { data, pending, refresh } = useUserLinkList(query, { key: 'my-links' })

// 编辑链接：size 表单以 MB 为单位，回显需从字节换算，提交再换算回字节
const dialog = ref(false)
const saving = ref(false)
const form = reactive({
  id: 0,
  category: '',
  content: '',
  code: '',
  size: undefined as number | undefined,
})

function openEdit(entry: LinkItems) {
  form.id = entry.item.id
  form.category = entry.item.category || ''
  form.content = entry.item.content || ''
  form.code = entry.item.code || ''
  form.size = bytesToMb(entry.item.size)
  dialog.value = true
}

async function submitEdit() {
  saving.value = true
  try {
    await reviewLink(form.id, {
      category: form.category || null,
      content: form.content || null,
      code: form.code || null,
      size: mbToBytes(form.size),
    })
    ElMessage.success('链接已更新')
    dialog.value = false
    refresh()
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '更新失败'))
  } finally {
    saving.value = false
  }
}

async function handleDelete(entry: LinkItems) {
  try {
    await ElMessageBox.confirm('确定删除该链接吗？', '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await deleteLink(entry.item.id)
    ElMessage.success('链接已删除')
    refresh()
  } catch (e: any) {
    ElMessage.error(getErrDetail(e, '删除失败'))
  }
}
</script>

<template>
  <div class="my-links">
    <el-skeleton v-if="pending && !data?.items?.length" :rows="6" animated />
    <ClientOnly v-else-if="!data?.items?.length">
      <el-empty description="还没有发布链接" :image-size="90" />
    </ClientOnly>

    <template v-else>
      <ul class="m-list">
        <li v-for="entry in data.items" :key="entry.item.id" class="m-item">
          <div class="m-main">
            <div class="m-title m-title-link">
              <a
                v-if="isSafeLink(entry.item.url)"
                :href="entry.item.url"
                target="_blank"
                rel="noopener noreferrer"
                class="m-link"
              >
                {{ entry.item.content || entry.item.url }}
              </a>
              <span v-else class="m-link unsafe">{{ entry.item.content || entry.item.url }}</span>
            </div>
            <div class="m-meta">
              <el-tag v-if="entry.item.category" size="small" type="info" effect="plain">
                {{ entry.item.category }}
              </el-tag>
              <el-tag v-if="entry.item.size" size="small" type="warning" effect="plain">
                {{ formatBytes(entry.item.size) }}
              </el-tag>
              <NuxtLink :to="`/galgame/${entry.item.game_id}`" class="m-taglink">
                游戏 #{{ entry.item.game_id }}
              </NuxtLink>
            </div>
          </div>
          <div class="m-actions">
            <el-button size="small" type="primary" plain @click="openEdit(entry)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="handleDelete(entry)">删除</el-button>
          </div>
        </li>
      </ul>
      <div class="pagination-wrap">
        <el-pagination
          layout="prev, pager, next, total"
          :total="data.total"
          :page-size="SIZE"
          :current-page="page"
          @current-change="(p: number) => (page = p)"
        />
      </div>
    </template>

    <!-- 编辑链接对话框 -->
    <el-dialog v-model="dialog" title="编辑链接" width="520px">
      <el-form label-position="top" @submit.prevent="submitEdit">
        <el-form-item label="分类">
          <el-input v-model="form.category" placeholder="如 网盘 / 磁力 / BT" maxlength="255" />
        </el-form-item>
        <el-form-item label="大小（MB）">
          <el-input-number v-model="form.size" :min="0" :max="100000" style="width: 100%" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="form.content"
            type="textarea"
            :rows="2"
            maxlength="255"
            placeholder="解压码 / 版本说明等"
          />
        </el-form-item>
        <el-form-item label="提取码（可选）">
          <el-input v-model="form.code" maxlength="255" placeholder="网盘提取码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submitEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.m-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.m-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border: 1px solid var(--fish-border);
  border-radius: 10px;
  margin-bottom: 8px;
  background: var(--fish-bg-2);
  transition: border-color 0.2s, transform 0.2s;
}
.m-item:hover {
  border-color: var(--fish-accent-border);
  transform: translateY(-1px);
}
.m-main {
  flex: 1;
  min-width: 0;
}
.m-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--fish-text-1);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.m-link {
  color: var(--fish-accent);
  text-decoration: none;
  word-break: break-all;
}
.m-link:hover {
  text-decoration: underline;
}
.m-link.unsafe,
.m-link.unsafe:hover {
  color: var(--fish-text-3);
  text-decoration: none;
  cursor: default;
}
.m-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 4px;
}
.m-taglink {
  font-size: 12px;
  color: var(--fish-text-3);
  text-decoration: none;
}
.m-taglink:hover {
  color: var(--fish-accent);
}
.m-actions {
  flex-shrink: 0;
  display: flex;
  gap: 6px;
}
.pagination-wrap {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}

@media (max-width: 560px) {
  .m-item {
    flex-wrap: wrap;
  }
  .m-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>
