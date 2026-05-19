<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import { clearAuthState, readAuthState, saveLoginResponse } from './api/auth'
import { ApiError, getJson } from './api/client'
import { findById, login, logout, me, refresh, register } from './api/account'
import { listComments, publishComment } from './api/comment'
import { listByFollowing, listByTag, listLatest, listLikesCount } from './api/feed'
import { isLiked, likeVideo, unlikeVideo } from './api/like'
import { follow, unfollow } from './api/social'
import type { Account, Comment, FeedVideoItem, Video } from './api/types'
import { getDetail, publishVideo } from './api/video'

type LogItem = {
  time: string
  title: string
  payload: unknown
  ok: boolean
}

type DisplayVideo = {
  id: number
  authorId: number
  username: string
  title: string
  description: string
  playUrl: string
  coverUrl: string
  likesCount: number
  popularity?: number
  createTime: string | number
  isLiked?: boolean
}

const auth = reactive(readAuthState())
const healthStatus = ref('未检查')
const currentAccount = ref<Account | null>(null)
const feedVideos = ref<DisplayVideo[]>([])
const selectedVideo = ref<DisplayVideo | null>(null)
const comments = ref<Comment[]>([])
const logs = ref<LogItem[]>([])
const feedMode = ref<'latest' | 'likes' | 'following' | 'tag'>('latest')
const nextLatestTime = ref(0)
const nextFollowingTime = ref(0)
const nextTagTime = ref(0)
const nextLikesCount = ref<number | null>(null)
const nextLikesId = ref<number | null>(null)
const hasMore = ref(false)

const registerForm = reactive({ username: '', password: '' })
const loginForm = reactive({ username: '', password: '' })
const publishForm = reactive({
  title: '新的短视频',
  description: '这里先保存视频元数据，封面和视频用占位色块展示。',
  play_url: 'debug://video-placeholder',
  cover_url: 'debug://cover-placeholder',
})
const commentForm = reactive({ content: '这是一条前端页面发布的评论。' })
const searchForm = reactive({ accountId: 1 })
const tagForm = reactive({ tagName: '后端' })

const isLoggedIn = computed(() => Boolean(auth.token))
const shortToken = computed(() => (auth.token ? `${auth.token.slice(0, 18)}...` : '未登录'))

function syncAuth(): void {
  /** 把 localStorage 中的登录态同步到页面响应式状态。 */
  Object.assign(auth, readAuthState())
}

function addLog(title: string, payload: unknown, ok = true): void {
  /** 记录一次接口调用结果，右侧日志栏会展示最近的请求。 */
  logs.value.unshift({
    time: new Date().toLocaleTimeString(),
    title,
    payload,
    ok,
  })
  logs.value = logs.value.slice(0, 12)
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
  /** 统一包装接口调用，成功和失败都会进入右侧日志栏。 */
  try {
    const result = await action()
    addLog(title, result, true)
    return result
  } catch (error) {
    addLog(`${title} 失败`, getErrorPayload(error), false)
    return null
  } finally {
    syncAuth()
  }
}

function fromVideo(video: Video): DisplayVideo {
  /** 把视频详情接口返回的 Video 转成页面统一展示结构。 */
  return {
    id: video.id,
    authorId: video.author_id,
    username: video.username,
    title: video.title,
    description: video.description,
    playUrl: video.play_url,
    coverUrl: video.cover_url,
    likesCount: video.likes_count,
    popularity: video.popularity,
    createTime: video.create_time,
  }
}

function fromFeedVideo(video: FeedVideoItem): DisplayVideo {
  /** 把 FeedVideoItem 转成页面统一展示结构。 */
  return {
    id: video.id,
    authorId: video.author.id,
    username: video.author.username,
    title: video.title,
    description: video.description,
    playUrl: video.play_url,
    coverUrl: video.cover_url,
    likesCount: video.likes_count,
    createTime: video.create_time,
    isLiked: video.is_liked,
  }
}

function feedTitle(): string {
  /** 根据当前 Feed 模式返回页面标题。 */
  if (feedMode.value === 'latest') return '推荐视频'
  if (feedMode.value === 'likes') return '点赞榜'
  if (feedMode.value === 'following') return '关注流'
  return `标签流 #${tagForm.tagName}`
}

