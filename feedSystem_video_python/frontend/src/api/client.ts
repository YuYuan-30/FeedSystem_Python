import { clearAuthState, readAuthState, saveAccessToken } from './auth'
import type { ApiErrorBody, LoginResponse } from './types'

const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined) ?? '/api'

let refreshingPromise: Promise<string | null> | null = null

export class ApiError extends Error {
  status: number
  payload: unknown

  constructor(message: string, status: number, payload: unknown) {
    /** 保存 HTTP 状态码和后端原始响应，方便页面展示调试信息。 */
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.payload = payload
  }
}

async function readBody(res: Response): Promise<unknown> {
  /** 读取响应体；后端返回空内容时统一给 null。 */
  const text = await res.text()
  if (!text) return null
  try {
    return JSON.parse(text)
  } catch {
    return text
  }
}

function getErrorMessage(data: unknown, status: number): string {
  /** 从 FastAPI 的 detail 字段或通用 error 字段里提取错误信息。 */
  if (data && typeof data === 'object') {
    const body = data as ApiErrorBody
    if (body.detail) return body.detail
    if (body.error) return body.error
  }
  return `请求失败：${status}`
}

async function handleResponse<T>(res: Response): Promise<T> {
  /** 统一处理 fetch 响应，非 2xx 时抛出 ApiError。 */
  const data = await readBody(res)
  if (!res.ok) {
    if (res.status === 401) clearAuthState()
    throw new ApiError(getErrorMessage(data, res.status), res.status, data)
  }
  return data as T
}

async function refreshAccessToken(): Promise<string | null> {
  /** access token 过期时尝试用 refresh token 换新 token。 */
  const auth = readAuthState()
  if (!auth.refreshToken) return null
  if (refreshingPromise) return refreshingPromise

  refreshingPromise = (async () => {
    try {
      const res = await fetch(`${API_BASE}/account/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: auth.refreshToken }),
      })
      if (!res.ok) {
        clearAuthState()
        return null
      }
      const data = await handleResponse<LoginResponse>(res)
      saveAccessToken(data.token)
      return data.token
    } catch {
      clearAuthState()
      return null
    } finally {
      refreshingPromise = null
    }
  })()

  return refreshingPromise
}

export async function getJson<T>(path: string): Promise<T> {
  /** 发送 GET 请求，当前主要用于健康检查。 */
  const res = await fetch(`${API_BASE}${path}`)
  return handleResponse<T>(res)
}

export async function postJson<T>(
  path: string,
  body: unknown,
  options: { authRequired?: boolean } = {},
): Promise<T> {
  /** 发送 JSON POST 请求，并在 401 时自动尝试刷新 access token 后重试一次。 */
  const auth = readAuthState()
  if (options.authRequired && !auth.token) {
    throw new ApiError('需要先登录', 401, null)
  }

  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (auth.token) headers.Authorization = `Bearer ${auth.token}`

  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body ?? {}),
  })

  if (res.status === 401 && path !== '/account/refresh' && auth.refreshToken) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      headers.Authorization = `Bearer ${newToken}`
      const retryRes = await fetch(`${API_BASE}${path}`, {
        method: 'POST',
        headers,
        body: JSON.stringify(body ?? {}),
      })
      return handleResponse<T>(retryRes)
    }
  }

  return handleResponse<T>(res)
}
