export type MessageResponse = {
  message: string
}

export type LoginResponse = {
  token: string
  refresh_token: string
  account_id: number
  username: string
}

export type Account = {
  id: number
  username: string
  avatar_url: string
  bio: string
}

export type Video = {
  id: number
  author_id: number
  username: string
  title: string
  description: string
  play_url: string
  cover_url: string
  likes_count: number
  popularity: number
  create_time: string
}

export type FeedAuthor = {
  id: number
  username: string
}

export type FeedVideoItem = {
  id: number
  author: FeedAuthor
  title: string
  description: string
  play_url: string
  cover_url: string
  create_time: number
  likes_count: number
  is_liked: boolean
}

export type ListLatestResponse = {
  video_list: FeedVideoItem[]
  next_time: number
  has_more: boolean
}

export type ListByFollowingResponse = ListLatestResponse

export type ListByTagResponse = ListLatestResponse

export type ListLikesCountResponse = {
  video_list: FeedVideoItem[]
  next_likes_count_before?: number | null
  next_id_before?: number | null
  has_more: boolean
}

export type IsLikedResponse = {
  is_liked: boolean
}

export type Comment = {
  id: number
  video_id: number
  author_id: number
  username: string
  content: string
  created_at: string
}

export type SocialFollowersResponse = {
  followers: Account[]
  follower_count: number
}

export type SocialVloggersResponse = {
  vloggers: Account[]
  vlogger_count: number
}

export type SocialCountsResponse = {
  follower_count: number
  vlogger_count: number
}

export type ApiErrorBody = {
  detail?: string
  error?: string
}
