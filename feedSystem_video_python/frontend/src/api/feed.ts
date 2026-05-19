import { postJson } from './client'
import type { ListByFollowingResponse, ListByTagResponse, ListLatestResponse, ListLikesCountResponse } from './types'

export function listLatest(limit: number, latestTime = 0): Promise<ListLatestResponse> {
  /** 查询最新 Feed；latest_time 为上一页最后一条视频的毫秒时间戳。 */
  return postJson<ListLatestResponse>('/feed/listLatest', { limit, latest_time: latestTime })
}

export function listLikesCount(
  limit: number,
  likesCountBefore?: number | null,
  idBefore?: number | null,
): Promise<ListLikesCountResponse> {
  /** 查询点赞榜 Feed；使用 likes_count + id 复合游标。 */
  return postJson<ListLikesCountResponse>('/feed/listLikesCount', {
    limit,
    likes_count_before: likesCountBefore ?? null,
    id_before: idBefore ?? null,
  })
}

export function listByFollowing(limit: number, latestTime = 0): Promise<ListByFollowingResponse> {
  /** 查询关注 Feed；需要登录，latest_time 为上一页最后一条视频的毫秒时间戳。 */
  return postJson<ListByFollowingResponse>('/feed/listByFollowing', { limit, latest_time: latestTime })
}

export function listByTag(tagName: string, limit: number, latestTime = 0): Promise<ListByTagResponse> {
  /** 查询标签 Feed；tag_name 可以传 Python 或 #Python，后端会统一处理。 */
  return postJson<ListByTagResponse>('/feed/listByTag', {
    tag_name: tagName,
    limit,
    latest_time: latestTime,
  })
}
