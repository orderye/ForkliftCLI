<template>
  <el-card>
    <div class="toolbar">
      <el-input v-model="query.keyword" placeholder="品牌名" clearable style="width: 220px" @keyup.enter="loadData" />
      <el-button type="primary" @click="loadData">查询</el-button>
      <el-button type="success" @click="onAdd">新增品牌</el-button>
    </div>

    <el-table :data="list" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="品牌名称" min-width="160" />
      <el-table-column prop="name_en" label="英文名" min-width="140" />
      <el-table-column prop="country" label="国家" width="120" />
      <el-table-column prop="series_count" label="系列数" width="90" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="onEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="onDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      class="pager"
      layout="total, prev, pager, next"
      :total="total"
      :current-page="query.page"
      :page-size="query.page_size"
      @current-change="(p) => { query.page = p; loadData() }"
    />

    <el-dialog v-model="dialog.visible" :title="dialog.id ? '编辑品牌' : '新增品牌'" width="460px">
      <el-form :model="dialog.form" label-width="80px">
        <el-form-item label="名称" required>
          <el-input v-model="dialog.form.name" />
        </el-form-item>
        <el-form-item label="英文名">
          <el-input v-model="dialog.form.name_en" />
        </el-form-item>
        <el-form-item label="国家">
          <el-input v-model="dialog.form.country" />
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
import { catalogApi } from '@/api/admin'
import type { Brand } from '@/api/types'

const loading = ref(false)
const list = ref<Brand[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 10, keyword: '' })

const emptyForm = () => ({ name: '', name_en: '', country: '' })
const dialog = reactive({ visible: false, saving: false, id: 0, form: emptyForm() })

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: query.page, page_size: query.page_size }
    if (query.keyword) params.keyword = query.keyword
    const res = await catalogApi.brandList(params)
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

function onEdit(row: Brand) {
  dialog.id = row.id
  dialog.form = { name: row.name, name_en: row.name_en, country: row.country }
  dialog.visible = true
}

async function onSave() {
  if (!dialog.form.name) {
    ElMessage.warning('品牌名称必填')
    return
  }
  dialog.saving = true
  try {
    if (dialog.id) await catalogApi.brandUpdate(dialog.id, dialog.form)
    else await catalogApi.brandCreate(dialog.form)
    ElMessage.success('已保存')
    dialog.visible = false
    loadData()
  } finally {
    dialog.saving = false
  }
}

async function onDelete(row: Brand) {
  await ElMessageBox.confirm(`确定删除品牌「${row.name}」吗？`, '提示', { type: 'warning' })
  await catalogApi.brandRemove(row.id)
  ElMessage.success('已删除')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.pager { margin-top: 16px; justify-content: flex-end; }
</style>
