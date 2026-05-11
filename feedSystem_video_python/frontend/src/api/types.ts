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

export type ApiErrorBody = {
  detail?: string
  error?: string
}
