/**
 * 后台管理 API —— 对接后端 /api/v1/admin/*（53 个端点）
 * 所有写操作后端自动记录审计日志。
 */
import request from './request'
import type {
  AdminUser, AuditLog, Brand, DashboardStats, Diagram, EngineBrand,
  EngineModel, Enterprise, FaultCode, FaultTree, ForkliftModel,
  KnowledgeDoc, Model3D, PageResult, Part, Series,
} from './types'

// ========== 数据看板 ==========
export const dashboardApi = {
  stats: () => request.get<any, DashboardStats>('/admin/dashboard/stats'),
}

// ========== 用户管理 ==========
export const userApi = {
  list: (params: Record<string, any> = {}) =>
    request.get<any, PageResult<AdminUser>>('/admin/users', { params }),
  get: (id: number) =>
    request.get<any, AdminUser>(`/admin/users/${id}`),
  update: (id: number, data: Record<string, any>) =>
    request.put<any, AdminUser>(`/admin/users/${id}`, data),
}

// ========== 企业管理 ==========
export const enterpriseApi = {
  list: (params: Record<string, any> = {}) =>
    request.get<any, PageResult<Enterprise>>('/admin/enterprises', { params }),
  create: (data: Record<string, any>) =>
    request.post<any, Enterprise>('/admin/enterprises', data),
  update: (id: number, data: Record<string, any>) =>
    request.put<any, Enterprise>(`/admin/enterprises/${id}`, data),
  remove: (id: number) =>
    request.delete<any, { message: string }>(`/admin/enterprises/${id}`),
}

// ========== 目录管理：叉车品牌/系列/车型 ==========
export const catalogApi = {
  // 品牌
  brandList: (params: Record<string, any> = {}) =>
    request.get<any, PageResult<Brand>>('/admin/catalog/brands', { params }),
  brandCreate: (data: Record<string, any>) =>
    request.post<any, Brand>('/admin/catalog/brands', data),
  brandUpdate: (id: number, data: Record<string, any>) =>
    request.put<any, Brand>(`/admin/catalog/brands/${id}`, data),
  brandRemove: (id: number) =>
    request.delete<any, { message: string }>(`/admin/catalog/brands/${id}`),

  // 系列
  seriesList: (params: Record<string, any> = {}) =>
    request.get<any, PageResult<Series>>('/admin/catalog/series', { params }),
  seriesCreate: (data: Record<string, any>) =>
    request.post<any, Series>('/admin/catalog/series', data),
  seriesUpdate: (id: number, data: Record<string, any>) =>
    request.put<any, Series>(`/admin/catalog/series/${id}`, data),
  seriesRemove: (id: number) =>
    request.delete<any, { message: string }>(`/admin/catalog/series/${id}`),

  // 车型
  modelList: (params: Record<string, any> = {}) =>
    request.get<any, PageResult<ForkliftModel>>('/admin/catalog/models', { params }),
  modelCreate: (data: Record<string, any>) =>
    request.post<any, ForkliftModel>('/admin/catalog/models', data),
  modelUpdate: (id: number, data: Record<string, any>) =>
    request.put<any, ForkliftModel>(`/admin/catalog/models/${id}`, data),
  modelRemove: (id: number) =>
    request.delete<any, { message: string }>(`/admin/catalog/models/${id}`),

  // 发动机品牌
  engineBrandList: (params: Record<string, any> = {}) =>
    request.get<any, PageResult<EngineBrand>>('/admin/catalog/engine-brands', { params }),
  engineBrandCreate: (data: Record<string, any>) =>
    request.post<any, EngineBrand>('/admin/catalog/engine-brands', data),
  engineBrandUpdate: (id: number, data: Record<string, any>) =>
    request.put<any, EngineBrand>(`/admin/catalog/engine-brands/${id}`, data),
  engineBrandRemove: (id: number) =>
    request.delete<any, { message: string }>(`/admin/catalog/engine-brands/${id}`),

  // 发动机型号
  engineModelList: (params: Record<string, any> = {}) =>
    request.get<any, PageResult<EngineModel>>('/admin/catalog/engine-models', { params }),
  engineModelCreate: (data: Record<string, any>) =>
    request.post<any, EngineModel>('/admin/catalog/engine-models', data),
  engineModelUpdate: (id: number, data: Record<string, any>) =>
    request.put<any, EngineModel>(`/admin/catalog/engine-models/${id}`, data),
  engineModelRemove: (id: number) =>
    request.delete<any, { message: string }>(`/admin/catalog/engine-models/${id}`),

  // 配件
  partList: (params: Record<string, any> = {}) =>
    request.get<any, PageResult<Part>>('/admin/catalog/parts', { params }),
  partCreate: (data: Record<string, any>) =>
    request.post<any, Part>('/admin/catalog/parts', data),
  partUpdate: (id: number, data: Record<string, any>) =>
    request.put<any, Part>(`/admin/catalog/parts/${id}`, data),
  partRemove: (id: number) =>
    request.delete<any, { message: string }>(`/admin/catalog/parts/${id}`),
}

