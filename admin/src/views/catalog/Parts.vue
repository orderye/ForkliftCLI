<template>
  <el-card>
    <div class="toolbar">
      <el-input v-model="query.keyword" placeholder="配件名/OEM号" clearable style="width: 220px" @keyup.enter="loadData" />
      <el-input v-model="query.category" placeholder="类别" clearable style="width: 160px" @keyup.enter="loadData" />
      <el-button type="primary" @click="loadData">查询</el-button>
      <el-button type="success" @click="onAdd">新增配件</el-button>
    </div>

    <el-table :data="list" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="oem_number" label="OEM编号" width="150" />
      <el-table-column prop="name" label="配件名称" min-width="180" />
      <el-table-column prop="category" label="类别" width="120" />
      <el-table-column prop="brand" label="品牌" width="120" />
      <el-table-column prop="unit" label="单位" width="80" />
      <el-table-column label="参考价" width="100">
        <template #default="{ row }">{{ row.price_reference != null ? `¥${row.price_reference}` : '—' }}</template>
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

    <el-dialog v-model="dialog.visible" :title="dialog.id ? '编辑配件' : '新增配件'" width="500px">
      <el-form :model="dialog.form" label-width="90px">
        <el-form-item label="OEM编号" required><el-input v-model="dialog.form.oem_number" /></el-form-item>
        <el-form-item label="配件名称" required><el-input v-model="dialog.form.name" /></el-form-item>
        <el-form-item label="英文名"><el-input v-model="dialog.form.name_en" /></el-form-item>
        <el-form-item label="类别"><el-input v-model="dialog.form.category" /></el-form-item>
        <el-form-item label="品牌"><el-input v-model="dialog.form.brand" /></el-form-item>
        <el-form-item label="单位">
          <el-select v-model="dialog.form.unit" style="width: 100%">
            <el-option label="个" value="个" />
            <el-option label="套" value="套" />
            <el-option label="箱" value="箱" />
            <el-option label="升" value="升" />
            <el-option label="米" value="米" />
          </el-select>
        </el-form-item>
        <el-form-item label="参考价(元)">
          <el-input-number v-model="dialog.form.price_reference" :min="0" :precision="2" controls-position="right" style="width: 100%" />
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
import type { Part } from '@/api/types'

const loading = ref(false)
const list = ref<Part[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 10, keyword: '', category: '' })

const emptyForm = () => ({
  oem_number: '', name: '', name_en: '', category: '',
  brand: '', unit: '个', price_reference: null as number | null,
})
const dialog = reactive({ visible: false, saving: false, id: 0, form: emptyForm() })

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: query.page, page_size: query.page_size }
    if (query.keyword) params.keyword = query.keyword
    if (query.category) params.category = query.category
    const res = await catalogApi.partList(params)
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

function onEdit(row: Part) {
  dialog.id = row.id
  dialog.form = {
    oem_number: row.oem_number, name: row.name, name_en: row.name_en,
    category: row.category, brand: row.brand, unit: row.unit || '个',
    price_reference: row.price_reference,
  }
  dialog.visible = true
}

async function onSave() {
  if (!dialog.form.oem_number || !dialog.form.name) {
    return ElMessage.warning('OEM编号和配件名称必填')
  }
  dialog.saving = true
  try {
    if (dialog.id) await catalogApi.partUpdate(dialog.id, dialog.form)
    else await catalogApi.partCreate(dialog.form)
    ElMessage.success('已保存')
    dialog.visible = false
    loadData()
  } finally {
    dialog.saving = false
  }
}

async function onDelete(row: Part) {
  await ElMessageBox.confirm(`确定删除配件「${row.name}」吗？`, '提示', { type: 'warning' })
  await catalogApi.partRemove(row.id)
  ElMessage.success('已删除')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.pager { margin-top: 16px; justify-content: flex-end; }
</style>
