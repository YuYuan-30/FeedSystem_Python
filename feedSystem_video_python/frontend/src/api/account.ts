import { postJson } from './client'
import type { Account, LoginResponse, MessageResponse } from './types'

export function register(username: string, password: string): Promise<MessageResponse> {
  /** 调用注册接口，后端会完成用户名查重和密码哈希入库。 */
  return postJson<MessageResponse>('/account/register', { username, password })
}

export function login(username: string, password: string): Promise<LoginResponse> {
  /** 调用登录接口，成功后返回 access token 和 refresh token。 */
  return postJson<LoginResponse>('/account/login', { username, password })
}

export function refresh(refreshToken: string): Promise<LoginResponse> {
  /** 用 refresh token 换取新的 access token。 */
  return postJson<LoginResponse>('/account/refresh', { refresh_token: refreshToken })
}

export function logout(): Promise<MessageResponse> {
  /** 调用登出接口，让 MySQL 和 Redis 中的当前 token 失效。 */
  return postJson<MessageResponse>('/account/logout', {}, { authRequired: true })
}

export function me(): Promise<Account> {
  /** 调用当前用户接口，用来验证 Authorization 请求头是否正确。 */
  return postJson<Account>('/account/me', {}, { authRequired: true })
}

export function findById(id: number): Promise<Account> {
  /** 按用户 ID 查询公开账号信息。 */
  return postJson<Account>('/account/findByID', { id })
}

export function findByUsername(username: string): Promise<Account> {
  /** 按用户名查询公开账号信息。 */
  return postJson<Account>('/account/findByUsername', { username })
}
