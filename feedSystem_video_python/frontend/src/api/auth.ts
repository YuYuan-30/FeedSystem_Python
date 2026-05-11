import type { LoginResponse } from './types'

const ACCESS_KEY = 'feedsystem_access_token'
const REFRESH_KEY = 'feedsystem_refresh_token'
const ACCOUNT_ID_KEY = 'feedsystem_account_id'
const USERNAME_KEY = 'feedsystem_username'

export type AuthState = {
  token: string
  refreshToken: string
  accountId: number | null
  username: string
}

export function readAuthState(): AuthState {
  /** 从 localStorage 读取登录态，页面刷新后仍能继续联调接口。 */
  const accountId = Number(localStorage.getItem(ACCOUNT_ID_KEY) || '')
  return {
    token: localStorage.getItem(ACCESS_KEY) || '',
    refreshToken: localStorage.getItem(REFRESH_KEY) || '',
    accountId: Number.isFinite(accountId) && accountId > 0 ? accountId : null,
    username: localStorage.getItem(USERNAME_KEY) || '',
  }
}

export function saveLoginResponse(data: LoginResponse): AuthState {
  /** 保存登录或刷新接口返回的 token，并把账号基本信息一起缓存。 */
  localStorage.setItem(ACCESS_KEY, data.token)
  localStorage.setItem(REFRESH_KEY, data.refresh_token)
  localStorage.setItem(ACCOUNT_ID_KEY, String(data.account_id))
  localStorage.setItem(USERNAME_KEY, data.username)
  return readAuthState()
}

export function saveAccessToken(token: string): AuthState {
  /** 只更新 access token，用于 refresh token 成功后的本地状态同步。 */
  localStorage.setItem(ACCESS_KEY, token)
  return readAuthState()
}

export function clearAuthState(): AuthState {
  /** 清空本地登录态，通常在登出或 token 失效时调用。 */
  localStorage.removeItem(ACCESS_KEY)
  localStorage.removeItem(REFRESH_KEY)
  localStorage.removeItem(ACCOUNT_ID_KEY)
  localStorage.removeItem(USERNAME_KEY)
  return readAuthState()
}
