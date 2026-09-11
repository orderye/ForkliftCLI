<template>
  <el-card>
    <div class="toolbar">
      <el-select v-model="query.action" placeholder="操作类型" clearable style="width: 170px">
        <el-option label="创建 create" value="create" />
        <el-option label="更新 update" value="update" />
        <el-option label="删除 delete" value="delete" />
      </el-select>
      <el-select v-model="query.target_type" placeholder="对象类型" clearable filterable style="width: 200px">
        <el-option v-for="t in targetTypes" :key="t" :label="t" :value="t" />
      </el-select>
      <el-input v-model="query.admin_user_id" placeholder="管理员ID" clearable style="width: 140px" />
      <el-button type="primary" @click="loadData">查询</el-button>
    </div>

    <el-table :data="list" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="admin_user_id" label="操作人ID" width="100" />
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-tag :type="actionType(row.action)">{{ actionLabel(row.action) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="target_type" label="对象类型" width="180" />
      <el-table-column prop="target_id" label="对象ID" width="90" />
      <el-table-column prop="ip" label="IP" width="140" />
      <el-table-column prop="created_at" label="时间" width="180">
        <template #default="{ row }">{{ fmt(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="变更详情" min-width="120">
        <template #default="{ row }">
          <el-button size="small" text type="primary" @click="showDetail(row)">查看</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="pager" layout="total, prev, pager, next"
      :total="total" :current-page="query.page" :page-size="query.page_size"
      @current-change="(p) => { query.page = p; loadData() }"
    />

    <el-dialog v-model="detailVisible" title="变更详情" width="640px">
      <el-descriptions :column="1" border>
        <el-descriptions-item label="操作">{{ current?.action }}</el-descriptions-item>
        <el-descriptions-item label="对象">{{ current?.target_type }} #{{ current?.target_id }}</el-descriptions-item>
        <el-descriptions-item label="变更前">
          <pre class="json">{{ pretty(current?.before_json) }}</pre>
        </el-descriptions-item>
        <el-descriptions-item label="变更后">
          <pre class="json">{{ pretty(current?.after_json) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { auditApi } from '@/api/admin'
import type { AuditLog } from '@/api/types'

const loading = ref(false)
const list = ref<AuditLog[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 15, action: '', target_type: '', admin_user_id: '' })
const detailVisible = ref(false)
const current = ref<AuditLog | null>(null)

const targetTypes = [
  'user', 'enterprise', 'brand', 'series', 'forklift_model',
  'engine_brand', 'engine_model', 'part', 'diagram', 'model3d',
  'knowledge_document', 'fault_code', 'fault_tree',
]

const actionLabel = (a: string) => ({ create: '创建', update: '更新', delete: '删除' }[a] || a)
const actionType = (a: string) => ({ create: 'success', update: 'warning', delete: 'danger' }[a] || 'info')
const fmt = (t: string | null) => (t ? t.replace('T', ' ').slice(0, 19) : '—')
const pretty = (v: any) => (v ? JSON.stringify(v, null, 2) : '—')

function showDetail(row: AuditLog) {
  current.value = row
  detailVisible.value = true
}

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: query.page, page_size: query.page_size }
    if (query.action) params.action = query.action
    if (query.target_type) params.target_type = query.target_type
    if (query.admin_user_id) params.admin_user_id = query.admin_user_id
    const res = await auditApi.list(params)
    list.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.pager { margin-top: 16px; justify-content: flex-end; }
.json {
  margin: 0;
  max-height: 240px;
  overflow: auto;
  font-size: 12px;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
