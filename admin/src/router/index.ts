import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/login/Login.vue'),
    meta: { public: true, title: '登录' },
  },
  {
    path: '/',
    component: () => import('@/layouts/AdminLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: () => import('@/views/dashboard/Dashboard.vue'),
        meta: { title: '数据看板', icon: 'DataAnalysis' },
      },
      {
        path: 'users',
        name: 'users',
        component: () => import('@/views/users/Users.vue'),
        meta: { title: '用户管理', icon: 'User' },
      },
      {
        path: 'enterprises',
        name: 'enterprises',
        component: () => import('@/views/enterprises/Enterprises.vue'),
        meta: { title: '企业管理', icon: 'OfficeBuilding' },
      },
      {
        path: 'catalog/brands',
        name: 'catalog-brands',
        component: () => import('@/views/catalog/Brands.vue'),
        meta: { title: '叉车品牌', icon: 'CollectionTag' },
      },
      {
        path: 'catalog/models',
        name: 'catalog-models',
        component: () => import('@/views/catalog/Models.vue'),
        meta: { title: '车型管理', icon: 'Van' },
      },
      {
        path: 'catalog/engines',
        name: 'catalog-engines',
        component: () => import('@/views/catalog/Engines.vue'),
        meta: { title: '发动机管理', icon: 'Setting' },
      },
      {
        path: 'catalog/parts',
        name: 'catalog-parts',
        component: () => import('@/views/catalog/Parts.vue'),
        meta: { title: '配件管理', icon: 'Box' },
      },
      {
        path: 'knowledge/documents',
        name: 'knowledge-documents',
        component: () => import('@/views/knowledge/Documents.vue'),
        meta: { title: '维修手册/知识库', icon: 'Document' },
      },
      {
        path: 'knowledge/faults',
        name: 'knowledge-faults',
        component: () => import('@/views/knowledge/Faults.vue'),
        meta: { title: '故障数据库', icon: 'Warning' },
      },
      {
        path: 'assets/diagrams',
        name: 'assets-diagrams',
        component: () => import('@/views/assets/Diagrams.vue'),
        meta: { title: '结构图管理', icon: 'Picture' },
      },
      {
        path: 'audit-logs',
        name: 'audit-logs',
        component: () => import('@/views/audit/AuditLogs.vue'),
        meta: { title: '审计日志', icon: 'List', superAdmin: true },
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isLoggedIn) {
    return { path: '/login', query: { redirect: to.fullPath } }
  }
  if (to.meta.superAdmin && !auth.isSuperAdmin) {
    return { path: '/dashboard' }
  }
  document.title = `${(to.meta.title as string) || ''} · ForkliftCLI 后台`
  return true
})

export default router
