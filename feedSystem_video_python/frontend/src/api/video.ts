import { postJson } from './client'
import type { Video } from './types'

export type PublishVideoInput = {
  title: string
  description: string
  play_url: string
  cover_url: string
}

export function publishVideo(input: PublishVideoInput): Promise<Video> {
  /** 发布视频元数据；当前版本不上传文件，只保存播放地址和封面地址。 */
  return postJson<Video>('/video/publish', input, { authRequired: true })
}

export function listByAuthorId(authorId: number): Promise<Video[]> {
  /** 按作者 ID 查询视频列表，后端按发布时间倒序返回。 */
  return postJson<Video[]>('/video/listByAuthorID', { author_id: authorId })
}

export function getDetail(id: number): Promise<Video> {
  /** 查询视频详情；不带 token 也可以访问，带坏 token 会被软鉴权拒绝。 */
  return postJson<Video>('/video/getDetail', { id })
}
