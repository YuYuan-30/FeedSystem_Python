# feedSystem_video_python 5 天学习与重构计划

## 0. 学习目标

这个 Python 重构项目不是为了把 Go 版本逐行翻译一遍，而是为了通过一个可运行的短视频 Feed 系统，建立后端开发的核心经验，并能在面试中讲清楚：

- 一个后端项目如何分层：API / Service / Repository / Model / Core。
- 数据库表如何设计，索引为什么这样建。
- JWT 鉴权、密码加密、登录态失效怎么做。
- Feed 流为什么要用游标分页，而不是简单 offset。
- Redis 在项目中扮演什么角色：缓存、限流、热榜、可选依赖。
- MQ 为什么能优化写链路，以及暂时不做 MQ 时如何预留扩展点。

5 天内的目标是：做出一个能跑、能演示、能讲的 MVP。代码不追求覆盖 Go 项目的所有细节，但关键思想必须理解。

## 1. 我们的协作方式

每个功能都按这个节奏推进：

1. 先讲思想：为什么要这样设计，它解决什么问题，有什么取舍。
2. 再看 Go 项目对应实现：只看关键流程，不逐行翻译。
3. 再写 Python 代码：用 FastAPI / SQLAlchemy 的习惯写法。
4. 亲手敲练习：关键代码块放到 `learning/*_practice.py`，先讲清为什么这样写，再让你对照实现敲一遍。
5. 最后复盘：把这一段整理成面试可说的话。

我后续会把一些“小而关键”的代码做成练习，例如：

```python
# 练习：先理解 bcrypt 校验为什么不可逆，再对照真实实现亲手敲一遍
```

这些练习不会影响主程序运行。它们的目标不是“刷代码”，而是让你真正理解关键链路为什么这样设计。

## 2. 本轮重构范围

### 必做

- FastAPI 项目骨架
- MySQL 数据库接入
- SQLAlchemy 模型与 Repository 层
- 用户注册 / 登录 / JWT 鉴权 / Refresh Token
- 视频发布 / 查询详情 / 作者视频列表
- 点赞 / 取消点赞 / 是否点赞
- 评论发布 / 删除 / 列表
- Feed 最新流 / 点赞榜 / 关注流 / 标签流
- Redis 接入：可选依赖、视频详情缓存、Feed 短缓存、限流
- Docker Compose：只启动 MySQL + Redis；后端和前端都在本地开发环境运行
- 面试复盘文档或每阶段讲解笔记

### 暂不实现，但要预留

- RabbitMQ 真实接入
- Worker 独立进程
- SSE 实时通知
- 热榜滑动窗口完整实现
- 死信队列和重试机制

### 预留方式

MQ 暂不做真实 RabbitMQ，但 Service 层不要写死“只能同步写库”。我们预留一个事件发布接口：

```python
class EventPublisher:
    async def publish_like(self, account_id: int, video_id: int) -> bool:
        return False
```

现在它永远返回 `False`，业务自动走同步 MySQL 事务。以后接 RabbitMQ 时，只替换这个 Publisher，不大改 Service。

## 3. 推荐技术栈与运行方式

- Web：FastAPI
- ASGI Server：uvicorn
- ORM：SQLAlchemy 2.x async
- 数据库迁移：Alembic
- 数据库：MySQL 8.0
- Redis：redis-py asyncio
- 配置：pydantic-settings
- 密码：bcrypt 或 passlib[bcrypt]
- JWT：PyJWT 或 python-jose
- 测试：pytest + httpx
- 容器：Docker Compose 只管理 MySQL + Redis
- 后端本地运行：`uvicorn app.main:app --reload`
- 前端本地运行：复用 Go 项目前端或后续新建前端，使用 `npm run dev`

本项目的默认开发方式：

```text
本地进程:
  FastAPI API     http://127.0.0.1:8000
  前端开发服务     http://127.0.0.1:5173

Docker 容器:
  MySQL           localhost:3306 -> container:3306
  Redis           localhost:6379，无密码
```

这样做的好处：

- 后端代码改完自动 reload，方便学习和调试。
- 前端也能本地热更新，不需要每次重建镜像。
- MySQL / Redis 放在 Docker 里，避免本机安装和环境污染。
- 更接近真实开发：应用本地跑，依赖服务容器化。

## 4. 建议目录结构

