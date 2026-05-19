# Python 版本 vs Go 版本：差距分析

> 本文档对比 `feedSystem_video_python`（Python/FastAPI 重构）与 `feedsystem_video_go`（Go/Gin 参考实现），
> 梳理 Python 版本已实现部分相比 Go 版本的不足，重点是流程简化导致的实现深度差异。
> 目标：为面试准备提供清晰的"还有什么可以深入学"的路线图。

## 先说结论

Python 版本目前完成了 Stages 1-4 的核心功能（约 40% 的 Go 版本），且在 **Feed 流系统** 这个最核心的模块上做了大幅简化——Go 版本的冷热分离、滑动窗口热榜、三级缓存、分布式锁防击穿等关键设计，Python 版本基本都降级成了"直接查 MySQL + 简单 Redis 缓存"。对于面试准备来说，**这些被简化的地方恰恰是最值得讲的技术亮点**。

Go 版本是一个**可以上生产的系统**（有 MQ 异步、多级缓存保护、限流、可观测性、Worker 独立部署、降级兜底），而 Python 版本目前是一个**功能正确的 CRUD 系统**（API → Service → Repository → DB，加了一层简单 Redis 缓存）。两者的差距不在功能数量，而在**对高并发和故障场景的防御深度**。

---

## 一、已声明暂不实现的部分（Roadmap Stages 6-10）

这些在 `process.md` 中明确写了"后续再做"，属于规划内的未完成项：

| 模块 | Go 版本 | 教学价值 |
|------|---------|----------|
| **RabbitMQ 消息队列** | 4 个 Topic Exchange + DLX 死信重试 + 独立 Worker 进程 | 异步优先+降级兜底模式（整个项目最有教学价值的设计） |
| **SSE 实时通知** | SSE Hub + 心跳保活 + 通知持久化 | SSE vs WebSocket 的选择理由 |
| **热度排行榜（滑动窗口）** | 60 分钟桶 ZUNIONSTORE 快照分页 | ZSET 高级用法、快照解决翻页抖动 |
| **限流系统** | Redis Lua 脚本 INCR + PEXPIRE | 滑动窗口限流的原子性保证 |
| **Worker 独立进程** | Like/Comment/Social/Popularity Worker + OutboxPoller | 双进程可独立伸缩的部署架构 |
| **pprof 可观测性** | API/Worker 各自暴露 pprof 端点 | 生产环境性能诊断 |
| **测试** | miniredis 单元测试 | 测试 Redis 相关逻辑的方式 |
| **私信系统** | send/list 端点 | 巩固 CRUD 能力 |

---

## 二、已实现但深度明显不足的部分

### 差距 1：Feed 最新流 — 从"冷热分离"简化成了"5 秒缓存"（差距最大）

**Go 版本（`internal/feed/service.go:ListLatest`）：**

```
ListLatest(limit, cursor, viewerID):
  ├─ ZSET feed:global_timeline 为空？
  │   └─ YES → global lock (singleflight) 重建 ZSET（从 MySQL 捞 1000 条）
  │
  ├─ 对比 cursor 和 ZSET 最老数据时间戳 watermark
  │
  ├─ cursor > watermark → 【热数据路径】
  │   ├─ ZRevRangeByScore 从 Redis ZSET 取 ID 列表
  │   ├─ 三级缓存 (L1内存→L2 Redis→L3 MySQL) 获取视频实体
  │   └─ 数量不够 limit → 拼接冷数据 (singleflight)
  │
  └─ cursor <= watermark → 【冷数据路径】
      ├─ 直接查 MySQL
      └─ 不回写 ZSET（防止冷数据污染热榜）
```

**Python 版本（`app/services/feed_service.py:list_latest`）：**

```python
# 整个逻辑只有这些
cache_key = f"v1:feed:latest:viewer={n}:limit={n}:before={t}"
cached = await get_json_cache(cache_key)  # 5秒 TTL
if cached: return cached
videos = await repo.list_latest(limit, before)  # 直接查 MySQL
await set_json_cache(cache_key, response, ttl=5)
```

**缺少的关键设计：**

- **Redis ZSET 存储视频时间线** — Go 用 ZSET 维护约 1000 条最近视频 ID，score 是发布时间。Python 完全没有 ZSET 操作。
- **冷热分离策略** — Go 通过对比游标和水位线，热数据从 ZSET 高效取、冷数据直接走 MySQL 且不污染 ZSET。Python 所有请求都走同一个路径。
- **全局锁重建 ZSET** — Go 在 ZSET 为空时用 singleflight 防惊群，一个请求重建，其他请求等待复用结果。
- **热冷边界拼接** — Go 在热数据不够 limit 时会用 singleflight 查 MySQL 补齐。Python 直接查 MySQL 取一整页。

