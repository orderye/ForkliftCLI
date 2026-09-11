<template>
  <el-card>
    <el-form inline>
      <el-form-item label="关键词">
        <el-input v-model="query.keyword" placeholder="手机号/昵称" clearable @keyup.enter="loadData" />
      </el-form-item>
      <el-form-item label="角色">
        <el-select v-model="query.role" placeholder="全部" clearable style="width: 140px">
          <el-option label="普通用户" value="user" />
          <el-option label="技师" value="technician" />
          <el-option label="运营" value="operator" />
          <el-option label="管理员" value="admin" />
        </el-select>
      </el-form-item>
      <el-form-item label="状态">
        <el-select v-model="query.status" placeholder="全部" clearable style="width: 120px">
          <el-option label="正常" value="active" />
          <el-option label="停用" value="disabled" />
        </el-select>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click="loadData">查询</el-button>
      </el-form-item>
    </el-form>

    <el-table :data="list" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="phone" label="手机号" width="130" />
      <el-table-column prop="nickname" label="昵称" width="140" />
      <el-table-column prop="enterprise_name" label="所属企业" width="160" />
      <el-table-column label="角色" width="110">
        <template #default="{ row }">
          <el-tag :type="roleTagType(row.role)">{{ roleLabel(row.role) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-switch
            :model-value="row.status === 'active'"
            @change="(v) => onToggleStatus(row, v)"
          />
        </template>
      </el-table-column>
      <el-table-column prop="last_login_at" label="最近登录" width="180">
        <template #default="{ row }">{{ fmt(row.last_login_at) }}</template>
      </el-table-column>
      <el-table-column prop="created_at" label="注册时间" width="180">
        <template #default="{ row }">{{ fmt(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button size="small" @click="onEdit(row)">编辑</el-button>
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

    <el-dialog v-model="dialog.visible" title="编辑用户" width="460px">
      <el-form :model="dialog.form" label-width="90px">
        <el-form-item label="昵称">
          <el-input v-model="dialog.form.nickname" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="dialog.form.role" style="width: 100%">
            <el-option label="普通用户" value="user" />
            <el-option label="技师" value="technician" />
            <el-option label="运营管理员" value="operator" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
        <el-form-item label="所属企业">
          <el-select v-model="dialog.form.enterprise_id" clearable filterable style="width: 100%">
            <el-option
              v-for="e in enterprises"
              :key="e.id"
              :label="e.name"
              :value="e.id"
            />
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
import { ElMessage } from 'element-plus'
import { enterpriseApi, userApi } from '@/api/admin'
import type { AdminUser, Enterprise } from '@/api/types'

const loading = ref(false)
const list = ref<AdminUser[]>([])
const total = ref(0)
const enterprises = ref<Enterprise[]>([])
const query = reactive({ page: 1, page_size: 10, keyword: '', role: '', status: '' })

const dialog = reactive({
  visible: false,
  saving: false,
  id: 0,
  form: { nickname: '', role: 'user', status: 'active', enterprise_id: null as number | null },
})

const roleMap: Record<string, string> = {
  user: '普通用户', technician: '技师', operator: '运营', admin: '管理员',
}
const roleLabel = (r: string) => roleMap[r] || r
const roleTagType = (r: string) =>
  r === 'admin' ? 'danger' : r === 'operator' ? 'warning' : r === 'technician' ? 'success' : 'info'
const fmt = (t: string | null) => (t ? t.replace('T', ' ').slice(0, 19) : '—')

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: query.page, page_size: query.page_size }
    if (query.keyword) params.keyword = query.keyword
    if (query.role) params.role = query.role
    if (query.status) params.status = query.status
    const res = await userApi.list(params)
    list.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function onEdit(row: AdminUser) {
  dialog.id = row.id
  dialog.form = {
    nickname: row.nickname,
    role: row.role,
    status: row.status,
    enterprise_id: row.enterprise_id,
  }
  dialog.visible = true
}

async function onSave() {
  dialog.saving = true
  try {
    await userApi.update(dialog.id, { ...dialog.form })
    ElMessage.success('已保存')
    dialog.visible = false
    loadData()
  } finally {
    dialog.saving = false
  }
}

async function onToggleStatus(row: AdminUser, active: boolean) {
  try {
    await userApi.update(row.id, { status: active ? 'active' : 'disabled' })
    ElMessage.success(active ? '已启用' : '已停用')
    loadData()
  } catch {
    loadData()
  }
}

onMounted(async () => {
  const res = await enterpriseApi.list({ page: 1, page_size: 100 })
  enterprises.value = res.items
  loadData()
})
</script>

<style scoped>
.pager {
  margin-top: 16px;
  justify-content: flex-end;
}
</style>