```text
feedSystem_video_python/
  plan.md
  README.md
  docker-compose.yml
  pyproject.toml
  .env.example
  app/
    main.py
    config.py
    database.py
    models/
      account.py
      video.py
      social.py
      message.py
    schemas/
      account.py
      video.py
      feed.py
      common.py
    api/
      account.py
      video.py
      like.py
      comment.py
      feed.py
      social.py
    services/
      account_service.py
      video_service.py
      like_service.py
      comment_service.py
      feed_service.py
      social_service.py
    repositories/
      account_repo.py
      video_repo.py
      like_repo.py
      comment_repo.py
      feed_repo.py
      social_repo.py
    core/
      security.py
      auth.py
      redis.py
      cache.py
      ratelimit.py
      events.py
    learning/
      day1_notes.md
      day2_notes.md
      day3_notes.md
      day4_notes.md
      day5_notes.md
  alembic/
  tests/
```

## 5. 数据库表规划

先实现 7 张核心表：

| 表 | 用途 | 本阶段要求 |
|---|---|---|
| `accounts` | 用户、密码、token | 必做 |
| `videos` | 视频元数据、计数、热度 | 必做 |
| `likes` | 点赞关系 | 必做，联合唯一索引 |
| `comments` | 评论 | 必做 |
| `socials` | 关注关系 | 必做，联合唯一索引 |
| `tags` | 话题标签 | 必做 |
| `video_tags` | 视频-标签关系 | 必做 |

暂时预留但不重点实现：

| 表 | 用途 | 处理方式 |
|---|---|---|
| `messages` | 私信 | 可选 |
| `notifications` | 通知 | 预留 |
| `outbox_msgs` | 事务发件箱 | 只讲思想，可晚点加 |

关键索引：

- `accounts.username` 唯一索引。
- `likes(video_id, account_id)` 联合唯一索引。
- `socials(follower_id, vlogger_id)` 联合唯一索引。
- `videos(create_time)` 支持最新流。
- `videos(likes_count, id)` 支持点赞榜复合游标。
- `videos(popularity, create_time, id)` 预留热榜 DB fallback。

## 6. 接口规划

### Day 1-2：账号与鉴权

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| POST | `/account/register` | 否 | 注册 |
| POST | `/account/login` | 否 | 登录，返回 access + refresh |
| POST | `/account/refresh` | 否 | 刷新 access token |
| POST | `/account/logout` | 是 | 登出，主动失效 token |
| POST | `/account/findByID` | 否 | 查用户 |
| POST | `/account/findByUsername` | 否 | 查用户 |

### Day 2-3：视频、点赞、评论

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| POST | `/video/publish` | 是 | 发布视频元数据 |
| POST | `/video/listByAuthorID` | 否 | 作者视频列表 |
| POST | `/video/getDetail` | 软鉴权 | 视频详情，后续加缓存 |
| POST | `/like/like` | 是 | 点赞 |
| POST | `/like/unlike` | 是 | 取消点赞 |
| POST | `/like/isLiked` | 是 | 是否已赞 |
| POST | `/comment/publish` | 是 | 评论 |
| POST | `/comment/delete` | 是 | 删除评论 |
| POST | `/comment/listAll` | 否 | 评论列表 |

### Day 3-4：Feed 与社交

| 方法 | 路径 | 鉴权 | 说明 |
|---|---|---|---|
| POST | `/feed/listLatest` | 软鉴权 | 最新视频，游标分页 |
| POST | `/feed/listLikesCount` | 软鉴权 | 点赞榜，复合游标 |
| POST | `/feed/listByFollowing` | 是 | 关注流 |
| POST | `/feed/listByTag` | 软鉴权 | 标签流 |
| POST | `/social/follow` | 是 | 关注 |
| POST | `/social/unfollow` | 是 | 取关 |
| POST | `/social/getAllFollowers` | 是 | 粉丝列表 |
| POST | `/social/getAllVloggers` | 是 | 关注列表 |

### Day 4-5：Redis 与工程化

| 功能 | Key 设计 | 说明 |
|---|---|---|
| Token 缓存 | `v1:account:{id}` | JWT 校验先查 Redis，miss 后查 MySQL 并回填 |
| 视频详情缓存 | `v1:video:detail:{id}` | Cache-Aside，先 DB 后删缓存 |
| Feed 短缓存 | `v1:feed:latest:limit={n}:before={t}` | TTL 5 秒，减少重复请求 |
| 限流 | `v1:ratelimit:{scope}:{subject}` | Redis INCR + 首次设置 TTL |

