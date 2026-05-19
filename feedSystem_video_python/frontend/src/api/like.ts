import { postJson } from './client'
import type { IsLikedResponse, MessageResponse } from './types'

export function likeVideo(videoId: number): Promise<MessageResponse> {
  /** 点赞视频；后端会同时写 likes 表并更新 videos.likes_count。 */
  return postJson<MessageResponse>('/like/like', { video_id: videoId }, { authRequired: true })
}

export function unlikeVideo(videoId: number): Promise<MessageResponse> {
  /** 取消点赞；后端会删除 likes 关系并安全减少计数。 */
  return postJson<MessageResponse>('/like/unlike', { video_id: videoId }, { authRequired: true })
}

export function isLiked(videoId: number): Promise<IsLikedResponse> {
  /** 查询当前登录用户是否点赞过该视频。 */
  return postJson<IsLikedResponse>('/like/isLiked', { video_id: videoId }, { authRequired: true })
}
