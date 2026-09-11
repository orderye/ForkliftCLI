/** 后端统一分页响应：PageOut<T> */
export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface PageQuery {
  page?: number
  page_size?: number
  keyword?: string
}

export interface LoginUser {
  id: number
  phone: string | null
  email: string | null
  nickname: string
  avatar: string
  role: string
}

export interface AdminUser extends LoginUser {
  enterprise_id: number | null
  enterprise_name: string
  status: string
  last_login_at: string | null
  is_super_admin: boolean
  created_at: string | null
}

export interface Enterprise {
  id: number
  name: string
  code: string
  contact_name: string
  contact_phone: string
  address: string
  plan: string
  plan_expire_at: string | null
  status: string
  created_at: string | null
  user_count: number
}

export interface Brand {
  id: number
  name: string
  name_en: string
  logo: string
  country: string
  series_count: number
}

export interface Series {
  id: number
  brand_id: number
  name: string
  description: string
  brand_name: string
  model_count: number
}

export interface ForkliftModel {
  id: number
  series_id: number
  name: string
  year_start: number | null
  year_end: number | null
  load_capacity_ton: number | null
  fuel_type: string
  image_url: string
  series_name: string
}

export interface EngineBrand {
  id: number
  name: string
  name_en: string
  country: string
  model_count: number
}

export interface EngineModel {
  id: number
  brand_id: number
  model_name: string
  displacement: string
  power_kw: number | null
  cylinders: number | null
  fuel_type: string
  brand_name: string
}

export interface Part {
  id: number
  oem_number: string
  name: string
  name_en: string
  category: string
  brand: string
  unit: string
  price_reference: number | null
}

export interface Diagram {
  id: number
  model_id: number | null
  diagram_type: string
  system_type: string
  title: string
  image_url: string
  hotspot_count: number
}

export interface Model3D {
  id: number
  forklift_model_id: number | null
  name: string
  file_url: string
  format: string
  version: number
  status: string
}

export interface KnowledgeDoc {
  id: number
  title: string
  content: string
  source: string
  doc_type: string
  forklift_model_id: number | null
  engine_model_id: number | null
  created_at: string | null
}

export interface FaultCode {
  id: number
  code: string
  description: string
  severity: string
  category: string
}

export interface FaultTree {
  id: number
  fault_code_id: number | null
  symptom: string
  causes_json: any[]
  solutions_json: any[]
}

export interface AuditLog {
  id: number
  admin_user_id: number
  action: string
  target_type: string
  target_id: number | null
  before_json: any
  after_json: any
  ip: string
  created_at: string | null
}

export interface DashboardStats {
  users: Record<string, number>
  catalog: Record<string, number>
  assets: Record<string, number>
  ai: Record<string, number>
  maintenance: Record<string, number>
}
