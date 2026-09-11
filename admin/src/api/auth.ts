import request from './request'
import type { LoginUser } from './types'

export interface LoginResponse {
  access_token: string
  token_type: string
  user: LoginUser
}

export function login(phone: string, password: string) {
  return request.post<any, LoginResponse>('/auth/login', { phone, password })
}
