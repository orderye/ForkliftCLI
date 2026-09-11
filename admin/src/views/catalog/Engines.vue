<template>
  <el-card>
    <el-tabs v-model="tab">
      <!-- 发动机品牌 -->
      <el-tab-pane label="发动机品牌" name="brands">
        <div class="toolbar">
          <el-input v-model="brandQuery.keyword" placeholder="品牌名" clearable style="width: 200px" @keyup.enter="loadBrands" />
          <el-button type="primary" @click="loadBrands">查询</el-button>
          <el-button type="success" @click="onBrandAdd">新增品牌</el-button>
        </div>
        <el-table :data="brands" v-loading="brandLoading" border stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="name" label="品牌名称" min-width="160" />
          <el-table-column prop="name_en" label="英文名" min-width="140" />
          <el-table-column prop="country" label="国家" width="120" />
          <el-table-column prop="model_count" label="型号数" width="90" />
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="onBrandEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="onBrandDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          class="pager" layout="total, prev, pager, next"
          :total="brandTotal" :current-page="brandQuery.page" :page-size="brandQuery.page_size"
          @current-change="(p) => { brandQuery.page = p; loadBrands() }"
        />
      </el-tab-pane>

      <!-- 发动机型号 -->
      <el-tab-pane label="发动机型号" name="models">
        <div class="toolbar">
          <el-input v-model="modelQuery.keyword" placeholder="型号名" clearable style="width: 200px" @keyup.enter="loadModels" />
          <el-select v-model="modelQuery.brand_id" placeholder="品牌" clearable filterable style="width: 180px" @change="loadModels">
            <el-option v-for="b in brands" :key="b.id" :label="b.name" :value="b.id" />
          </el-select>
          <el-button type="primary" @click="loadModels">查询</el-button>
          <el-button type="success" @click="onModelAdd">新增型号</el-button>
        </div>
        <el-table :data="models" v-loading="modelLoading" border stripe>
          <el-table-column prop="id" label="ID" width="70" />
          <el-table-column prop="brand_name" label="品牌" width="140" />
          <el-table-column prop="model_name" label="型号" min-width="160" />
          <el-table-column prop="displacement" label="排量(L)" width="100" />
          <el-table-column prop="power_kw" label="功率(kW)" width="100" />
          <el-table-column prop="cylinders" label="缸数" width="80" />
          <el-table-column label="燃料" width="90">
            <template #default="{ row }">{{ fuelLabel(row.fuel_type) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="onModelEdit(row)">编辑</el-button>
              <el-button size="small" type="danger" @click="onModelDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-pagination
          class="pager" layout="total, prev, pager, next"
          :total="modelTotal" :current-page="modelQuery.page" :page-size="modelQuery.page_size"
          @current-change="(p) => { modelQuery.page = p; loadModels() }"
        />
      </el-tab-pane>
    </el-tabs>

    <!-- 品牌弹窗 -->
    <el-dialog v-model="brandDialog.visible" :title="brandDialog.id ? '编辑品牌' : '新增品牌'" width="440px">
      <el-form :model="brandDialog.form" label-width="80px">
        <el-form-item label="名称" required><el-input v-model="brandDialog.form.name" /></el-form-item>
        <el-form-item label="英文名"><el-input v-model="brandDialog.form.name_en" /></el-form-item>
        <el-form-item label="国家"><el-input v-model="brandDialog.form.country" /></el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="brandDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="brandDialog.saving" @click="onBrandSave">保存</el-button>
      </template>
    </el-dialog>

    <!-- 型号弹窗 -->
    <el-dialog v-model="modelDialog.visible" :title="modelDialog.id ? '编辑型号' : '新增型号'" width="480px">
      <el-form :model="modelDialog.form" label-width="90px">
        <el-form-item label="所属品牌" required>
          <el-select v-model="modelDialog.form.brand_id" filterable style="width: 100%">
            <el-option v-for="b in brands" :key="b.id" :label="b.name" :value="b.id" />
          </el-select>
        </el-form-item>
        <el-form-item label="型号名称" required><el-input v-model="modelDialog.form.model_name" /></el-form-item>
        <el-form-item label="排量(L)">
          <el-input v-model="modelDialog.form.displacement" placeholder="如 3.9" />
        </el-form-item>
        <el-form-item label="功率(kW)">
          <el-input-number v-model="modelDialog.form.power_kw" :min="0" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="缸数">
          <el-input-number v-model="modelDialog.form.cylinders" :min="1" :max="20" controls-position="right" style="width: 100%" />
        </el-form-item>
        <el-form-item label="燃料类型">
          <el-select v-model="modelDialog.form.fuel_type" style="width: 100%">
            <el-option label="柴油" value="diesel" />
            <el-option label="汽油" value="gasoline" />
            <el-option label="LPG" value="lpg" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="modelDialog.visible = false">取消</el-button>
        <el-button type="primary" :loading="modelDialog.saving" @click="onModelSave">保存</el-button>
      </template>
    </el-dialog>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { catalogApi } from '@/api/admin'