**面试可讲的知识点：** Redis ZSET 数据结构（跳表）、冷热数据分离策略、游标分页、singleflight 防惊群效应。

---

### 差距 2：视频详情缓存 — 从"三级缓存+分布式锁"简化成了"Cache-Aside 无锁"

**Go 版本（`internal/video/video_service.go:GetDetail`）：**

```
GetDetail(videoID):
  L1: go-cache (本地内存, 3s TTL)
  L2: Redis video:entity:{id} (1h TTL)
  L3: MySQL (singleflight 合并并发请求)

  L2 miss 时:
    ├─ SETNX 抢分布式锁 (2s TTL)
    ├─ 抢到锁 → 再查一次 Redis (double-check) → 查 MySQL → 写 Redis → 释放锁 (Lua safe unlock)
    └─ 没抢到 → 等 5×20ms spin-wait → 读缓存 → 超时直接查 DB
```

此外 Go 的 `GetVideoByIDs`（`internal/feed/service.go`）实现了完整的三级缓存：

```
GetVideoByIDs(ids[]):
  L1: go-cache 本地内存 (3s TTL)
  L2: Redis MGet 批量查询 (50ms 超时, 失败则全部降级 L3)
  L3: MySQL + singleflight 合并 (异步回写 L2 + 回写 L1)
```

**Python 版本（`app/services/video_service.py:get_detail`）：**

```python
cached = await get_json_cache(key)  # 查 Redis
if cached: return cached
video = await repo.get_by_id(id)    # 查 DB
await set_json_cache(key, data, ttl=300)  # 回填
```

**缺少的关键设计：**

- **L1 本地内存缓存** — Go 用 go-cache 在进程内存里缓存 3 秒，省掉同进程内重复请求的 Redis 网络往返。
- **分布式锁防击穿** — 如果一个热门视频的缓存过期，1000 个并发请求同时来查，Go 用 SETNX 保证只有 1 个请求查 MySQL，其余 999 个等待后读缓存。Python 版本会导致 1000 个请求全部打到 MySQL（**缓存击穿**）。
- **singleflight** — Go 不仅在分布式锁层面做合并，同一进程内的并发请求也通过 singleflight 合并成一次 DB 查询。
- **Double-check** — Go 抢到锁后会再查一次 Redis（因为之前抢锁失败的请求可能已经回填了缓存）。
- **批量查询优化** — Go 的 `GetVideoByIDs` 支持一次查多个视频，Feed 组装时使用 MGet 批量查 Redis。

**面试可讲的知识点：** 缓存穿透/击穿/雪崩的概念和解决方案、SETNX 分布式锁、singleflight 请求合并、Lua 脚本安全解锁。

---

### 差距 3：关注流 — Go 有缓存+分布式锁，Python 直接查 DB

**Go 版本（`internal/feed/service.go:ListByFollowing`）：**

- Redis 缓存整个关注流响应，TTL 24 小时
- 缓存 miss 时 SETNX 抢锁 → 查 DB → 写缓存 → 解锁
- 抢不到锁的请求 spin-wait 5×20ms 重试读缓存 → 超时则直接查 DB

**Python 版本（`app/services/feed_service.py:list_by_following`）：**

- 没有任何缓存，每次请求都直接查 MySQL

**面试可讲的知识点：** 关注流是"变化不频繁但计算成本高"的查询，非常适合长 TTL 缓存。可以讨论为什么不同 Feed 类型的缓存策略应该不同。

---

### 差距 4：点赞/评论系统 — Go 是"异步优先+降级兜底"，Python 是纯同步

**Go 版本（`internal/video/like_service.go:Like`）：**

```
Like(videoID, accountID):
  1. 校验：视频存在 + 未重复点赞
  2. 尝试发两条 MQ:
     likeMQ.Like()         → 让 Worker 异步写 MySQL likes 表
     popularityMQ.Update() → 让 Worker 异步更新 Redis 热榜 ZSET
  3. 两条都成功 → 直接 return（用户感知延迟极低）
  4. 任一条失败 → 降级:
     BEGIN TRANSACTION
       INSERT likes + UPDATE videos.likes_count + UPDATE videos.popularity
     COMMIT
  5. 如果 popularityMQ 失败 → 直接 ZINCRBY Redis 热榜（本地补偿）
```

**Python 版本（`app/services/like_service.py:like`）：**

```python
# 纯同步路径，没有 MQ，没有降级
await like_repo.create(video_id, account_id)
await video_repo.increment_like_counters(video_id)
await delete_cache_key(video_detail_cache_key(video_id))
```

