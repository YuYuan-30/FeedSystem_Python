import { postJson } from './client'
import type { Comment, MessageResponse } from './types'

export function publishComment(videoId: number, content: string): Promise<Comment> {
  /** 发布评论；后端会写 comments 表并提高视频热度。 */
  return postJson<Comment>('/comment/publish', { video_id: videoId, content }, { authRequired: true })
}

export function deleteComment(id: number): Promise<MessageResponse> {
  /** 删除评论；后端会校验只能删除自己的评论。 */
  return postJson<MessageResponse>('/comment/delete', { id }, { authRequired: true })
}

export function listComments(videoId: number): Promise<Comment[]> {
  /** 查询某个视频下的评论列表。 */
  return postJson<Comment[]>('/comment/listAll', { video_id: videoId })
}