function feedSubtitle(): string {
  /** 根据当前 Feed 模式返回排序或筛选说明。 */
  if (feedMode.value === 'latest') return '按发布时间倒序'
  if (feedMode.value === 'likes') return '按点赞数和 ID 复合游标排序'
  if (feedMode.value === 'following') return '只看已关注作者的视频'
  return '按标题和描述中的 #tag 查询'
}

function placeholderStyle(video: DisplayVideo | null): Record<string, string> {
  /** 根据视频 ID 生成稳定色块，调试阶段用它替代真实封面图。 */
  const colors = ['#2563eb', '#0f766e', '#7c3aed', '#be123c', '#b45309', '#475569']
  const color = colors[(video?.id ?? 0) % colors.length] || '#2563eb'
  return { background: color }
}

function formatTime(value: string | number): string {
  /** 格式化后端返回的字符串时间或毫秒时间戳。 */
  const date = typeof value === 'number' ? new Date(value) : new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleString()
}

function selectVideo(video: DisplayVideo): void {
  /** 选中 Feed 中的视频，并拉取详情和评论。 */
  selectedVideo.value = video
  void loadVideoDetail(video.id)
  void loadComments(video.id)
}

async function checkHealth(): Promise<void> {
  /** 调用后端健康检查，确认 Vite 代理和 FastAPI 都能响应。 */
  const result = await runAction('健康检查', () => getJson<{ status: string }>('/health'))
  healthStatus.value = result?.status === 'ok' ? '正常' : '异常'
}

async function onRegister(): Promise<void> {
  /** 提交注册表单，后端会写入 accounts 表。 */
  await runAction('注册账号', () => register(registerForm.username, registerForm.password))
}

async function onLogin(): Promise<void> {
  /** 登录成功后保存双 token，并刷新当前用户和 Feed。 */
  const result = await runAction('登录账号', () => login(loginForm.username, loginForm.password))
  if (!result) return
  saveLoginResponse(result)
  syncAuth()
  searchForm.accountId = result.account_id
  await onMe()
  await refreshCurrentFeed()
}

async function onRefresh(): Promise<void> {
  /** 手动刷新 access token，观察 token 续签链路。 */
  if (!auth.refreshToken) {
    addLog('刷新 Token 失败', { message: '没有 refresh token' }, false)
    return
  }
  const result = await runAction('刷新 Token', () => refresh(auth.refreshToken))
  if (result) {
    saveLoginResponse(result)
    syncAuth()
  }
}

async function onLogout(): Promise<void> {
  /** 登出后清空本地 token，并刷新 Feed 的游客状态。 */
  const result = await runAction('登出账号', () => logout())
  if (!result) return
  clearAuthState()
  syncAuth()
  currentAccount.value = null
  await refreshCurrentFeed()
}

async function onMe(): Promise<void> {
  /** 查询当前登录用户，验证 Authorization 请求头是否生效。 */
  const result = await runAction('当前用户', () => me())
  if (result) currentAccount.value = result
}

async function onFindAccount(): Promise<void> {
  /** 按 ID 查询公开账号信息，保留给调试作者数据使用。 */
  const result = await runAction('按 ID 查用户', () => findById(searchForm.accountId))
  if (result) currentAccount.value = result
}

async function onPublishVideo(): Promise<void> {
  /** 发布视频元数据；当前阶段封面和视频用 debug 占位值。 */
  const result = await runAction('发布视频', () => publishVideo({ ...publishForm }))
  if (!result) return
  selectedVideo.value = fromVideo(result)
  await refreshCurrentFeed()
}

async function refreshCurrentFeed(): Promise<void> {
  /** 根据当前 Feed 模式刷新第一页。 */
  if (feedMode.value === 'latest') {
    await loadLatest(true)
  } else if (feedMode.value === 'likes') {
    await loadLikesFeed(true)
  } else if (feedMode.value === 'following') {
    await loadFollowingFeed(true)
  } else {
    await loadTagFeed(true)
  }
}

async function loadLatest(reset = false): Promise<void> {
  /** 加载最新 Feed；reset 为 true 时重新从第一页开始。 */
  feedMode.value = 'latest'
  const cursor = reset ? 0 : nextLatestTime.value
  const result = await runAction('最新 Feed', () => listLatest(8, cursor))
  if (!result) return
  const items = result.video_list.map(fromFeedVideo)
  feedVideos.value = reset ? items : [...feedVideos.value, ...items]
  nextLatestTime.value = result.next_time
  hasMore.value = result.has_more
  if (!selectedVideo.value && feedVideos.value[0]) selectVideo(feedVideos.value[0])
}