**缺少的关键设计：**

- **异步路径** — Go 的写操作 API 响应时间 = 发 MQ 消息的时间（~1ms），Python 的写操作 = INSERT + UPDATE + DELETE cache（~10-20ms）。
- **降级兜底** — Go 的关键设计哲学：MQ 是加速路径，MySQL 直写是保底路径。MQ 挂了不影响数据正确性。
- **热度写入 Redis ZSET** — Go 的点赞/评论会 `ZINCRBY hot:video:1m:{minute_key}` 更新分钟桶，为热榜提供数据源。Python 只改了 MySQL 的 popularity 字段。
- **MySQL 1062 错误处理** — Go 用 `isDupKey()` 优雅处理并发重复插入，Python 用 `IntegrityError` 捕获但缺少对具体错误码的判断。

**面试可讲的知识点：** 异步优先+降级兜底是 backend 核心设计模式。MQ 作为加速路径、DB 作为保底路径的最终一致性思想。

---

### 差距 5：视频发布 — Go 有事务发件箱，Python 只写 DB

**Go 版本（`internal/video/video_service.go:Publish`）：**

```
Publish:
  BEGIN TRANSACTION
    INSERT INTO videos (...)
    INSERT INTO outbox_msgs (video_id, event_type="publish", status="pending")
    -- 提取 #标签，INSERT tags / INSERT video_tags
  COMMIT

  [另一个进程]
  OutboxWorker 每 1 秒轮询 outbox_msgs (status=pending, 批量 100)
    → 发布到 timeline MQ
    → TimelineConsumer 更新 Redis ZSET feed:global_timeline
    → 标记 status=processed
```

**Python 版本（`app/services/video_service.py:publish`）：**

```python
video = await repo.create(...)
tag_names = extract_tags(...)
if tag_names:
    await tag_repo.attach_tags(video.id, tag_names)
await delete_cache_prefix("v1:feed:latest:")
```

**缺少的关键设计：**

- **事务发件箱模式** — Go 通过 `outbox_msgs` 表保证"视频写入"和"时间线更新通知"的最终一致性。即使 MQ 挂了，outbox 消息还在 DB 里，Worker 恢复后会重新投递。
- **Redis 时间线更新** — Go 的发布会通过 outbox → MQ → consumer 链路最终写入 `feed:global_timeline` ZSET。Python 只是删除了 Feed 短缓存（新视频要等缓存过期后才能被看到）。

**面试可讲的知识点：** 事务发件箱（Transactional Outbox）是分布式系统中保证"数据库和消息队列一致性"的经典模式。可以讨论为什么不用"先写 DB 再发 MQ"而是引入 outbox 表。

---

### 差距 6：鉴权系统 — Go 有更完整的账号管理和 Token 轮转

**Go 有而 Python 没有的账号管理功能：**

| 功能 | Go 实现 | Python 状态 |
|------|---------|------------|
| 改名 (Rename) | 事务更新 username + 重新签发 JWT + 缓存新 token | 未实现 |
| 改密码 (ChangePassword) | 验证旧密码 → 哈希新密码 → 强制登出所有设备 | 未实现 |
| 上传头像 (UploadAvatar) | 文件类型校验、大小限制 (10MB)、按 ID 组织目录 | 未实现 |
| 更新资料 (UpdateProfile) | 灵活的部分字段更新 | 未实现 |

**Go 的 Refresh Token 设计更完整：**

- Go 在 Redis 中缓存了 `account:{id}:refresh` 和 `refresh:{token}→id` 反向映射，Refresh 时可以 O(1) 查到，不需要遍历 DB。
- Python 的 Refresh 只走 DB（`find_by_refresh_token`），没有 Redis 优化；Go 的 fallback 是 `FindAll` 全表遍历（也很粗暴但至少有两层）。

**Go 的 Login 缓存更完整：**

- Go 一次 Login 写 3 个 Redis key：账户 token、账户 refresh token、refresh token 反向映射。
- Python 只缓存了 access token。

---

### 差距 7：Redis 基础设施

| 能力 | Go | Python |
|------|-----|--------|
| **分布式锁** | SETNX + 随机 token + Lua safe unlock | 无 |
| **自增+设过期（原子）** | Lua: INCR + if count==1 → PEXPIRE | 无 |
| **ZSET 操作** | ZAdd, ZIncrBy, ZUnionStore, ZRevRange, ZRevRangeByScore, ZRangeWithScores | 无 |
| **MGet 批量读** | 有（三级缓存中批量查 Redis） | 无 |
| **Key 前缀系统** | `c.Key(format, args...)` 统一管理 | 手动拼接字符串 |
| **IsMiss 判断** | 区分"key 不存在"和"Redis 错误" | 无（都按 miss 处理） |
| **TTL 配置化** | 每个场景独立 TTL | 硬编码 |