## 7. 5 天学习安排

### Day 1：项目骨架、数据库、用户注册登录

学习主题：

- FastAPI 项目如何启动。
- 请求模型和响应模型为什么要分开。
- SQLAlchemy Model / Schema / Repository / Service 的边界。
- 密码为什么不能明文存，用 bcrypt 的意义。

完成内容：

- 搭建项目结构。
- 接入 MySQL。
- 建 `accounts` 表。
- 实现注册、登录。
- 先返回 access token，refresh token 可以在 Day 2 完善。

你需要亲手敲的重点：

练习位置：`backend/app/learning/day1_practice.py`

重点不是填空，而是理解这三段为什么重要：

- `hash_password`：密码为什么不能明文入库。
- `verify_password`：bcrypt 为什么是校验，不是解密。
- `find_by_username`：Repository 为什么只负责查询，不负责 HTTP 和业务判断。

面试能讲：

- 为什么密码要用 bcrypt。
- 为什么要分 Repository 和 Service。
- 为什么数据库模型不能直接当 API 响应随便返回。

验收标准：

- 能启动 FastAPI。
- Swagger 里能完成注册和登录。
- 数据库里能看到加密后的密码。

### Day 2：JWT 双 Token、鉴权依赖、视频发布

学习主题：

- JWT 的 header / payload / signature。
- Access Token 和 Refresh Token 的区别。
- FastAPI Depends 如何做鉴权。
- 硬鉴权和软鉴权的区别。

完成内容：

- 完成 access token + refresh token。
- 实现 `get_current_user`。
- 实现 `get_optional_user`。
- 实现登出与 token 主动失效。
- 建 `videos` 表。
- 实现视频发布、作者视频列表、视频详情。

你需要亲手敲的重点：

```python
# 练习：先理解 JWT 为什么能表达登录身份，再对照真实实现亲手敲一遍
# 1. create_access_token(account_id, username)
# 2. parse_access_token(token)
# 3. get_current_user()
```

面试能讲：

- JWT 为什么还要存在数据库里。
- logout 为什么能让 JWT 失效。
- 软鉴权为什么适合 Feed。

验收标准：

- 未登录不能发布视频。
- 登录后能发布视频。
- 不带 token 可以看视频详情。

### Day 3：点赞、评论、事务、基础 Feed 分页

学习主题：

- 为什么点赞要用事务。
- 计数冗余字段 `likes_count` 的意义。
- 唯一索引如何保证不能重复点赞。
- 游标分页为什么比 offset 更适合 Feed。

完成内容：

- 建 `likes`、`comments` 表。
- 点赞：插入 likes + 更新 videos.likes_count。
- 取消点赞：删除 likes + likes_count 防负数。
- 评论：发布、删除、列表。
- 最新 Feed：`create_time < cursor`。
- 点赞榜：`likes_count + id` 复合游标。

你需要亲手敲的重点：

```python
# 练习：先理解事务和复合游标解决什么问题，再对照真实实现亲手敲一遍
# 1. 点赞事务：insert like + update likes_count
# 2. 复合游标 WHERE:
#    likes_count < cursor_likes
#    OR (likes_count = cursor_likes AND id < cursor_id)
```

面试能讲：

- 为什么不能只查 `likes` 表动态 count。
- 为什么点赞数相同会导致分页重复或漏数据。
- 什么是复合游标。

验收标准：

- 同一个用户不能重复点赞。
- 取消点赞不会让计数变负数。
- Feed 连续翻页不重复。

### Day 4：关注、标签、Redis 缓存

学习主题：

- 关注关系为什么是多对多。
- `#话题` 标签如何建模。
- Redis 是性能层，不是数据真相。
- Cache-Aside：读缓存、miss 查 DB、回填缓存；写 DB 后删缓存。

完成内容：

- 建 `socials`、`tags`、`video_tags` 表。
- 实现关注、取关、粉丝列表、关注列表。
- 视频发布时提取 `#tag`。
- 实现标签流。
- 接入 Redis。
- 给视频详情加缓存。
- 给最新 Feed 加短 TTL 缓存。

