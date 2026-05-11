# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Architecture

This is a TikTok-like short-video feed system with two independently deployable Go processes sharing the same `internal/` code:

- **API server** (`cmd/main.go`) — Gin HTTP server on :8080. Handles all client requests. Starts outbox/Timeline/SSE workers inline.
- **Worker** (`cmd/worker/main.go`) — RabbitMQ consumer. Runs Like/Comment/Social/Popularity workers that asynchronously persist events to MySQL/Redis.

The project is a microservices-oriented monolith. Redis and RabbitMQ are optional dependencies — when unavailable, the system degrades gracefully to synchronous MySQL writes.

**Request flow**: All endpoints use POST with JSON bodies. No GET/PUT/DELETE. Auth uses `Authorization: Bearer <jwt>` header.

**Key directories**:
```
backend/
  cmd/              Entry points (main.go, worker/main.go)
  configs/          YAML configs (local, docker, compose-local)
  internal/
    account/        Registration, login, profile (bcrypt + JWT)
    auth/           JWT generation (HS256, 15min) and refresh tokens
    config/         YAML loader with env var overrides
    db/             GORM init + AutoMigrate
    feed/           Five feed types (latest, likes, popularity, following, tag)
    http/           Gin router — all route registrations live here
    message/        Direct messaging between users
    middleware/      JWT (strict + soft), rate limiter, Redis helpers, RabbitMQ publishers
    social/         Follow/unfollow
    video/          Video CRUD, likes, comments, tags, popularity cache
    worker/         Async consumers + SSE notification hub
```

## Build & Run

```bash
# One-shot Docker Compose (everything)
docker compose up -d --build

# Local dev — start dependencies only
docker compose up -d mysql redis rabbitmq

# API server
cd backend
CONFIG_PATH=configs/config.compose-local.yaml go run ./cmd

# Worker (separate terminal)
CONFIG_PATH=configs/config.compose-local.yaml go run ./cmd/worker

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

All-in-one script: `./start.sh` (set `START_FRONTEND=0` to skip frontend).

## Configuration

Config is loaded from YAML with environment variable overrides. Three config files under `configs/`:
- `config.yaml` — localhost defaults
- `config.docker.yaml` — Docker service names as hosts
- `config.compose-local.yaml` — Docker MySQL on port 3307

Key env vars: `JWT_SECRET`, `CONFIG_PATH`, `MYSQL_HOST/PORT/USER/PASSWORD/DATABASE`, `REDIS_HOST/PORT/PASSWORD/DB`, `RABBITMQ_HOST/PORT/USER/PASS`.

## Testing

```bash
cd backend
go test ./...                              # all tests
go test -v ./internal/middleware/redis/    # specific package
```

No test database required — use the existing test in `middleware/redis/redis_test.go` as a pattern.

## Core Patterns

### Async-first with DB fallback (likes, comments, follows)
The most important pattern. API publishes to RabbitMQ and returns immediately. If MQ publish fails, falls back to a direct MySQL transaction. This means RabbitMQ can be down and writes still succeed. See `internal/video/like_service.go` for the canonical implementation.

### Three-level cache (video entities)
L1 (in-memory go-cache, 3s TTL) → L2 (Redis `video:entity:{id}`, 1h TTL) → L3 (MySQL). Each level uses `singleflight` to merge concurrent requests for the same key. See `internal/feed/service.go:GetVideoByIDs`.

### Hot/cold timeline separation (feed ListLatest)
Redis ZSET `feed:global_timeline` holds ~1000 latest video IDs. Requests with cursors newer than the oldest ZSET entry hit Redis (hot path). Older requests fall through to MySQL (cold path) and never write back to ZSET. When ZSET is empty, a global lock rebuilds it from the DB. See `internal/feed/service.go:ListLatest`.

### Sliding-window popularity ranking
Popularity changes write to per-minute ZSETs (`hot:video:1m:{YYYYMMDDHHMM}`). On read, `ZUNIONSTORE` merges the last 60 minute buckets into a snapshot with 2min TTL. Stable pagination uses this frozen snapshot. See `internal/feed/service.go:ListByPopularity`.

### Composite cursor pagination
For fields that can have duplicate values (e.g. likes_count), pagination uses a two-field cursor: `WHERE (likes_count < ? OR (likes_count = ? AND id < ?))`. The second field (id) guarantees stable ordering.

### Transactional outbox (video publish)
Video publish wraps `INSERT video + INSERT outbox_msg + INSERT tags` in a single GORM transaction. An outbox poller picks up pending messages and publishes to the timeline MQ, ensuring at-least-once delivery.

### Graceful degradation everywhere
Redis nil → cache disabled, direct DB reads. RabbitMQ nil → skip MQ, direct DB writes. This means the system works with just MySQL, and you add Redis/RabbitMQ for performance.

## Database

GORM AutoMigrate on startup (no migration files). Tables: accounts, videos, likes, comments, socials, outbox_msgs, tags, video_tags, messages, notifications. Composite unique indexes on `likes(video_id, account_id)` and `socials(follower_id, vlogger_id)`. Composite indexes for feed queries on `videos(popularity, create_time, id)` and `videos(likes_count, id)`.
