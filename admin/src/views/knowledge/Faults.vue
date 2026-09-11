<template>
  <el-card>
    <div class="toolbar">
      <el-input v-model="query.keyword" placeholder="故障码/描述" clearable style="width: 220px" @keyup.enter="loadData" />
      <el-button type="primary" @click="loadData">查询</el-button>
      <el-button type="success" @click="onAdd">新增故障码</el-button>
    </div>

    <el-table :data="list" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="code" label="故障代码" width="140">
        <template #default="{ row }">
          <el-tag type="danger" effect="plain">{{ row.code }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="故障描述" min-width="240" show-overflow-tooltip />
      <el-table-column label="严重程度" width="110">
        <template #default="{ row }">
          <el-tag :type="severityType(row.severity)">{{ severityLabel(row.severity) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="category" label="分类" width="130" />
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

    <el-dialog v-model="dialog.visible" :title="dialog.id ? '编辑故障码' : '新增故障码'" width="500px">
      <el-form :model="dialog.form" label-width="90px">
        <el-form-item label="故障代码" required><el-input v-model="dialog.form.code" /></el-form-item>
        <el-form-item label="故障描述" required>
          <el-input v-model="dialog.form.description" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="严重程度">
          <el-select v-model="dialog.form.severity" style="width: 100%">
            <el-option label="提示" value="info" />
            <el-option label="警告" value="warning" />
            <el-option label="严重" value="critical" />
          </el-select>
        </el-form-item>
        <el-form-item label="分类"><el-input v-model="dialog.form.category" placeholder="如：电气/液压/发动机" /></el-form-item>
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
import type { FaultCode } from '@/api/types'

const loading = ref(false)
const list = ref<FaultCode[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 10, keyword: '' })

const emptyForm = () => ({ code: '', description: '', severity: 'warning', category: '' })
const dialog = reactive({ visible: false, saving: false, id: 0, form: emptyForm() })

const severityLabel = (s: string) => ({ info: '提示', warning: '警告', critical: '严重' }[s] || s)
const severityType = (s: string) => ({ info: 'info', warning: 'warning', critical: 'danger' }[s] || 'info')

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: query.page, page_size: query.page_size }
    if (query.keyword) params.keyword = query.keyword
    const res = await knowledgeApi.faultCodeList(params)
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

function onEdit(row: FaultCode) {
  dialog.id = row.id
  dialog.form = {
    code: row.code, description: row.description,
    severity: row.severity || 'warning', category: row.category || '',
  }
  dialog.visible = true
}

async function onSave() {
  if (!dialog.form.code || !dialog.form.description) {
    return ElMessage.warning('故障代码和描述必填')
  }
  dialog.saving = true
  try {
    if (dialog.id) await knowledgeApi.faultCodeUpdate(dialog.id, dialog.form)
    else await knowledgeApi.faultCodeCreate(dialog.form)
    ElMessage.success('已保存')
    dialog.visible = false
    loadData()
  } finally {
    dialog.saving = false
  }
}

async function onDelete(row: FaultCode) {
  await ElMessageBox.confirm(`确定删除故障码「${row.code}」吗？被故障树引用时无法删除。`, '提示', { type: 'warning' })
  await knowledgeApi.faultCodeRemove(row.id)
  ElMessage.success('已删除')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.pager { margin-top: 16px; justify-content: flex-end; }
</style>