// ========== 资产管理 ==========
export const assetApi = {
  diagramList: (params: Record<string, any> = {}) =>
    request.get<any, PageResult<Diagram>>('/admin/assets/diagrams', { params }),
  diagramCreate: (data: Record<string, any>) =>
    request.post<any, Diagram>('/admin/assets/diagrams', data),
  diagramUpdate: (id: number, data: Record<string, any>) =>
    request.put<any, Diagram>(`/admin/assets/diagrams/${id}`, data),
  diagramRemove: (id: number) =>
    request.delete<any, { message: string }>(`/admin/assets/diagrams/${id}`),

  model3dList: (params: Record<string, any> = {}) =>
    request.get<any, PageResult<Model3D>>('/admin/assets/models3d', { params }),
  model3dUpdate: (id: number, data: Record<string, any>) =>
    request.put<any, Model3D>(`/admin/assets/models3d/${id}`, data),
  model3dRemove: (id: number) =>
    request.delete<any, { message: string }>(`/admin/assets/models3d/${id}`),
}

// ========== 知识库 / 故障数据 ==========
export const knowledgeApi = {
  docList: (params: Record<string, any> = {}) =>
    request.get<any, PageResult<KnowledgeDoc>>('/admin/knowledge/documents', { params }),
  docCreate: (data: Record<string, any>) =>
    request.post<any, KnowledgeDoc>('/admin/knowledge/documents', data),
  docUpdate: (id: number, data: Record<string, any>) =>
    request.put<any, KnowledgeDoc>(`/admin/knowledge/documents/${id}`, data),
  docRemove: (id: number) =>
    request.delete<any, { message: string }>(`/admin/knowledge/documents/${id}`),

  faultCodeList: (params: Record<string, any> = {}) =>
    request.get<any, PageResult<FaultCode>>('/admin/knowledge/fault-codes', { params }),
  faultCodeCreate: (data: Record<string, any>) =>
    request.post<any, FaultCode>('/admin/knowledge/fault-codes', data),
  faultCodeUpdate: (id: number, data: Record<string, any>) =>
    request.put<any, FaultCode>(`/admin/knowledge/fault-codes/${id}`, data),
  faultCodeRemove: (id: number) =>
    request.delete<any, { message: string }>(`/admin/knowledge/fault-codes/${id}`),

  faultTreeList: (params: Record<string, any> = {}) =>
    request.get<any, PageResult<FaultTree>>('/admin/knowledge/fault-trees', { params }),
  faultTreeCreate: (data: Record<string, any>) =>
    request.post<any, FaultTree>('/admin/knowledge/fault-trees', data),
  faultTreeUpdate: (id: number, data: Record<string, any>) =>
    request.put<any, FaultTree>(`/admin/knowledge/fault-trees/${id}`, data),
  faultTreeRemove: (id: number) =>
    request.delete<any, { message: string }>(`/admin/knowledge/fault-trees/${id}`),
}

// ========== 审计日志（仅超级管理员） ==========
export const auditApi = {
  list: (params: Record<string, any> = {}) =>
    request.get<any, PageResult<AuditLog>>('/admin/audit-logs', { params }),
}