你需要亲手敲的重点：

```python
# 练习：先理解标签提取和缓存回填为什么这样做，再对照真实实现亲手敲一遍
# 1. extract_tags("标题 #Python #后端")
# 2. get_video_detail: Redis miss -> DB -> Redis set
# 3. update video 后删除缓存 key
```

面试能讲：

- Redis 挂了为什么数据不会丢。
- 为什么写操作后是删缓存，而不是直接更新缓存。
- 为什么 Feed 缓存 TTL 要短。

验收标准：

- Redis 不启动时，核心接口仍然能用。
- Redis 启动时，视频详情第二次请求命中缓存。
- 发布带 `#tag` 的视频后能按标签查到。

### Day 5：限流、本地联调、Docker 依赖、复盘与面试表达

学习主题：

- 限流保护什么。
- Redis INCR + TTL 的固定窗口限流。
- Docker Compose 如何组织 MySQL / Redis 这类基础设施。
- 本地后端、前端如何连接 Docker 中的 MySQL / Redis。
- 如何把项目讲成面试故事。

完成内容：

- 注册、登录、点赞、评论限流。
- Docker Compose 一键启动 MySQL + Redis。
- 本地启动 FastAPI 后端。
- 本地启动前端开发服务，并通过代理访问后端。
- 写 `README.md` 启动说明。
- 写每个核心模块的面试讲法。
- 预留 MQ 扩展接口，不接 RabbitMQ。

你需要亲手敲的重点：

```python
# 练习：先理解限流和事件发布扩展点为什么存在，再对照真实实现亲手敲一遍
# 1. rate_limit dependency
# 2. Redis INCR + 第一次请求设置 expire
# 3. EventPublisher 的空实现
```

面试能讲：

- Redis 限流失败时为什么放行。
- 为什么 RabbitMQ 当前没做，但系统已预留扩展点。
- 如果后续加 MQ，点赞链路会怎么改。

验收标准：

- `docker compose up -d mysql redis` 能启动依赖。
- 本地 `uvicorn app.main:app --reload` 能启动后端。
- 本地 `npm run dev` 能启动前端。
- 主要接口能跑通一条完整链路：
  注册 -> 登录 -> 发布视频 -> 点赞 -> 评论 -> 刷 Feed。
- 你能用 2-3 分钟讲清项目。

## 8. MQ 预留设计

当前不接 RabbitMQ，但代码中保留三个位置：

### 8.1 事件发布接口

```python
class EventPublisher:
    async def publish_like(self, account_id: int, video_id: int) -> bool:
        return False

    async def publish_comment(self, account_id: int, video_id: int, content: str) -> bool:
        return False

    async def publish_follow(self, follower_id: int, vlogger_id: int) -> bool:
        return False
```

### 8.2 Service 层调用方式

```python
published = await publisher.publish_like(account_id, video_id)
if not published:
    await like_repo.like_directly(...)
```

这样以后变成：

```python
published = await rabbitmq_publisher.publish_like(account_id, video_id)
```

业务代码不用大改。

### 8.3 面试说法

当前 MVP 先使用同步 MySQL 事务保证强一致性。后续如果 QPS 上来，可以把点赞、评论、关注改成“异步优先 + DB 兜底”：API 先发布 MQ 成功就快速返回，MQ 不可用就走当前已经实现的同步事务路径。

## 9. 最小演示链路

最终 5 天结束时至少跑通：

```text
1. 注册用户 A
2. 登录用户 A
3. 用户 A 发布视频，标题带 #后端
4. 用户 A 查看自己的视频列表
5. 注册并登录用户 B
6. 用户 B 点赞 A 的视频
7. 用户 B 评论 A 的视频
8. 用户 B 关注 A
9. 用户 B 查看最新 Feed / 点赞榜 / 关注流 / 标签流
10. Redis 开启时观察缓存；Redis 关闭时核心功能仍可用
```

推荐启动顺序：

```bash
# 1. 启动基础设施
# 如果已经有 YYmysql / YYredis 在运行，可以跳过这一步。
docker compose up -d mysql redis

# 2. 启动后端
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 3. 启动前端
npm run dev
```

后端连接配置建议：

```text
DATABASE_URL=mysql+asyncmy://root:123456@127.0.0.1:3306/feedsystem
REDIS_URL=redis://127.0.0.1:6379/0
```