async function loadLikesFeed(reset = false): Promise<void> {
  /** 加载点赞榜 Feed；reset 为 true 时清空复合游标。 */
  feedMode.value = 'likes'
  const likesCursor = reset ? null : nextLikesCount.value
  const idCursor = reset ? null : nextLikesId.value
  const result = await runAction('点赞榜 Feed', () => listLikesCount(8, likesCursor, idCursor))
  if (!result) return
  const items = result.video_list.map(fromFeedVideo)
  feedVideos.value = reset ? items : [...feedVideos.value, ...items]
  nextLikesCount.value = result.next_likes_count_before ?? null
  nextLikesId.value = result.next_id_before ?? null
  hasMore.value = result.has_more
  if (!selectedVideo.value && feedVideos.value[0]) selectVideo(feedVideos.value[0])
}

async function loadFollowingFeed(reset = false): Promise<void> {
  /** 加载关注流；这个接口需要登录态。 */
  feedMode.value = 'following'
  const cursor = reset ? 0 : nextFollowingTime.value
  const result = await runAction('关注流 Feed', () => listByFollowing(8, cursor))
  if (!result) return
  const items = result.video_list.map(fromFeedVideo)
  feedVideos.value = reset ? items : [...feedVideos.value, ...items]
  nextFollowingTime.value = result.next_time
  hasMore.value = result.has_more
  if (!selectedVideo.value && feedVideos.value[0]) selectVideo(feedVideos.value[0])
}

async function loadTagFeed(reset = false): Promise<void> {
  /** 加载标签流；tagName 可以带 #，后端会统一去掉前缀。 */
  feedMode.value = 'tag'
  const cursor = reset ? 0 : nextTagTime.value
  const result = await runAction('标签流 Feed', () => listByTag(tagForm.tagName, 8, cursor))
  if (!result) return
  const items = result.video_list.map(fromFeedVideo)
  feedVideos.value = reset ? items : [...feedVideos.value, ...items]
  nextTagTime.value = result.next_time
  hasMore.value = result.has_more
  if (!selectedVideo.value && feedVideos.value[0]) selectVideo(feedVideos.value[0])
}

async function loadMore(): Promise<void> {
  /** 加载当前 Feed 模式的下一页。 */
  if (feedMode.value === 'latest') {
    await loadLatest(false)
  } else if (feedMode.value === 'likes') {
    await loadLikesFeed(false)
  } else if (feedMode.value === 'following') {
    await loadFollowingFeed(false)
  } else {
    await loadTagFeed(false)
  }
}

async function loadVideoDetail(id: number): Promise<void> {
  /** 拉取视频详情，并在登录时顺便刷新是否点赞状态。 */
  const result = await runAction('视频详情', () => getDetail(id))
  if (!result) return
  selectedVideo.value = fromVideo(result)
  if (isLoggedIn.value) {
    const liked = await runAction('是否点赞', () => isLiked(id))
    if (liked && selectedVideo.value?.id === id) selectedVideo.value.isLiked = liked.is_liked
  }
}

async function onLike(): Promise<void> {
  /** 点赞当前视频，成功后刷新详情和当前 Feed。 */
  if (!selectedVideo.value) return
  const id = selectedVideo.value.id
  const result = await runAction('点赞视频', () => likeVideo(id))
  if (!result) return
  await loadVideoDetail(id)
  await refreshCurrentFeed()
}

async function onUnlike(): Promise<void> {
  /** 取消点赞当前视频，成功后刷新详情和当前 Feed。 */
  if (!selectedVideo.value) return
  const id = selectedVideo.value.id
  const result = await runAction('取消点赞', () => unlikeVideo(id))
  if (!result) return
  await loadVideoDetail(id)
  await refreshCurrentFeed()
}

async function onFollowAuthor(): Promise<void> {
  /** 关注当前视频作者，用来验证 socials 表和关注流。 */
  if (!selectedVideo.value) return
  const result = await runAction('关注作者', () => follow(selectedVideo.value!.authorId))
  if (!result) return
  await loadFollowingFeed(true)
}

