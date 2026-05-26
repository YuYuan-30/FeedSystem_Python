# Day 6 学习笔记：Redis 锁与缓存防击穿

## 1. 今天解决了什么问题

Day 4 的视频详情缓存已经用了 Cache-Aside：

```text
读 Redis -> miss -> 查 MySQL -> 写 Redis -> 返回
```

这个链路在普通访问下没有问题，但如果某个热门视频的缓存刚好过期，很多请求同时进来，就会出现：

```text
100 个请求同时读 Redis miss
100 个请求同时查 MySQL
100 个请求同时回填 Redis
```

这就是缓存击穿：一个热点 key 失效瞬间，大量请求一起打到数据库。

Day 6 要解决的就是这个问题：缓存 miss 时，不让所有请求都回源 MySQL，而是用 Redis 分布式锁控制“只有一个请求负责构建缓存”。

## 2. 当前涉及的文件

新增文件：

- `app/core/redis_lock.py`
  - 负责 Redis 分布式锁。
  - 核心函数：`redis_lock_key`、`try_acquire_lock`、`release_lock`。
- `app/core/cache_protector.py`
  - 负责缓存保护流程。
  - 核心函数：`get_json_with_cache_protection`。

改造文件：

- `app/services/video_service.py`
  - `VideoService.get_detail` 不再自己手写 Redis miss 后查库。
  - 改成调用 `get_json_with_cache_protection`。

复用文件：

- `app/core/redis.py`
  - `get_json_cache`
  - `set_json_cache`
  - `video_detail_cache_key`
- `app/repositories/video_repo.py`
  - `VideoRepository.get_by_id`
- `app/schemas/video.py`
  - `VideoPublic`

## 3. 视频详情现在的数据流

输入来源：

- 前端或 Swagger 调用 `POST /video/getDetail`。
- 请求体里传入 `video_id`。

函数链路：

1. `app/api/video.py::get_detail`
   - 接收请求体。
   - 调用 `VideoService.get_detail(video_id)`。

2. `app/services/video_service.py::VideoService.get_detail`
   - 调用 `video_detail_cache_key(video_id)` 生成缓存 key。
   - 定义内部函数 `build_detail`，表示缓存未命中时如何回源 MySQL。
   - 调用 `get_json_with_cache_protection(...)`。

3. `app/core/cache_protector.py::get_json_with_cache_protection`
   - 第一次读 Redis：`get_json_cache(cache_key)`。
   - 命中：直接返回缓存字典。
   - 未命中：进入抢锁流程。

4. `app/core/redis_lock.py::redis_lock_key`
   - 把业务缓存 key 转成锁 key。
   - 例如：

```text
缓存 key: v1:video:detail:6
锁 key:   v1:lock:v1:video:detail:6
```

5. `app/core/redis_lock.py::try_acquire_lock`
   - 生成随机 token。
   - 执行 Redis：

```text
SET lock_key token NX EX 3
```

含义：

- `NX`：只有 key 不存在时才设置成功。
- `EX 3`：锁最多 3 秒自动过期，避免请求崩溃后锁永远不释放。
- `token`：用来证明“这把锁是我抢到的”。

6. 如果抢到锁
   - 再读一次 Redis。
   - 这一步叫 double-check。
   - 如果第二次已经命中，说明别的请求可能刚刚回填了缓存，直接返回。
   - 如果仍然 miss，调用 `build_detail`。

7. `build_detail`
   - 调用 `VideoRepository.get_by_id(video_id)` 查 MySQL。
   - 查不到：抛出 `VideoNotFoundError`。
   - 查到：用 `VideoPublic.model_validate(video)` 转成响应模型。
   - 再用 `model_dump(mode="json")` 转成可以 JSON 缓存的字典。

8. `set_json_cache`
   - 把字典写入 Redis。
   - TTL 仍然是 300 秒。

9. `release_lock`
   - 用 Lua 脚本释放锁。
   - 先判断 Redis 中保存的 token 是否等于自己的 token。
   - 一致才删除锁。

10. `VideoService.get_detail`
   - 把缓存保护工具返回的字典重新转成 `VideoPublic`。
   - API 层返回 JSON 给前端或 Swagger。

输出去向：

- Redis 命中或 MySQL 回源成功后，最终返回视频详情 JSON。
- Redis 写入 `v1:video:detail:{video_id}`。
- Redis 临时写入 `v1:lock:v1:video:detail:{video_id}`，释放后删除。

## 4. 为什么需要 double-check

抢到锁以后不能立刻查 MySQL，而是要再读一次 Redis。