## 10. 面试主线

2-3 分钟介绍项目时可以这样组织：

```text
这是一个仿短视频平台的 Feed 流后端系统。我用 Python/FastAPI 重构 Go 参考项目，核心目标不是简单 CRUD，而是学习真实后端项目的分层、鉴权、事务、分页和缓存设计。

系统分为账号、视频、点赞、评论、关注和 Feed 六个核心模块。数据库用 MySQL 保存核心数据，Redis 作为可选性能层，用于 token 缓存、视频详情缓存、Feed 短缓存和限流。Feed 流部分没有用简单 offset，而是用游标分页和复合游标分页，解决深分页性能和排序字段重复导致的重复/漏数据问题。

写操作方面，当前 MVP 先用 MySQL 事务保证一致性，比如点赞会在一个事务里插入点赞关系并更新视频计数。RabbitMQ 暂时没有接入，但 Service 层预留了 EventPublisher 接口，后续可以平滑升级为异步优先、失败降级直写的模式。
```

## 11. 每天结束前的复盘问题

每天结束时至少回答这 3 个问题：

1. 今天这个模块解决了什么真实后端问题？
2. 如果面试官追问“为什么这样设计”，我怎么回答？
3. 这段代码里哪 20 行最关键，我是否能自己敲出来？

## 12. 5 天后的后续扩展

如果 5 天 MVP 完成，再按优先级扩展：

1. RabbitMQ：点赞、评论、关注异步化。
2. Worker：独立消费者进程。
3. 热榜：Redis ZSET 滑动窗口 + 快照分页。
4. SSE：实时通知。
5. 测试：pytest 覆盖核心 happy path。
6. 更完整的文件上传：本地存储 -> MinIO / OSS。

## 13. Day 5 之后的完善方向：先不接 MQ，但补足面试深度

根据 `E:\feedSystem_video\next.md` 对 Go 版本和 Python 版本的差距分析，Python 版本现在已经能完成账号、视频、点赞、评论、关注、标签、基础 Feed、Redis 缓存和限流的主链路。但是和 Go 版本相比，当前实现仍然更像“功能正确的 CRUD + 简单缓存”，还没有把 Feed 系统里最有面试价值的几个设计讲深：

- Redis ZSET 时间线与冷热分离。
- 视频详情的三级缓存、防击穿、分布式锁。
- 热榜的滑动窗口分钟桶。
- 事务发件箱 Outbox。
- 通知、账号安全、视频生命周期、测试与可观测性。

后续阶段仍然坚持一个原则：

```text
先不引入 RabbitMQ，不启动 Worker。
所有写操作继续以 MySQL 同步事务保证正确性。
Redis 仍然是性能层，失败时可以降级。
但是每个可能异步化的动作都预留事件边界，方便以后接 MQ。
```

这样做的好处是：你可以先学会 Go 版本里最值得讲的后端设计思想，同时不被 MQ、消费者、死信队列、重复消费这些额外复杂度打断。

## 14. 后续阶段安排

### Day 6：Redis 基础设施升级，重点学“缓存保护”

学习主题：

- 缓存穿透、击穿、雪崩分别是什么。
- 为什么热门 key 过期会把 MySQL 打爆。
- `SET NX EX` 分布式锁的基本思想。
- 为什么释放锁要校验随机 token，不能直接 `DEL key`。
- 本地 L1 缓存、Redis L2 缓存、MySQL L3 数据源分别解决什么问题。

完成内容：

- 在 `core/redis.py` 或新增 `core/redis_lock.py` 中封装 Redis 锁：
  - `try_acquire_lock(key, ttl)`
  - `release_lock(key, token)`
  - 锁 key 统一使用 `v1:lock:{业务key}`。
- 给视频详情缓存加防击穿：
  - 先查 Redis。
  - miss 后尝试抢锁。
  - 抢到锁后 double-check Redis。
  - 再查 MySQL 并回填缓存。
  - 没抢到锁时短暂等待并重试读缓存，仍失败再降级查 MySQL。
- 可选增加一个很短 TTL 的本地 L1 缓存，用来学习“进程内缓存”的价值，但不作为必须项。
- 把 Redis key 命名集中管理，减少到处手写字符串。

暂不做：