**面试可讲的知识点：** 分布式锁为什么需要随机 token + Lua 脚本安全释放（防止 A 的锁被 B 误删）。INCR 为什么需要 Lua 脚本设置首次过期（原子性保证）。为什么 key 需要统一前缀（多服务共用 Redis、方便批量管理）。

---

### 差距 8：文件上传

Go 有完整的三类文件上传：

- 视频上传（`.mp4`, 200MB 限制, 按 `author/date/uuid` 组织目录, 返回绝对 URL）
- 封面上传（`.jpg/.jpeg/.png/.webp`, 10MB）
- 头像上传（同上, 按 ID 组织目录）

Python 完全没有文件上传——视频发布时用的是 `debug://` 占位 URL。

**面试可讲的知识点：** 文件类型校验（扩展名 + magic bytes）、大小限制、路径遍历攻击防护、静态资源服务、绝对 URL 构造（包含 scheme 检测和 X-Forwarded-Proto 处理）。

---

### 差距 9：@mention 通知和评论删除

**Go 的 `comment_service.notifyMentions()`：**

- 用正则 `@(\w+)` 提取评论中的被提及用户
- 排除自己 @ 自己的情况
- 对每个被提及的用户创建 notifications 记录

**Python 的评论模块完全没有 @mention 检测功能。**

**Go 的评论删除走 MQ 异步路径：**

- 尝试 `commentMQ.Delete()` → 成功直接返回
- MQ 失败 → 降级为直接 DB 删除

**Python 只有纯同步 DB 删除。**

---

### 差距 10：popularity_cache 独立模块

Go 有独立的 `UpdatePopularityCache()` 函数（`internal/video/popularity_cache.go`）：

- 失效视频详情 Redis 缓存
- ZINCRBY 当前分钟的 `hot:video:1m:{YYYYMMDDHHMM}` ZSET
- 设置该分钟桶的 TTL 为 2 小时

Python 的点赞/评论只是做了 `video_repo.increment_popularity()`（更新 MySQL 字段）和 `delete_cache_key()`（失效详情缓存），没有将热度变化写入 Redis 分钟桶。

---

## 三、总结：按面试重要程度排序的差距清单

| 优先级 | 差距 | 面试可讲的知识点 |
|--------|------|-----------------|
| **P0** | Feed 冷热分离 + ZSET 时间线 | Redis ZSET（跳表）、冷热数据分离策略、游标分页、singleflight 防惊群 |
| **P0** | 视频三级缓存 + 分布式锁防击穿 | 缓存穿透/击穿/雪崩、SETNX 分布式锁、singleflight 请求合并、Lua 安全解锁 |
| **P1** | 点赞/评论写入热榜分钟桶 ZSET | ZINCRBY、滑动窗口、按分钟分桶的写入分散优化 |
| **P1** | 视频发布的事务发件箱 | DB-MQ 最终一致性、Transactional Outbox 模式 |
| **P2** | 关注流缓存 + 分布式锁 | 缓存策略选择（长 TTL vs 短 TTL）、分布式锁 spin-wait |
| **P2** | @mention 通知 | 正则提取、通知创建 |
| **P3** | 账号管理（改名/改密/头像） | 改名后 token 轮转、改密后强制所有设备下线 |
| **P3** | Refresh Token Redis 反向索引 | `refresh:{token}→id` 映射设计 |
| **P4** | 文件上传 | 文件类型校验、大小限制、路径组织、安全防护 |

---

## 四、推荐学习路线（对应 Roadmap 后续阶段）

```
当前状态: Stages 1-4 完成（基础 CRUD + 简单缓存）
         ↓
Step 1: 补充 P0 差距（Feed 冷热分离 + 三级缓存 + 分布式锁）
         → 对应 Stage 5（缓存体系）+ Stage 6 部分（ZSET 时间线）
         ↓
Step 2: 补充 P1 差距（热度分钟桶 + 事务发件箱）
         → 对应 Stage 6（热榜）+ Stage 7（MQ 异步+降级兜底）
         ↓
Step 3: 补充 P2-P4 差距 + Stage 8-10
         → 对应完整的 Roadmap 后续阶段
```

**关键纪律：** 每阶段只引入一个新概念。比如不要在加冷热分离的同时引入 MQ。概念叠加会让你不知道哪个部分出了 bug。
