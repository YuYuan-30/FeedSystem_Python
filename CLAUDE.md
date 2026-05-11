# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository structure

```
feedSystem_video/
├── feedsystem_video_go/      # Complete Go reference implementation
│   └── CLAUDE.md             # Go-specific build/architecture/patterns
├── feedSystem_video_python/   # Python reconstruction (work in progress)
└── 项目核心.md                # Architecture deep-dive & 10-stage learning roadmap
```

This is a dual-project workspace: the Go project is the **reference implementation**, and the Python project is a **staged reconstruction** following the 10-stage roadmap in `项目核心.md`. When working on the Python project, the Go code serves as design reference — understand it first, then implement idiomatically in Python, not as a line-by-line translation.

## Go reference project

See `feedsystem_video_go/CLAUDE.md` for Go-specific build commands, architecture, core patterns, and testing. Quick start:

```bash
cd feedsystem_video_go
docker compose up -d --build          # everything
# or just dependencies:
docker compose up -d mysql redis rabbitmq
cd backend
CONFIG_PATH=configs/config.compose-local.yaml go run ./cmd       # API
CONFIG_PATH=configs/config.compose-local.yaml go run ./cmd/worker # Worker
```

## Python reconstruction

The `feedSystem_video_python/` directory is a ground-up Python rewrite for learning backend engineering concepts. No files exist yet. The `项目核心.md` document defines a 10-stage roadmap where each stage introduces one new concept:

| Stage | Focus | Key concepts |
|-------|-------|-------------|
| 1 | Project skeleton + user CRUD | FastAPI, SQLAlchemy, bcrypt, Pydantic |
| 2 | Auth system | JWT dual-token (access + refresh), middleware, soft auth |
| 3 | Video + likes + comments | File upload, transactions, @mention extraction |
| 4 | Feed pagination | Cursor, composite cursor, snapshot pagination |
| 5 | Caching | L1 memory → L2 Redis → L3 MySQL, cache stampede prevention |
| 6 | Hot ranking | Redis ZSET sliding windows, snapshot aggregation |
| 7 | Message queue | RabbitMQ async-first + DB fallback, DLX retry |
| 8 | Real-time notifications | SSE push, in-memory hub |
| 9 | Social + messaging | Consolidation — apply earlier patterns independently |
| 10 | Production readiness | Docker Compose, rate limiting, tests, structured logging |

Recommended Python stack: FastAPI, SQLAlchemy + Alembic, redis-py (async), aio-pika, PyJWT, bcrypt/passlib, sse-starlette, cachetools.

### Development approach

- Read the relevant section of `项目核心.md`, then read the Go source, then implement in Python with the Go code closed.
- Each stage should produce a runnable, testable system before moving to the next.
- The MVP is stages 1-4 + 10 (skip caching, MQ, hot ranking, SSE, social, messaging).

## Key architectural document

`项目核心.md` contains the complete system architecture: 10 database tables, JWT dual-token design, the async-first-with-fallback pattern for likes/comments/follows, three-level caching, hot/cold timeline separation, sliding-window popularity ranking, RabbitMQ topology, SSE notification flow, and rate limiting. Read it before touching any implementation.