原因是这个时间线可能发生：

```text
请求 A 读 Redis miss
请求 B 读 Redis miss
请求 A 抢到锁，查 MySQL，写 Redis，释放锁
请求 B 此时才抢到锁
```

如果 B 抢到锁后不 double-check，就会再查一次 MySQL，浪费数据库资源。

所以正确流程是：

```text
抢到锁 -> 再读 Redis -> 仍然 miss 才查 MySQL
```

## 5. 为什么释放锁要用 Lua 校验 token

不能简单写：

```text
DEL lock_key
```

因为可能发生这种情况：

```text
请求 A 抢到锁，锁 TTL 3 秒
请求 A 因为网络或数据库慢，处理超过 3 秒
锁自动过期
请求 B 抢到新的锁
请求 A 终于处理完，执行 DEL lock_key
```

如果 A 直接 `DEL`，就会把 B 的锁删掉。

所以我们写入锁时放一个随机 token：

```text
SET lock_key token_a NX EX 3
```

释放时 Lua 脚本做原子判断：

```text
if redis.get(lock_key) == token_a:
    redis.del(lock_key)
```

只有锁还是自己的，才允许删除。

Lua 的意义是：判断和删除在 Redis 里一次完成，不会被其他请求插队。

## 6. 没抢到锁的请求怎么办

没抢到锁说明已经有别的请求在构建缓存。

当前策略：

```text
等待 0.05 秒 -> 读缓存
最多重试 5 次
```

如果等到了缓存，就直接返回。

如果仍然等不到，就降级查 MySQL。这样做是为了避免请求一直卡住。这个降级路径可能仍然查 DB，但只有在锁持有者太慢、Redis 异常或缓存构建失败时发生。

## 7. Redis 挂了怎么办

Redis 在本项目里仍然是性能层，不是数据真相。

如果 Redis 出错：

- `get_json_cache` 返回 None。
- `try_acquire_lock` 返回 None。
- 请求会短暂等待后调用 `builder`。
- `builder` 最终查 MySQL。

所以 Redis 故障不会导致视频详情不可用，只会失去缓存保护和缓存加速能力。

## 8. 这和 FastAPI 框架有什么关系

这次的缓存防击穿不是 FastAPI 中间件，而是 Service 层内部的业务读优化。

原因：

- 中间件适合处理所有请求都要经过的通用逻辑，比如 request id、全局限流、日志。
- 视频详情缓存只属于视频详情这个业务，不应该让所有请求都经过同一套缓存逻辑。
- `VideoService.get_detail` 最清楚“缓存 miss 时该怎么查 MySQL、查不到该抛什么业务错误”。

所以缓存保护工具放在 `core`，业务回源函数由 Service 提供。

## 9. 和 Day 4 Cache-Aside 的关系

Day 4 学的是基础 Cache-Aside：

```text
读缓存 -> miss -> 查 DB -> 写缓存
```

Day 6 是在 miss 和查 DB 中间加保护：

```text
读缓存 -> miss -> 抢锁 -> double-check -> 查 DB -> 写缓存 -> 释放锁
```

它们不是两套方案，而是同一个缓存模式的升级版。

## 10. 面试表达

可以这样讲：

> 我一开始的视频详情缓存是标准 Cache-Aside：先读 Redis，miss 后查 MySQL，再回填 Redis。后来我补了防击穿逻辑，因为热门视频缓存过期时，很多并发请求会同时 miss 并打到 MySQL。现在缓存 miss 后会先尝试用 Redis `SET NX EX` 抢锁，抢到锁的请求 double-check 缓存后负责查库和回填，没抢到锁的请求短暂等待后再读缓存。释放锁时用随机 token + Lua 脚本，避免误删其他请求的新锁。Redis 异常时仍然回源 MySQL，保证缓存层失败不影响业务正确性。

可能追问：为什么不用普通 Python 锁？

可以回答：

> Python 进程内锁只能保护当前进程。如果后端部署了多个 uvicorn worker 或多台机器，每个进程都有自己的内存，普通锁无法互相感知。Redis 锁是跨进程、跨机器共享的，适合保护这种分布式场景里的热点缓存回源。

可能追问：锁 TTL 应该怎么设置？

可以回答：

> 锁 TTL 要比正常回源耗时略长，防止请求崩溃时锁长期存在。当前视频详情查库很轻，所以先设 3 秒。如果回源逻辑变重，比如组装多个表或调外部服务，就要结合实际耗时调整 TTL，或者引入续期机制。
