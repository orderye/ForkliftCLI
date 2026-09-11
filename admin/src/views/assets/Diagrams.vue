<template>
  <el-card>
    <div class="toolbar">
      <el-input v-model="query.keyword" placeholder="图纸标题" clearable style="width: 200px" @keyup.enter="loadData" />
      <el-select v-model="query.diagram_type" placeholder="类型" clearable style="width: 150px">
        <el-option label="结构图" value="structure" />
        <el-option label="爆炸图" value="exploded" />
        <el-option label="发动机图" value="engine" />
      </el-select>
      <el-button type="primary" @click="loadData">查询</el-button>
      <el-button type="success" @click="onAdd">新增图纸</el-button>
      <el-text type="info" size="small" class="tip">提示：3D 模型文件请通过移动端/现有上传接口上传后在此维护</el-text>
    </div>

    <el-table :data="list" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column label="类型" width="110">
        <template #default="{ row }">
          <el-tag :type="typeTag(row.diagram_type)">{{ typeLabel(row.diagram_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="system_type" label="系统" width="120" />
      <el-table-column prop="hotspot_count" label="热区数" width="90" />
      <el-table-column label="预览" width="90">
        <template #default="{ row }">
          <el-link v-if="row.image_url" :href="row.image_url" target="_blank" type="primary">查看</el-link>
          <span v-else>—</span>
        </template>
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

    <el-dialog v-model="dialog.visible" :title="dialog.id ? '编辑图纸' : '新增图纸'" width="500px">
      <el-form :model="dialog.form" label-width="90px">
        <el-form-item label="标题" required><el-input v-model="dialog.form.title" /></el-form-item>
        <el-form-item label="图纸类型">
          <el-select v-model="dialog.form.diagram_type" style="width: 100%">
            <el-option label="结构图" value="structure" />
            <el-option label="爆炸图" value="exploded" />
            <el-option label="发动机图" value="engine" />
          </el-select>
        </el-form-item>
        <el-form-item label="系统类型">
          <el-input v-model="dialog.form.system_type" placeholder="如：液压/电气/传动" />
        </el-form-item>
        <el-form-item label="图片URL">
          <el-input v-model="dialog.form.image_url" placeholder="上传后回填的图片地址" />
        </el-form-item>
        <el-form-item label="关联车型ID">
          <el-input-number v-model="dialog.form.model_id" :min="1" controls-position="right" style="width: 100%" />
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
import { assetApi } from '@/api/admin'
import type { Diagram } from '@/api/types'

const loading = ref(false)
const list = ref<Diagram[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 10, keyword: '', diagram_type: '' })

const emptyForm = () => ({
  title: '', diagram_type: 'structure', system_type: '',
  image_url: '', model_id: null as number | null,
})
const dialog = reactive({ visible: false, saving: false, id: 0, form: emptyForm() })

const typeLabel = (t: string) => ({ structure: '结构图', exploded: '爆炸图', engine: '发动机图' }[t] || t)
const typeTag = (t: string) => ({ structure: 'primary', exploded: 'warning', engine: 'success' }[t] || 'info')

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: query.page, page_size: query.page_size }
    if (query.keyword) params.keyword = query.keyword
    if (query.diagram_type) params.diagram_type = query.diagram_type
    const res = await assetApi.diagramList(params)
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

function onEdit(row: Diagram) {
  dialog.id = row.id
  dialog.form = {
    title: row.title, diagram_type: row.diagram_type || 'structure',
    system_type: row.system_type || '', image_url: row.image_url || '',
    model_id: row.model_id,
  }
  dialog.visible = true
}

async function onSave() {
  if (!dialog.form.title) return ElMessage.warning('标题必填')
  dialog.saving = true
  try {
    if (dialog.id) await assetApi.diagramUpdate(dialog.id, dialog.form)
    else await assetApi.diagramCreate(dialog.form)
    ElMessage.success('已保存')
    dialog.visible = false
    loadData()
  } finally {
    dialog.saving = false
  }
}

async function onDelete(row: Diagram) {
  await ElMessageBox.confirm(`确定删除图纸「${row.title}」吗？`, '提示', { type: 'warning' })
  await assetApi.diagramRemove(row.id)
  ElMessage.success('已删除')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; align-items: center; margin-bottom: 16px; }
.tip { margin-left: auto; }
.pager { margin-top: 16px; justify-content: flex-end; }
</style>
