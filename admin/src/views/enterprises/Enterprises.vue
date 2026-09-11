<template>
  <el-card>
    <div class="toolbar">
      <el-input
        v-model="query.keyword"
        placeholder="企业名/编号"
        clearable
        style="width: 240px"
        @keyup.enter="loadData"
      />
      <el-select v-model="query.plan" placeholder="套餐" clearable style="width: 140px">
        <el-option label="免费版" value="free" />
        <el-option label="专业版" value="pro" />
        <el-option label="企业版" value="enterprise" />
      </el-select>
      <el-button type="primary" @click="loadData">查询</el-button>
      <el-button type="success" @click="onAdd">新增企业</el-button>
    </div>

    <el-table :data="list" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="name" label="企业名称" min-width="180" />
      <el-table-column prop="code" label="企业编号" width="140" />
      <el-table-column prop="contact_name" label="联系人" width="110" />
      <el-table-column prop="contact_phone" label="联系电话" width="140" />
      <el-table-column label="套餐" width="110">
        <template #default="{ row }">
          <el-tag :type="planTag(row.plan)">{{ planLabel(row.plan) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="user_count" label="用户数" width="90" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'">
            {{ row.status === 'active' ? '正常' : '停用' }}
          </el-tag>
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
      class="pager"
      layout="total, prev, pager, next"
      :total="total"
      :current-page="query.page"
      :page-size="query.page_size"
      @current-change="(p) => { query.page = p; loadData() }"
    />

    <el-dialog v-model="dialog.visible" :title="dialog.id ? '编辑企业' : '新增企业'" width="500px">
      <el-form :model="dialog.form" label-width="90px">
        <el-form-item label="企业名称" required>
          <el-input v-model="dialog.form.name" />
        </el-form-item>
        <el-form-item label="企业编号" required>
          <el-input v-model="dialog.form.code" :disabled="!!dialog.id" placeholder="如 E001" />
        </el-form-item>
        <el-form-item label="联系人">
          <el-input v-model="dialog.form.contact_name" />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input v-model="dialog.form.contact_phone" />
        </el-form-item>
        <el-form-item label="地址">
          <el-input v-model="dialog.form.address" />
        </el-form-item>
        <el-form-item label="套餐">
          <el-select v-model="dialog.form.plan" style="width: 100%">
            <el-option label="免费版" value="free" />
            <el-option label="专业版" value="pro" />
            <el-option label="企业版" value="enterprise" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="dialog.form.status">
            <el-radio value="active">正常</el-radio>
            <el-radio value="disabled">停用</el-radio>
          </el-radio-group>
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
import { enterpriseApi } from '@/api/admin'
import type { Enterprise } from '@/api/types'

const loading = ref(false)
const list = ref<Enterprise[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 10, keyword: '', plan: '' })

const emptyForm = () => ({
  name: '', code: '', contact_name: '', contact_phone: '',
  address: '', plan: 'free', status: 'active',
})
const dialog = reactive({
  visible: false, saving: false, id: 0,
  form: emptyForm(),
})

const planLabel = (p: string) => ({ free: '免费版', pro: '专业版', enterprise: '企业版' }[p] || p)
const planTag = (p: string) => ({ free: 'info', pro: 'warning', enterprise: 'success' }[p] || 'info')

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: query.page, page_size: query.page_size }
    if (query.keyword) params.keyword = query.keyword
    if (query.plan) params.plan = query.plan
    const res = await enterpriseApi.list(params)
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

function onEdit(row: Enterprise) {
  dialog.id = row.id
  dialog.form = {
    name: row.name, code: row.code, contact_name: row.contact_name,
    contact_phone: row.contact_phone, address: row.address,
    plan: row.plan, status: row.status,
  }
  dialog.visible = true
}

async function onSave() {
  if (!dialog.form.name || !dialog.form.code) {
    ElMessage.warning('企业名称和编号必填')
    return
  }
  dialog.saving = true
  try {
    if (dialog.id) {
      await enterpriseApi.update(dialog.id, dialog.form)
    } else {
      await enterpriseApi.create(dialog.form)
    }
    ElMessage.success('已保存')
    dialog.visible = false
    loadData()
  } finally {
    dialog.saving = false
  }
}

async function onDelete(row: Enterprise) {
  await ElMessageBox.confirm(`确定删除企业「${row.name}」吗？`, '提示', { type: 'warning' })
  await enterpriseApi.remove(row.id)
  ElMessage.success('已删除')
  loadData()
}

onMounted(loadData)
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