import type { EngineBrand, EngineModel } from '@/api/types'

const tab = ref('brands')
const fuelLabel = (f: string) => ({ diesel: '柴油', gasoline: '汽油', lpg: 'LPG' }[f] || f || '—')

// ---- 品牌 ----
const brandLoading = ref(false)
const brands = ref<EngineBrand[]>([])
const brandTotal = ref(0)
const brandQuery = reactive({ page: 1, page_size: 10, keyword: '' })
const brandDialog = reactive({
  visible: false, saving: false, id: 0,
  form: { name: '', name_en: '', country: '' },
})

async function loadBrands() {
  brandLoading.value = true
  try {
    const params: Record<string, any> = { page: brandQuery.page, page_size: brandQuery.page_size }
    if (brandQuery.keyword) params.keyword = brandQuery.keyword
    const res = await catalogApi.engineBrandList(params)
    brands.value = res.items
    brandTotal.value = res.total
  } finally {
    brandLoading.value = false
  }
}

function onBrandAdd() {
  brandDialog.id = 0
  brandDialog.form = { name: '', name_en: '', country: '' }
  brandDialog.visible = true
}

function onBrandEdit(row: EngineBrand) {
  brandDialog.id = row.id
  brandDialog.form = { name: row.name, name_en: row.name_en, country: row.country }
  brandDialog.visible = true
}

async function onBrandSave() {
  if (!brandDialog.form.name) return ElMessage.warning('品牌名称必填')
  brandDialog.saving = true
  try {
    if (brandDialog.id) await catalogApi.engineBrandUpdate(brandDialog.id, brandDialog.form)
    else await catalogApi.engineBrandCreate(brandDialog.form)
    ElMessage.success('已保存')
    brandDialog.visible = false
    loadBrands()
  } finally {
    brandDialog.saving = false
  }
}

async function onBrandDelete(row: EngineBrand) {
  await ElMessageBox.confirm(`确定删除品牌「${row.name}」吗？`, '提示', { type: 'warning' })
  await catalogApi.engineBrandRemove(row.id)
  ElMessage.success('已删除')
  loadBrands()
}

// ---- 型号 ----
const modelLoading = ref(false)
const models = ref<EngineModel[]>([])
const modelTotal = ref(0)
const modelQuery = reactive({ page: 1, page_size: 10, keyword: '', brand_id: null as number | null })
const modelDialog = reactive({
  visible: false, saving: false, id: 0,
  form: {
    brand_id: null as number | null, model_name: '',
    displacement: null as string | null, power_kw: null as number | null,
    cylinders: null as number | null, fuel_type: 'diesel',
  },
})

async function loadModels() {
  modelLoading.value = true
  try {
    const params: Record<string, any> = { page: modelQuery.page, page_size: modelQuery.page_size }
    if (modelQuery.keyword) params.keyword = modelQuery.keyword
    if (modelQuery.brand_id) params.brand_id = modelQuery.brand_id
    const res = await catalogApi.engineModelList(params)
    models.value = res.items
    modelTotal.value = res.total
  } finally {
    modelLoading.value = false
  }
}

function onModelAdd() {
  modelDialog.id = 0
  modelDialog.form = {
    brand_id: null, model_name: '', displacement: null,
    power_kw: null, cylinders: null, fuel_type: 'diesel',
  }
  modelDialog.visible = true
}

function onModelEdit(row: EngineModel) {
  modelDialog.id = row.id
  modelDialog.form = {
    brand_id: row.brand_id, model_name: row.model_name,
    displacement: row.displacement || null,
    power_kw: row.power_kw, cylinders: row.cylinders,
    fuel_type: row.fuel_type || 'diesel',
  }
  modelDialog.visible = true
}

async function onModelSave() {
  if (!modelDialog.form.brand_id || !modelDialog.form.model_name) {
    return ElMessage.warning('所属品牌和型号名称必填')
  }
  modelDialog.saving = true
  try {
    if (modelDialog.id) await catalogApi.engineModelUpdate(modelDialog.id, modelDialog.form)
    else await catalogApi.engineModelCreate(modelDialog.form)
    ElMessage.success('已保存')
    modelDialog.visible = false
    loadModels()
  } finally {
    modelDialog.saving = false
  }
}

async function onModelDelete(row: EngineModel) {
  await ElMessageBox.confirm(`确定删除型号「${row.model_name}」吗？`, '提示', { type: 'warning' })
  await catalogApi.engineModelRemove(row.id)
  ElMessage.success('已删除')
  loadModels()
}

onMounted(() => {
  loadBrands()
  loadModels()
})
</script>

<style scoped>
.toolbar { display: flex; gap: 12px; margin-bottom: 16px; }
.pager { margin-top: 16px; justify-content: flex-end; }
</style>