async function onUnfollowAuthor(): Promise<void> {
  /** 取消关注当前视频作者，用来验证关注关系删除。 */
  if (!selectedVideo.value) return
  const result = await runAction('取消关注作者', () => unfollow(selectedVideo.value!.authorId))
  if (!result) return
  await loadFollowingFeed(true)
}

async function loadComments(videoId: number): Promise<void> {
  /** 拉取当前视频的评论列表。 */
  const result = await runAction('评论列表', () => listComments(videoId))
  if (result) comments.value = result
}

async function onPublishComment(): Promise<void> {
  /** 给当前视频发布评论，成功后刷新评论列表和详情。 */
  if (!selectedVideo.value) return
  const id = selectedVideo.value.id
  const result = await runAction('发布评论', () => publishComment(id, commentForm.content))
  if (!result) return
  commentForm.content = ''
  await loadComments(id)
  await loadVideoDetail(id)
}

onMounted(async () => {
  /** 页面加载后同步登录态，检查后端，并加载最新 Feed。 */
  syncAuth()
  if (auth.accountId) searchForm.accountId = auth.accountId
  await checkHealth()
  await loadLatest(true)
})
</script>

<template>
  <div class="app-frame">
    <main class="product-shell">
      <aside class="app-nav">
        <div class="brand-block">
          <strong>ShortVideo</strong>
          <span>Python MVP</span>
        </div>
        <nav>
          <button type="button" :class="{ active: feedMode === 'latest' }" @click="loadLatest(true)">推荐</button>
          <button type="button" :class="{ active: feedMode === 'likes' }" @click="loadLikesFeed(true)">点赞榜</button>
          <button type="button" :class="{ active: feedMode === 'following' }" @click="loadFollowingFeed(true)">关注流</button>
          <button type="button" :class="{ active: feedMode === 'tag' }" @click="loadTagFeed(true)">标签流</button>
          <button type="button" @click="checkHealth">健康检查</button>
        </nav>
        <div class="nav-status">
          <span :class="{ ok: healthStatus === '正常' }" />
          <p>后端 {{ healthStatus }}</p>
        </div>
      </aside>

      <section class="main-surface">
        <header class="site-header">
          <div>
            <p class="eyebrow">feedSystem Video Python</p>
            <h1>视频流</h1>
          </div>
          <div class="session-panel">
            <div class="session-user">
              <span :class="{ online: isLoggedIn }" />
              <strong>{{ isLoggedIn ? auth.username || '已登录' : '游客模式' }}</strong>
              <small>{{ shortToken }}</small>
            </div>
            <details class="auth-popover">
              <summary>{{ isLoggedIn ? '账号' : '登录 / 注册' }}</summary>
              <div class="auth-menu">
                <form class="stack-form" @submit.prevent="onLogin">
                  <input v-model.trim="loginForm.username" placeholder="登录用户名" autocomplete="username" />
                  <input v-model="loginForm.password" type="password" placeholder="密码" autocomplete="current-password" />
                  <button type="submit">登录</button>
                </form>
                <form class="stack-form" @submit.prevent="onRegister">
                  <input v-model.trim="registerForm.username" placeholder="注册用户名" autocomplete="username" />
                  <input v-model="registerForm.password" type="password" placeholder="密码" autocomplete="new-password" />
                  <button type="submit" class="ghost">注册</button>
                </form>
                <div class="menu-actions">
                  <button type="button" class="ghost" @click="onMe">当前用户</button>
                  <button type="button" class="ghost" @click="onRefresh">刷新 Token</button>
                  <button type="button" class="danger" @click="onLogout">登出</button>
                </div>
              </div>
            </details>
          </div>
        </header>

        <section class="content-grid">
        <section class="feed-column">
          <div class="section-head">
            <div>
              <h2>{{ feedTitle() }}</h2>
              <p>{{ feedSubtitle() }}</p>
            </div>
            <button type="button" class="ghost" @click="refreshCurrentFeed">刷新</button>
          </div>
          <form v-if="feedMode === 'tag'" class="tag-filter" @submit.prevent="loadTagFeed(true)">
            <input v-model.trim="tagForm.tagName" placeholder="输入标签，例如 后端 或 #Python" />
            <button type="submit" class="ghost">查询</button>
          </form>

          <div class="feed-list">
            <button
              v-for="video in feedVideos"
              :key="`${feedMode}-${video.id}`"
              type="button"
              class="feed-card"
              :class="{ selected: selectedVideo?.id === video.id }"
              @click="selectVideo(video)"
            >
              <div class="cover-placeholder" :style="placeholderStyle(video)">
                <span>V{{ video.id }}</span>
              </div>
              <div class="feed-card-body">
                <strong>{{ video.title }}</strong>
                <p>{{ video.description || '暂无描述' }}</p>
                <small>#{{ video.id }} · {{ video.username }} · {{ video.likesCount }} 赞</small>
              </div>
            </button>
          </div>

          <button v-if="hasMore" type="button" class="load-more" @click="loadMore">加载下一页</button>
        </section>

        <section class="detail-column">
          <article class="video-stage">
            <div class="video-placeholder" :style="placeholderStyle(selectedVideo)">
              <span>{{ selectedVideo ? `VIDEO ${selectedVideo.id}` : 'NO VIDEO' }}</span>
            </div>
            <div v-if="selectedVideo" class="video-meta">
              <span>作者 #{{ selectedVideo.authorId }} {{ selectedVideo.username }}</span>
              <h2>{{ selectedVideo.title }}</h2>
              <p>{{ selectedVideo.description || '暂无描述' }}</p>
              <div class="meta-row">
                <strong>{{ selectedVideo.likesCount }} 赞</strong>
                <strong v-if="selectedVideo.popularity !== undefined">热度 {{ selectedVideo.popularity }}</strong>
                <small>{{ formatTime(selectedVideo.createTime) }}</small>
              </div>
              <div class="button-row">
                <button type="button" @click="onLike">点赞</button>
                <button type="button" class="ghost" @click="onUnlike">取消点赞</button>
                <button type="button" class="ghost" @click="onFollowAuthor">关注作者</button>
                <button type="button" class="ghost" @click="onUnfollowAuthor">取关作者</button>
                <button type="button" class="ghost" @click="loadVideoDetail(selectedVideo.id)">刷新详情</button>
              </div>
            </div>
            <div v-else class="empty-state">选择一个视频查看详情</div>
          </article>

          <section class="publish-panel">
            <div class="section-head">
              <div>
                <h2>发布视频</h2>
                <p>当前用 debug URL 入库，画面用色块替代真实资源。</p>
              </div>
            </div>
            <form class="publish-form" @submit.prevent="onPublishVideo">
              <input v-model.trim="publishForm.title" placeholder="标题" />
              <textarea v-model.trim="publishForm.description" rows="3" placeholder="描述" />
              <div class="two-col">
                <input v-model.trim="publishForm.play_url" placeholder="播放地址" />
                <input v-model.trim="publishForm.cover_url" placeholder="封面地址" />
              </div>
              <button type="submit">发布</button>
            </form>
          </section>

          <section class="comment-panel">
            <div class="section-head">
              <div>
                <h2>评论</h2>
                <p>{{ selectedVideo ? `视频 #${selectedVideo.id}` : '选择视频后可评论' }}</p>
              </div>
              <button
                v-if="selectedVideo"
                type="button"
                class="ghost"
                @click="loadComments(selectedVideo.id)"
              >
                刷新
              </button>
            </div>
            <form class="comment-form" @submit.prevent="onPublishComment">
              <input v-model.trim="commentForm.content" placeholder="写一条评论" />
              <button type="submit">发送</button>
            </form>
            <div class="comment-list">
              <article v-for="comment in comments" :key="comment.id">
                <strong>{{ comment.username }}</strong>
                <p>{{ comment.content }}</p>
                <small>#{{ comment.id }} · {{ formatTime(comment.created_at) }}</small>
              </article>
            </div>
          </section>
          </section>
        </section>
      </section>
    </main>

    <aside class="log-sidebar">
      <div class="log-header">
        <div>
          <h2>接口日志</h2>
          <p>{{ shortToken }}</p>
        </div>
        <button type="button" class="ghost" @click="logs = []">清空</button>
      </div>
      <div class="quick-query">
        <input v-model.number="searchForm.accountId" type="number" min="1" />
        <button type="button" @click="onFindAccount">查用户</button>
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
    </aside>
  </div>
</template>
