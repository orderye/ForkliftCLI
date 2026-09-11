<template>
  <el-card>
    <div class="toolbar">
      <el-input v-model="query.keyword" placeholder="标题关键词" clearable style="width: 220px" @keyup.enter="loadData" />
      <el-select v-model="query.doc_type" placeholder="类型" clearable style="width: 160px">
        <el-option label="维修手册" value="manual" />
        <el-option label="故障案例" value="case" />
        <el-option label="参数资料" value="parameter" />
      </el-select>
      <el-button type="primary" @click="loadData">查询</el-button>
      <el-button type="success" @click="onAdd">新增文档</el-button>
    </div>

    <el-table :data="list" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
      <el-table-column label="类型" width="120">
        <template #default="{ row }">
          <el-tag>{{ typeLabel(row.doc_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="source" label="来源" width="140" />
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">{{ fmt(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="onEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="pager" layout="total, prev, pager, next"
      :total="total" :current-page="query.page" :page-size="query.page_size"
      @current-change="(p) => { query.page = p; loadData() }"
    />

    <el-dialog v-model="dialog.visible" :title="dialog.id ? '编辑文档' : '新增文档'" width="640px">
      <el-form :model="dialog.form" label-width="80px">
        <el-form-item label="标题" required><el-input v-model="dialog.form.title" /></el-form-item>
        <el-form-item label="类型">
          <el-select v-model="dialog.form.doc_type" style="width: 100%">
            <el-option label="维修手册" value="manual" />
            <el-option label="故障案例" value="case" />
            <el-option label="参数资料" value="parameter" />
          </el-select>
        </el-form-item>
        <el-form-item label="来源"><el-input v-model="dialog.form.source" /></el-form-item>
        <el-form-item label="正文内容" required>
          <el-input v-model="dialog.form.content" type="textarea" :rows="10" placeholder="文档正文，保存后自动切分用于 AI 检索" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="dialog.saving" @click="onSave">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { knowledgeApi } from '@/api/admin'
import type { KnowledgeDoc } from '@/api/types'

const loading = ref(false)
const list = ref<KnowledgeDoc[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 10, keyword: '', doc_type: '' })

const emptyForm = () => ({ title: '', content: '', source: '', doc_type: 'manual' })
const dialog = reactive({ visible: false, saving: false, id: 0, form: emptyForm() })

const typeLabel = (t: string) => ({ manual: '维修手册', case: '故障案例', parameter: '参数资料' }[t] || t || '—')
const fmt = (t: string | null) => (t ? t.replace('T', ' ').slice(0, 19) : '—')

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: query.page, page_size: query.page_size }
    if (query.keyword) params.keyword = query.keyword
    if (query.doc_type) params.doc_type = query.doc_type
    const res = await knowledgeApi.docList(params)
    list.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function onAdd() {
  dialog.id = 0
  dialog.form = emptyForm()
  dialog.visible = true
}

function onEdit(row: KnowledgeDoc) {
  dialog.id = row.id
  dialog.form = {
    title: row.title, content: row.content || '',
    source: row.source || '', doc_type: row.doc_type || 'manual',
  }
  dialog.visible = true
}

async function onSave() {
  if (!dialog.form.title || !dialog.form.content) {
    return ElMessage.warning('标题和正文必填')
  }
  dialog.saving = true
  try {
    if (dialog.id) await knowledgeApi.docUpdate(dialog.id, dialog.form)
    else await knowledgeApi.docCreate(dialog.form)
    ElMessage.success('已保存')
    dialog.visible = false
    loadData()
  } finally {
    dialog.saving = false
  }
}

async function onDelete(row: KnowledgeDoc) {
  await ElMessageBox.confirm(`确定删除文档「${row.title}」吗？关联的向量分块将一并删除。`, '提示', { type: 'warning' })
  await knowledgeApi.docRemove(row.id)
  ElMessage.success('已删除')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.pager { margin-top: 16px; justify-content: flex-end; }
</style>