- 不做 RabbitMQ。
- 不做真正的 Go `singleflight` 完整复刻。
- 不追求压测，只做可解释、可验证的小并发场景。

预留接口：

```python
class CacheProtector:
    async def get_or_build(self, key: str, ttl: int, builder: Callable):
        ...
```

以后 Feed、关注流、热榜都可以复用这个“查缓存 -> 抢锁 -> 回源 -> 回填”的模式。

面试能讲：

> 我的视频详情不是简单 Cache-Aside，而是补了缓存击穿保护。热门视频缓存过期时，不让所有请求同时回源 MySQL，而是用 Redis `SET NX EX` 让一个请求构建缓存，其余请求短暂等待后读缓存。释放锁时用随机 token + Lua 脚本，避免误删别人的锁。

### Day 7：Feed 最新流升级，重点学“冷热分离 + ZSET 时间线”

学习主题：

- Redis ZSET 为什么适合做时间线。
- `score=create_time`、`member=video_id` 是什么含义。
- 热数据和冷数据为什么要分开。
- 为什么冷数据不要写回热 ZSET。
- 游标分页如何和 ZSET 的 score 查询结合。

完成内容：

- 新增全局时间线 Redis key：
  - `v1:feed:global_timeline`
  - member：`video_id`
  - score：视频发布时间戳。
- 发布视频成功后，在同步 MySQL 提交之后，直接尝试写入 ZSET。
  - Redis 写失败不影响发布成功。
  - 失败时最多记录日志，后续可通过重建时间线修复。
- `listLatest` 从“短 TTL 缓存”升级为“热路径 + 冷路径”：
  - 如果 ZSET 不存在或太少，用 Redis 锁保护一次重建。
  - 游标在 ZSET 水位线以内，走 Redis 热路径取 ID。
  - 热路径 ID 不够一页时，用 MySQL 冷路径补齐。
  - 游标已经很老时，直接走 MySQL 冷路径。
- Feed 组装视频详情时，可以先复用 Day 6 的缓存保护能力。

暂不做：

- 不接 timeline MQ。
- 不做独立 Worker 重建。
- 不做复杂的异步回填，只在 API 进程里同步尝试维护 ZSET。

预留接口：

```python
class TimelineWriter:
    async def add_video(self, video_id: int, create_time: datetime) -> None:
        ...

class EventPublisher:
    async def publish_video_created(self, video_id: int) -> bool:
        return False
```

现在发布视频后直接调用 `TimelineWriter.add_video`。以后接 MQ 时，可以把这个动作挪到 `video.created` 消费者里，API 层只负责发事件。

面试能讲：

> 最新 Feed 没有一直打 MySQL。我用 Redis ZSET 保存最近一批视频 ID，发布时间作为 score。新的请求优先走 Redis 热路径，老游标走 MySQL 冷路径。这样既让首页最新流很快，又避免把历史冷数据不断塞进 Redis，造成缓存污染。

### Day 8：热榜与 popularity，重点学“滑动窗口热度”

学习主题：

- 点赞数榜和热度榜有什么区别。
- 为什么热榜不能只看 MySQL `popularity` 总值。
- 为什么 Go 版本用“分钟桶”而不是一个大 ZSET。
- `ZINCRBY`、`ZUNIONSTORE`、快照分页分别解决什么问题。

完成内容：

- 先补一个 DB fallback 版热度榜接口：
  - `POST /feed/listByPopularity`
  - 排序：`popularity DESC, create_time DESC, id DESC`
  - 游标：`popularity + create_time + id`。
- 点赞、取消点赞、评论发布、评论删除继续同步更新 MySQL `popularity`。
- 再补 Redis 简化版热度写入：
  - 当前分钟桶：`v1:hot:video:1m:{yyyyMMddHHmm}`
  - 点赞 `+1`，取消点赞 `-1`，评论 `+1` 或自定义权重。
  - 每个分钟桶设置 2 小时 TTL。
- 可选实现“最近 60 分钟热榜快照”：
  - 把多个分钟桶合并到 `v1:hot:video:snapshot:{minute}`。
  - 查询热榜优先读快照，Redis 不可用回退 DB fallback。

暂不做：

- 不做 PopularityWorker。
- 不通过 MQ 更新热榜。
- 不追求复杂推荐算法，只学热度存储和分页稳定性。

