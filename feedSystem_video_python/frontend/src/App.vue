<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { clearAuthState, readAuthState, saveLoginResponse } from './api/auth'
import { ApiError, getJson } from './api/client'
import { findById, findByUsername, login, logout, me, refresh, register } from './api/account'
import type { Account, Video } from './api/types'
import { getDetail, listByAuthorId, publishVideo } from './api/video'

type LogItem = {
  time: string
  title: string
  payload: unknown
  ok: boolean
}

const auth = reactive(readAuthState())
const healthStatus = ref('未检查')
const currentAccount = ref<Account | null>(null)
const videos = ref<Video[]>([])
const selectedVideo = ref<Video | null>(null)
const logs = ref<LogItem[]>([])

const registerForm = reactive({ username: 'alice', password: '123456' })
const loginForm = reactive({ username: 'alice', password: '123456' })
const queryForm = reactive({ accountId: 1, username: 'alice' })
const videoForm = reactive({
  title: 'Day2 联调视频',
  description: '这是前端调用 FastAPI 发布的一条视频元数据。',
  play_url: 'https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4',
  cover_url: 'https://images.unsplash.com/photo-1490750967868-88aa4486c946?auto=format&fit=crop&w=900&q=80',
})
const videoQuery = reactive({ authorId: 1, detailId: 1 })

const isLoggedIn = computed(() => Boolean(auth.token))
const shortToken = computed(() => (auth.token ? `${auth.token.slice(0, 18)}...` : ''))

function syncAuth(): void {
  /** 把 localStorage 中的登录态同步到页面响应式状态。 */
  Object.assign(auth, readAuthState())
}

function addLog(title: string, payload: unknown, ok = true): void {
  /** 记录一次接口调用结果，方便观察前后端联调过程。 */
  logs.value.unshift({
    time: new Date().toLocaleTimeString(),
    title,
    payload,
    ok,
  })
  logs.value = logs.value.slice(0, 8)
}

function getErrorPayload(error: unknown): unknown {
  /** 把异常转换成适合展示的对象，ApiError 会保留后端响应体。 */
  if (error instanceof ApiError) {
    return { status: error.status, message: error.message, payload: error.payload }
  }
  if (error instanceof Error) return { message: error.message }
  return error
}

async function runAction<T>(title: string, action: () => Promise<T>): Promise<T | null> {
  /** 包一层通用执行器，统一处理成功日志和失败日志。 */
  try {
    const result = await action()
    addLog(title, result, true)
    return result
  } catch (error) {
    const payload = getErrorPayload(error)
    addLog(`${title} 失败`, payload, false)
    return null
  } finally {
    syncAuth()
  }
}

async function checkHealth(): Promise<void> {
  /** 调用后端健康检查，确认 Vite 代理和 FastAPI 都能正常响应。 */
  const result = await runAction('健康检查', () => getJson<{ status: string }>('/health'))
  healthStatus.value = result?.status === 'ok' ? '正常' : '异常'
}

async function onRegister(): Promise<void> {
  /** 提交注册表单，后端会写入 accounts 表。 */
  await runAction('注册账号', () => register(registerForm.username, registerForm.password))
}

async function onLogin(): Promise<void> {
  /** 提交登录表单，保存 access token 和 refresh token。 */
  const result = await runAction('登录账号', () => login(loginForm.username, loginForm.password))
  if (result) {
    saveLoginResponse(result)
    syncAuth()
    queryForm.accountId = result.account_id
    videoQuery.authorId = result.account_id
    loginForm.username = result.username
  }
}

async function onRefresh(): Promise<void> {
  /** 手动调用 refresh 接口，验证 refresh token 能换新 access token。 */
  if (!auth.refreshToken) {
    addLog('刷新 token 失败', { message: '没有 refresh token' }, false)
    return
  }
  const result = await runAction('刷新 token', () => refresh(auth.refreshToken))
  if (result) {
    saveLoginResponse(result)
    syncAuth()
  }
}

async function onLogout(): Promise<void> {
  /** 调用登出接口，成功后清空浏览器中的 token。 */
  const result = await runAction('登出账号', () => logout())
  if (result) {
    clearAuthState()
    syncAuth()
    currentAccount.value = null
  }
}

async function onMe(): Promise<void> {
  /** 调用当前用户接口，验证 Authorization 请求头是否携带成功。 */
  const result = await runAction('查询当前用户', () => me())
  if (result) currentAccount.value = result
}

async function onFindById(): Promise<void> {
  /** 按账号 ID 查询公开用户信息。 */
  const result = await runAction('按 ID 查用户', () => findById(queryForm.accountId))
  if (result) currentAccount.value = result
}

async function onFindByUsername(): Promise<void> {
  /** 按用户名查询公开用户信息。 */
  const result = await runAction('按用户名查用户', () => findByUsername(queryForm.username))
  if (result) currentAccount.value = result
}

async function onPublishVideo(): Promise<void> {
  /** 发布视频元数据，后端会使用 token 中的用户作为作者。 */
  const result = await runAction('发布视频', () => publishVideo({ ...videoForm }))
  if (result) {
    selectedVideo.value = result
    videoQuery.detailId = result.id
    videoQuery.authorId = result.author_id
    await onListByAuthor()
  }
}

async function onListByAuthor(): Promise<void> {
  /** 按作者 ID 拉取视频列表，用于确认 videos 表写入成功。 */
  const result = await runAction('查询作者视频', () => listByAuthorId(videoQuery.authorId))
  if (result) videos.value = result
}

async function onGetDetail(id = videoQuery.detailId): Promise<void> {
  /** 查询视频详情，演示软鉴权接口不登录也可以访问。 */
  const result = await runAction('查询视频详情', () => getDetail(id))
  if (result) {
    selectedVideo.value = result
    videoQuery.detailId = result.id
  }
}

