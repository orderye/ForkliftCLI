<template>
  <el-container class="layout">
    <el-aside width="220px" class="aside">
      <div class="logo">
        <el-icon size="22"><Tools /></el-icon>
        <span>ForkliftCLI 后台</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        router
        background-color="#001529"
        text-color="#a6adb4"
        active-text-color="#ffffff"
      >
        <el-menu-item
          v-for="item in visibleMenus"
          :key="item.path"
          :index="item.path"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="header">
        <div class="header-title">{{ route.meta.title }}</div>
        <el-dropdown @command="onCommand">
          <span class="user-info">
            <el-icon><UserFilled /></el-icon>
            {{ auth.user?.nickname || '管理员' }}
            <el-tag size="small" type="primary" effect="plain" class="role-tag">
              {{ roleLabel }}
            </el-tag>
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>

      <el-main class="main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const allMenus = [
  { path: '/dashboard', title: '数据看板', icon: 'DataAnalysis', superAdmin: false },
  { path: '/users', title: '用户管理', icon: 'User', superAdmin: false },
  { path: '/enterprises', title: '企业管理', icon: 'OfficeBuilding', superAdmin: false },
  { path: '/catalog/brands', title: '叉车品牌', icon: 'CollectionTag', superAdmin: false },
  { path: '/catalog/models', title: '车型管理', icon: 'Van', superAdmin: false },
  { path: '/catalog/engines', title: '发动机管理', icon: 'Setting', superAdmin: false },
  { path: '/catalog/parts', title: '配件管理', icon: 'Box', superAdmin: false },
  { path: '/knowledge/documents', title: '维修手册/知识库', icon: 'Document', superAdmin: false },
  { path: '/knowledge/faults', title: '故障数据库', icon: 'Warning', superAdmin: false },
  { path: '/assets/diagrams', title: '结构图管理', icon: 'Picture', superAdmin: false },
  { path: '/audit-logs', title: '审计日志', icon: 'List', superAdmin: true },
]

const visibleMenus = computed(() =>
  allMenus.filter((m) => !m.superAdmin || auth.isSuperAdmin),
)

const activeMenu = computed(() => route.path)

const roleLabel = computed(() => (auth.isSuperAdmin ? '超级管理员' : '运营管理员'))

async function onCommand(command: string) {
  if (command === 'logout') {
    await ElMessageBox.confirm('确定退出登录吗？', '提示', { type: 'warning' })
    auth.logout()
    router.push('/login')
  }
}
</script>

<style scoped>
.layout {
  height: 100%;
}
.aside {
  background: #001529;
  overflow-x: hidden;
}
.logo {
  height: 60px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  padding: 0 20px;
  white-space: nowrap;
}
.aside :deep(.el-menu) {
  border-right: none;
}
.header {
  background: #fff;
  border-bottom: 1px solid #ebeef5;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.header-title {
  font-size: 16px;
  font-weight: 600;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: #303133;
}
.role-tag {
  margin: 0 4px;
}
.main {
  background: #f0f2f5;
  padding: 16px;
}
</style>