预留接口：

```python
class PopularityWriter:
    async def increase(self, video_id: int, delta: int, reason: str) -> None:
        ...

class EventPublisher:
    async def publish_popularity_changed(self, video_id: int, delta: int, reason: str) -> bool:
        return False
```

现在 Service 直接调用 `PopularityWriter`。以后接 MQ 时，API 只发 `popularity.changed`，由 Worker 消费后写 Redis 热榜。

面试能讲：

> 点赞榜是累计值，适合用 MySQL 字段排序；热榜更关注最近一段时间的增量，所以我用 Redis ZSET 按分钟分桶写入热度。这样可以降低单个热榜 key 的写竞争，也能用最近 N 个分钟桶合并出滑动窗口榜单。

### Day 9：账号与视频生命周期，重点学“业务完整性”

学习主题：

- 为什么真实项目不只有注册登录。
- 改名、改密码为什么会影响 token。
- 删除视频时怎么处理点赞、评论、标签关系。
- 文件上传为什么要校验类型、大小和路径安全。

完成内容：

- 账号模块补充：
  - `POST /account/rename`
  - `POST /account/changePassword`
  - `POST /account/updateProfile`
  - 可选 `POST /account/updateAvatarUrl`，先不做真实文件上传。
- Token 策略：
  - 改名后重新签发 access token。
  - 改密码后清空 MySQL token、refresh token，并删除 Redis token，让旧登录态失效。
- 视频模块补充：
  - `POST /video/update`
  - `POST /video/delete`
  - 只有作者能改自己的视频。
  - 删除视频后同步删除或标记相关评论、点赞、标签关系。
  - 删除或更新后失效视频详情、Feed、作者列表相关缓存。
- 文件上传作为可选小阶段：
  - 本地保存封面和视频文件。
  - 限制大小。
  - 校验扩展名和 MIME。
  - 返回可访问的静态资源 URL。

暂不做：

- 不做对象存储。
- 不做视频转码。
- 不做复杂审核系统。

预留接口：

```python
class EventPublisher:
    async def publish_video_deleted(self, video_id: int) -> bool:
        return False
```

以后接 MQ 时，删除视频可以异步通知 timeline、hot ranking、notification 等模块清理派生数据。

面试能讲：

> 改密码不只是更新密码哈希，还要让旧 token 失效；删除视频不只是删 `videos` 一行，还要考虑点赞、评论、标签、Feed 缓存和热榜里的派生数据。这类功能体现的是业务一致性，而不是单表 CRUD。

### Day 10：通知系统，不接 MQ 也能学“事件副作用”

学习主题：

- 点赞、评论、关注为什么会产生通知。
- 通知是业务主流程还是副作用。
- 不接 MQ 时如何先同步创建通知。
- 以后接 MQ 时如何把通知创建挪到 Worker。

完成内容：

- 新增 `notifications` 表：
  - `id`
  - `receiver_id`
  - `sender_id`
  - `type`
  - `video_id`
  - `comment_id`
  - `content`
  - `is_read`
  - `created_at`
- 点赞、评论、关注成功后同步创建通知。
- 评论内容中提取 `@username`，给被提及用户创建 mention 通知。
- 新增接口：
  - `POST /notification/list`
  - `POST /notification/unreadCount`
  - `POST /notification/markRead`
- 前端右侧日志栏可以继续保留，同时主页面加一个简单通知入口。

暂不做：

- 不做 SSE 实时推送。
- 不做 RabbitMQ 通知消费者。
- 不做复杂去重聚合，例如“10 个人赞了你的视频”。

预留接口：

```python
class NotificationService:
    async def create_like_notification(...):
        ...

class EventPublisher:
    async def publish_notification_created(self, notification_id: int) -> bool:
        return False
```

以后接 MQ 时，点赞/评论/关注 Service 可以只发布事件，Notification Worker 负责生成通知；SSE Worker 再负责推送。

面试能讲：

> 我把通知看成主业务成功后的副作用。当前不接 MQ，所以先同步创建通知，保证用户能查到；但代码上保留事件边界，后续可以把通知创建和 SSE 推送迁到异步 Worker，避免主接口被通知逻辑拖慢。

### Day 11：测试、迁移与可观测性，重点学“工程可信度”

学习主题：