function applyLoginToQuery(): void {
  /** 把当前登录用户 ID 填入查询表单，减少手动输入。 */
  if (auth.accountId) {
    queryForm.accountId = auth.accountId
    videoQuery.authorId = auth.accountId
  }
}

onMounted(async () => {
  /** 页面加载后先同步登录态，再检查后端健康状态。 */
  syncAuth()
  applyLoginToQuery()
  await checkHealth()
})
</script>

<template>
  <main class="app-shell">
    <section class="topbar">
      <div>
        <p class="eyebrow">feedSystem Video Python</p>
        <h1>Day1-2 前后端联调</h1>
      </div>
      <div class="status-row">
        <span class="status" :class="{ ok: healthStatus === '正常' }">后端：{{ healthStatus }}</span>
        <span class="status" :class="{ ok: isLoggedIn }">
          登录：{{ isLoggedIn ? auth.username || '已登录' : '未登录' }}
        </span>
      </div>
    </section>

    <section class="layout">
      <div class="panel">
        <div class="panel-title">
          <h2>账号链路</h2>
          <button type="button" class="ghost" @click="checkHealth">检查</button>
        </div>

        <form class="form-grid" @submit.prevent="onRegister">
          <label>
            注册用户名
            <input v-model.trim="registerForm.username" autocomplete="username" />
          </label>
          <label>
            注册密码
            <input v-model="registerForm.password" type="password" autocomplete="new-password" />
          </label>
          <button type="submit">注册</button>
        </form>

        <form class="form-grid" @submit.prevent="onLogin">
          <label>
            登录用户名
            <input v-model.trim="loginForm.username" autocomplete="username" />
          </label>
          <label>
            登录密码
            <input v-model="loginForm.password" type="password" autocomplete="current-password" />
          </label>
          <button type="submit">登录</button>
        </form>

        <div class="token-box">
          <div>
            <span>账号 ID</span>
            <strong>{{ auth.accountId || '-' }}</strong>
          </div>
          <div>
            <span>Access Token</span>
            <strong>{{ shortToken || '-' }}</strong>
          </div>
        </div>

        <div class="button-row">
          <button type="button" @click="onMe">当前用户</button>
          <button type="button" @click="onRefresh">刷新 Token</button>
          <button type="button" class="danger" @click="onLogout">登出</button>
        </div>

        <div class="query-card">
          <h3>用户查询</h3>
          <div class="inline-form">
            <input v-model.number="queryForm.accountId" type="number" min="1" />
            <button type="button" @click="onFindById">按 ID 查</button>
          </div>
          <div class="inline-form">
            <input v-model.trim="queryForm.username" />
            <button type="button" @click="onFindByUsername">按用户名查</button>
          </div>
        </div>

        <article v-if="currentAccount" class="result-card">
          <span>当前展示用户</span>
          <strong>#{{ currentAccount.id }} {{ currentAccount.username }}</strong>
          <p>{{ currentAccount.bio || '暂无简介' }}</p>
        </article>
      </div>

      <div class="panel">
        <div class="panel-title">
          <h2>视频链路</h2>
          <button type="button" class="ghost" @click="applyLoginToQuery">填入当前用户</button>
        </div>

        <form class="video-form" @submit.prevent="onPublishVideo">
          <label>
            标题
            <input v-model.trim="videoForm.title" />
          </label>
          <label>
            描述
            <textarea v-model.trim="videoForm.description" rows="3" />
          </label>
          <label>
            播放地址
            <input v-model.trim="videoForm.play_url" />
          </label>
          <label>
            封面地址
            <input v-model.trim="videoForm.cover_url" />
          </label>
          <button type="submit">发布视频</button>
        </form>

        <div class="query-card">
          <h3>视频查询</h3>
          <div class="inline-form">
            <input v-model.number="videoQuery.authorId" type="number" min="1" />
            <button type="button" @click="onListByAuthor">作者列表</button>
          </div>
          <div class="inline-form">
            <input v-model.number="videoQuery.detailId" type="number" min="1" />
            <button type="button" @click="onGetDetail()">查详情</button>
          </div>
        </div>

        <article v-if="selectedVideo" class="video-detail">
          <img :src="selectedVideo.cover_url" :alt="selectedVideo.title" />
          <div>
            <span>#{{ selectedVideo.id }} 作者 {{ selectedVideo.username }}</span>
            <h3>{{ selectedVideo.title }}</h3>
            <p>{{ selectedVideo.description || '暂无描述' }}</p>
            <a :href="selectedVideo.play_url" target="_blank" rel="noreferrer">打开播放地址</a>
          </div>
        </article>

        <div class="video-list">
          <button
            v-for="video in videos"
            :key="video.id"
            type="button"
            class="video-row"
            @click="onGetDetail(video.id)"
          >
            <img :src="video.cover_url" :alt="video.title" />
            <span>
              <strong>{{ video.title }}</strong>
              <small>#{{ video.id }} · {{ video.username }} · {{ video.likes_count }} 赞</small>
            </span>
          </button>
        </div>
      </div>
    </section>

    <section class="log-panel">
      <div class="panel-title">
        <h2>接口日志</h2>
        <button type="button" class="ghost" @click="logs = []">清空</button>
      </div>
      <div class="log-list">
        <article v-for="log in logs" :key="`${log.time}-${log.title}`" :class="{ error: !log.ok }">
          <header>
            <strong>{{ log.title }}</strong>
            <time>{{ log.time }}</time>
          </header>
          <pre>{{ JSON.stringify(log.payload, null, 2) }}</pre>
        </article>
      </div>
    </section>
  </main>
</template>
