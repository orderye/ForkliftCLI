<template>
  <div v-loading="loading">
    <el-row :gutter="16">
      <el-col v-for="card in cards" :key="card.title" :span="8">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-title">{{ card.title }}</div>
          <el-row :gutter="12" class="stat-row">
            <el-col
              v-for="item in card.items"
              :key="item.label"
              :span="8"
              class="stat-item"
            >
              <div class="stat-value" :style="{ color: item.color }">{{ item.value }}</div>
              <div class="stat-label">{{ item.label }}</div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { dashboardApi } from '@/api/admin'
import type { DashboardStats } from '@/api/types'

const loading = ref(false)
const stats = ref<DashboardStats | null>(null)

const cards = computed(() => {
  const s = stats.value
  return [
    {
      title: '用户与企业',
      items: [
        { label: '总用户', value: s?.users.total ?? '-', color: '#409eff' },
        { label: '技师', value: s?.users.technicians ?? '-', color: '#67c23a' },
        { label: '企业', value: s?.users.enterprises ?? '-', color: '#e6a23c' },
      ],
    },
    {
      title: '车型目录',
      items: [
        { label: '品牌', value: s?.catalog.brands ?? '-', color: '#409eff' },
        { label: '车型', value: s?.catalog.models ?? '-', color: '#67c23a' },
        { label: '配件', value: s?.catalog.parts ?? '-', color: '#e6a23c' },
      ],
    },
    {
      title: '资产与知识库',
      items: [
        { label: '3D模型', value: s?.assets.models3d ?? '-', color: '#409eff' },
        { label: '手册文档', value: s?.ai.knowledge_documents ?? '-', color: '#67c23a' },
        { label: '故障代码', value: s?.ai.fault_codes ?? '-', color: '#f56c6c' },
      ],
    },
  ]
})

onMounted(async () => {
  loading.value = true
  try {
    stats.value = await dashboardApi.stats()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.stat-card {
  margin-bottom: 16px;
}
.stat-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #303133;
}
.stat-item {
  text-align: center;
}
.stat-value {
  font-size: 26px;
  font-weight: 700;
}
.stat-label {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