- 为什么项目能跑不等于项目可靠。
- 单元测试、接口测试、集成测试分别测什么。
- Alembic 迁移为什么比 `create_all()` 更适合长期项目。
- request id、结构化日志、错误响应统一有什么价值。

完成内容：

- 添加 pytest 测试：
  - 纯函数：标签提取、JWT 解析、Redis key 生成。
  - Service happy path：注册、登录、发布视频、点赞、评论。
  - 关键异常：重复点赞、未登录发布、越权删除。
- 增加一个简单的接口测试脚本或 Postman/HTTP 示例。
- 可选引入 Alembic：
  - 将当前表结构生成初始迁移。
  - 后续新增通知、outbox 等表都走迁移。
- 日志增强：
  - 每个请求生成 request id。
  - 关键写操作记录结构化日志。
  - 前端接口日志只作为调试视图，后端日志作为排障依据。

暂不做：

- 不追求完整覆盖率。
- 不引入复杂 APM。

面试能讲：

> 我不只验证接口能手动点通，还给关键业务补了测试。比如重复点赞依赖数据库唯一约束兜底，越权删除依赖 Service 层校验，这些都适合写测试固定下来。后续表结构变化也应该从 `create_all()` 过渡到 Alembic 迁移，避免线上环境不可控。

## 15. Outbox 作为 MQ 前的过渡能力

RabbitMQ 暂时不做，但可以先学习事务发件箱，因为它不要求真的接消息队列，却能解释“数据库写入”和“后续副作用”如何保持最终一致。

建议在 Day 8 或 Day 10 之后加入一个轻量 Outbox：

```text
outbox_msgs
  id
  event_type
  payload_json
  status        pending / processed / failed
  retry_count
  created_at
  updated_at
```

同步写业务数据时，在同一个 MySQL 事务里插入 outbox 事件：

```text
BEGIN
  INSERT videos ...
  INSERT outbox_msgs(event_type="video.created", payload={video_id})
COMMIT
```

当前不启动 Worker，可以先做两个简单能力：

1. 提供一个开发用接口或脚本查看 pending outbox。
2. 在 Service 成功后继续同步调用当前本地 writer，例如 `TimelineWriter`、`PopularityWriter`、`NotificationService`。

以后接 RabbitMQ 时：

```text
OutboxPoller 读取 pending outbox
  -> 发布到 RabbitMQ
  -> 成功后标记 processed
  -> 失败后 retry_count + 1
```

面试能讲：

> 如果直接“先写 DB，再发 MQ”，DB 成功但 MQ 失败时就会丢事件；如果“先发 MQ，再写 DB”，消费者可能看到还没提交的数据。Outbox 的核心是把业务数据和事件记录放在同一个事务里，至少保证事件不会丢。当前我还没接 RabbitMQ，但先把 outbox 表和事件边界留好，后续加 MQ 时就有可靠的发布来源。

## 16. 后续优先级建议

最推荐先做：

1. Day 6：视频详情缓存防击穿 + Redis 锁。
2. Day 7：最新 Feed ZSET 时间线 + 冷热分离。
3. Day 8：`/feed/listByPopularity` DB fallback + Redis 分钟桶。
4. Day 11：pytest 覆盖核心 happy path。

原因是这四个最能把项目从“能跑的业务系统”提升到“能讲后端设计取舍的项目”。

可以稍后做：

1. Day 9：账号改密、改名、视频更新删除。
2. Day 10：通知系统和 `@mention`。
3. 文件上传。
4. Alembic 迁移。

暂时继续不做：

1. RabbitMQ 真接入。
2. Worker 独立进程。
3. 死信队列和重试拓扑。
4. SSE 实时推送。

## 17. 新阶段的学习纪律

从 Day 6 开始，每个阶段都要继续保留三类产物：

1. 代码实现：功能必须能跑通。
2. `learning/dayX_notes.md`：写清楚函数链路、数据流、输入输出、缓存/DB/MQ 预留点。
3. `learning/dayX_practice.py`：只挑最关键的 2-3 段让你对照敲，不为了敲代码而敲代码。

每阶段结束时必须补充面试素材：

```text
这个阶段解决了什么真实后端问题？
为什么 Go 版本要这么设计？
Python 版本这次实现了哪一层？
暂时没做 MQ 时如何保证正确性？
以后接 MQ 时要替换哪个接口？
```
