import { postJson } from './client'
import type { MessageResponse, SocialCountsResponse, SocialFollowersResponse, SocialVloggersResponse } from './types'

export function follow(vloggerId: number): Promise<MessageResponse> {
  /** 关注一个作者；后端会在 socials 表中写入 follower/vlogger 关系。 */
  return postJson<MessageResponse>('/social/follow', { vlogger_id: vloggerId })
}

export function unfollow(vloggerId: number): Promise<MessageResponse> {
  /** 取消关注一个作者；后端会删除 socials 表中的关系。 */
  return postJson<MessageResponse>('/social/unfollow', { vlogger_id: vloggerId })
}

export function getAllFollowers(vloggerId?: number): Promise<SocialFollowersResponse> {
  /** 查询粉丝列表；不传 vlogger_id 时默认查询当前登录用户。 */
  return postJson<SocialFollowersResponse>('/social/getAllFollowers', { vlogger_id: vloggerId ?? null })
}

export function getAllVloggers(followerId?: number): Promise<SocialVloggersResponse> {
  /** 查询关注列表；不传 follower_id 时默认查询当前登录用户。 */
  return postJson<SocialVloggersResponse>('/social/getAllVloggers', { follower_id: followerId ?? null })
}

export function getCounts(): Promise<SocialCountsResponse> {
  /** 查询当前用户的粉丝数和关注数。 */
  return postJson<SocialCountsResponse>('/social/getCounts', {})
}
