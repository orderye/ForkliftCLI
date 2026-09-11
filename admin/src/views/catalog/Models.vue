<template>
  <el-card>
    <div class="toolbar">
      <el-input v-model="query.keyword" placeholder="车型名" clearable style="width: 200px" @keyup.enter="loadData" />
      <el-select v-model="query.brand_id" placeholder="品牌" clearable filterable style="width: 180px" @change="loadData">
        <el-option v-for="b in brands" :key="b.id" :label="b.name" :value="b.id" />
      </el-select>
      <el-button type="primary" @click="loadData">查询</el-button>
      <el-button type="success" @click="onAdd">新增车型</el-button>
    </div>

    <el-table :data="list" v-loading="loading" border stripe>
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column label="品牌/系列" min-width="180">
        <template #default="{ row }">
          <el-tag size="small">{{ row.brand_name || '-' }}</el-tag>
          <span style="margin-left: 8px">{{ row.series_name }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="车型名称" min-width="150" />
      <el-table-column label="年份" width="120">
        <template #default="{ row }">{{ row.year_start || '?' }} - {{ row.year_end || '?' }}</template>
      </el-table-column>
      <el-table-column prop="load_capacity_ton" label="载重(吨)" width="100" />
      <el-table-column label="燃料" width="90">
        <template #default="{ row }">{{ fuelLabel(row.fuel_type) }}</template>
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

    <el-dialog v-model="dialog.visible" :title="dialog.id ? '编辑车型' : '新增车型'" width="500px">
      <el-form :model="dialog.form" label-width="90px">
        <el-form-item label="所属系列" required>
          <el-select v-model="dialog.form.series_id" filterable style="width: 100%" placeholder="先选品牌筛选系列">
            <el-option
              v-for="s in filteredSeries"
              :key="s.id"
              :label="`${s.brand_name} / ${s.name}`"
              :value="s.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="车型名称" required>
          <el-input v-model="dialog.form.name" />
        </el-form-item>
        <el-form-item label="上市年份">
          <el-input-number v-model="dialog.form.year_start" :min="1980" :max="2100" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="停产年份">
          <el-input-number v-model="dialog.form.year_end" :min="1980" :max="2100" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="载重(吨)">
          <el-input-number v-model="dialog.form.load_capacity_ton" :min="0" :step="0.5" :precision="1" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="燃料类型">
          <el-select v-model="dialog.form.fuel_type" style="width: 100%">
            <el-option label="电动" value="electric" />
            <el-option label="柴油" value="diesel" />
            <el-option label="汽油" value="gasoline" />
            <el-option label="LPG" value="lpg" />
          </el-select>
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
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { catalogApi } from '@/api/admin'
import type { Brand, ForkliftModel, Series } from '@/api/types'

const loading = ref(false)
const list = ref<ForkliftModel[]>([])
const brands = ref<Brand[]>([])
const series = ref<Series[]>([])
const total = ref(0)
const query = reactive({ page: 1, page_size: 10, keyword: '', brand_id: null as number | null })

const emptyForm = () => ({
  series_id: null as number | null, name: '', year_start: null as number | null,
  year_end: null as number | null, load_capacity_ton: null as number | null,
  fuel_type: 'diesel',
})
const dialog = reactive({ visible: false, saving: false, id: 0, form: emptyForm() })

const filteredSeries = computed(() =>
  query.brand_id ? series.value.filter((s) => s.brand_id === query.brand_id) : series.value,
)

const fuelLabel = (f: string) =>
  ({ electric: '电动', diesel: '柴油', gasoline: '汽油', lpg: 'LPG' }[f] || f || '—')

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, any> = { page: query.page, page_size: query.page_size }
    if (query.keyword) params.keyword = query.keyword
    if (query.brand_id) params.brand_id = query.brand_id
    const res = await catalogApi.modelList(params)
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

function onEdit(row: ForkliftModel) {
  dialog.id = row.id
  dialog.form = {
    series_id: row.series_id, name: row.name, year_start: row.year_start,
    year_end: row.year_end, load_capacity_ton: row.load_capacity_ton,
    fuel_type: row.fuel_type || 'diesel',
  }
  dialog.visible = true
}

async function onSave() {
  if (!dialog.form.series_id || !dialog.form.name) {
    ElMessage.warning('所属系列和车型名称必填')
    return
  }
  dialog.saving = true
  try {
    if (dialog.id) await catalogApi.modelUpdate(dialog.id, dialog.form)
    else await catalogApi.modelCreate(dialog.form)
    ElMessage.success('已保存')
    dialog.visible = false
    loadData()
  } finally {
    dialog.saving = false
  }
}

async function onDelete(row: ForkliftModel) {
  await ElMessageBox.confirm(`确定删除车型「${row.name}」吗？关联图纸/手册需先处理。`, '提示', { type: 'warning' })
  await catalogApi.modelRemove(row.id)
  ElMessage.success('已删除')
  loadData()
}

onMounted(async () => {
  const [b, s] = await Promise.all([
    catalogApi.brandList({ page: 1, page_size: 200 }),
    catalogApi.seriesList({ page: 1, page_size: 500 }),
  ])
  brands.value = b.items
  series.value = s.items
  loadData()
})
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.pager { margin-top: 16px; justify-content: flex-end; }
</style>
