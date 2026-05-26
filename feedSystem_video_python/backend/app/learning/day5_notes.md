# Day 5 学习笔记：限流、MQ 扩展点与工程化收口

## 1. 今天解决了什么问题

Day 5 的目标不是继续堆业务接口，而是给已有系统补上工程化保护和面试表达：

- 用 Redis 做固定窗口限流。
- 给注册、登录、点赞、评论、关注这些写接口加保护。
- 预留 `EventPublisher`，以后可以接 RabbitMQ。
- 明确当前 Docker 使用方式：你已经有 `YYmysql` 和 `YYredis`，不需要强行切到 compose。
- 把项目整理成可以演示、可以讲述的 MVP。

## 2. 为什么需要限流

限流不是为了正常用户，而是为了保护系统免受异常请求冲击。

典型场景：

- 登录接口被暴力尝试密码。
- 注册接口被刷垃圾账号。
- 点赞、评论、关注接口被脚本高频调用。
- 某个前端 bug 导致短时间重复请求。

所以我们给写接口加了简单固定窗口限流：

```text
注册：按 IP 限流
登录：按 IP 限流
点赞/取消点赞：按账号限流
评论发布/删除：按账号限流
关注/取关：按账号限流
```

## 3. Redis 固定窗口限流的核心思想

固定窗口限流可以理解为：

```text
某个对象，在某段时间内，最多允许请求 N 次。
```

例如：

```text
v1:ratelimit:account_login:127.0.0.1
```

表示本机这个 IP 在登录接口上的访问计数。

函数链路：

1. `rate_limit_by_ip` 或 `rate_limit_by_account`
   - 生成 FastAPI 依赖。
2. 依赖函数拿到 subject
   - 未登录接口用 IP。
   - 已登录写接口用账号 ID。
3. 调用 `allow_request`
   - 生成 Redis key。
   - 执行 `INCR key`。
   - 如果是第一次请求，执行 `EXPIRE key window_seconds`。
   - 如果计数超过限制，返回 `False`。
4. 路由依赖发现 `False`
   - 返回 HTTP 429。

## 4. 为什么 Redis 限流失败时选择放行

这里有一个重要取舍：

```text
限流是保护层，不是业务真相。
```

如果 Redis 挂了，有两种选择：

1. 拒绝所有请求。
2. 放行请求，让主业务继续走 MySQL。

我们当前 MVP 选择放行，因为：

- Redis 是可选性能层，不应成为核心业务的单点故障。
- 对学习项目来说，可用性比“限流绝对准确”更重要。
- 如果 Redis 短暂异常，直接拒绝登录、评论、点赞会让用户体验很差。

面试里可以补充：

> 生产系统要结合业务风险选择 fail-open 还是 fail-closed。普通内容类接口可以 fail-open；支付、风控、短信验证码这类高风险接口可能要 fail-closed 或走本地降级策略。

## 5. 限流接口接入位置

注册和登录还没有用户身份，所以按 IP 限流：

```python
dependencies=[Depends(rate_limit_by_ip("account_login", limit=20, window_seconds=60))]
```

点赞、评论、关注需要登录，所以按账号限流：

```python
dependencies=[Depends(rate_limit_by_account("like_write", limit=60, window_seconds=60))]
```

这说明限流不一定只按 IP：

- 未登录接口：IP 是最容易拿到的 subject。
- 登录后接口：账号 ID 更准确。
- 真实网关层：还可能按用户、设备、接口、租户、IP 段组合限流。

## 5.5 限流请求的数据流

注册和登录限流：

输入来源：

- 前端或 Swagger 调用 `POST /account/register` 或 `POST /account/login`。
- 请求还没有通过账号鉴权，所以 subject 使用请求 IP。

函数链路：

1. FastAPI 进入路由前，先执行路由上的 `Depends(rate_limit_by_ip(...))`。
2. `rate_limit_by_ip` 内部依赖函数调用 `get_client_ip(request)`。
3. 调用 `allow_request(scope, subject, limit, window_seconds)`。
4. `allow_request` 生成 Redis key：

```text
v1:ratelimit:{scope}:{subject}
```

5. Redis 执行 `INCR key`。
6. 如果计数是 1，说明这是当前窗口第一次请求，设置 `EXPIRE key window_seconds`。
7. 如果计数超过 limit，依赖函数抛出 HTTP 429。
8. 如果未超过 limit，FastAPI 才继续执行真正的注册或登录路由函数。

输出去向：

- 未超过限制：请求继续进入业务 Service。
- 超过限制：直接返回 HTTP 429，业务 Service 不会执行。
- Redis 中短暂存在限流 key，到期后自动删除。

点赞、评论、关注限流：

输入来源：

- 前端调用点赞、评论、关注这类需要登录的写接口。
- subject 使用当前账号 ID。

函数链路：

1. 路由依赖中调用 `rate_limit_by_account(...)`。
2. `rate_limit_by_account` 先通过 `get_current_user` 拿到当前账号。
3. 再用 `current_user.id` 调用 `allow_request`。
4. 未超过限制才进入对应的 Service，例如 `LikeService.like`、`CommentService.publish`、`SocialService.follow`。

框架知识点：

- 当前限流不是 FastAPI Middleware，而是 FastAPI `Depends` 依赖。
- 这样做的好处是：不同接口可以有不同 `scope`、不同 limit、不同 subject。
- 全局中间件更适合做“所有请求都按 IP 粗限流”；业务限流更适合放在路由依赖里。

## 6. MQ 扩展点为什么现在只返回 False

我们新增了：

```text
app/core/events.py
```

里面有：

```python
class EventPublisher:
    async def publish_like(...):
        return False
```

`False` 的意思是：

```text
当前没有真实 MQ 可用，业务继续走同步 MySQL。
```

这样 Service 层就可以写成：

```text
先尝试发布事件
如果发布成功，未来可以快速返回
如果发布失败或当前没有 MQ，就走同步 MySQL 事务
```

当前 MVP 里它不会改变现有行为，但它表达了一个架构扩展点：以后接 RabbitMQ 时，不需要把所有业务逻辑推倒重写。

当前 EventPublisher 的数据流：

点赞：

1. `POST /like/like`
2. `LikeService.like`
3. 校验视频存在、校验是否重复点赞。
4. 调用 `EventPublisher.publish_like(current_user.id, video_id)`。
5. 当前返回 `False`。
6. 继续同步写 MySQL：插入 `likes`，更新 `videos.likes_count` 和 `videos.popularity`。
7. 删除视频详情缓存。

取消点赞：

1. `POST /like/unlike`
2. `LikeService.unlike`
3. 调用 `EventPublisher.publish_unlike(...)`。
4. 当前返回 `False`。
5. 继续同步删除 `likes`，减少 `likes_count` 和 `popularity`。
6. 删除视频详情缓存。

评论：

1. `POST /comment/publish`
2. `CommentService.publish`
3. 调用 `EventPublisher.publish_comment(...)`。
4. 当前只是预留扩展点，后续仍同步写 `comments` 表，更新 `videos.popularity`，删除视频详情缓存。

关注：

1. `POST /social/follow`
2. `SocialService.follow`
3. 校验不能关注自己、目标用户存在、不能重复关注。
4. 调用 `EventPublisher.publish_follow(...)`。
5. 当前返回 `False`。
6. 继续同步写 MySQL 的 `socials` 表。

这个设计的重点是：当前同步路径是真正的数据落地点，MQ 只是未来的加速路径。

## 7. 如果以后真的接 RabbitMQ，点赞链路怎么改

当前点赞链路：

```text
API -> LikeService -> 写 likes 表 -> 更新 videos.likes_count -> commit
```

以后可以变成：

```text
API -> LikeService -> EventPublisher.publish_like -> RabbitMQ
Worker -> 消费 like 事件 -> 写 likes 表 -> 更新 videos.likes_count
```

但这会带来新问题：

- API 返回时数据库可能还没更新，属于最终一致性。
- Worker 要处理重复消息，所以数据库唯一约束仍然重要。
- MQ 不可用时要有降级路径，也就是当前同步 MySQL 路径。

所以当前设计里保留同步路径不是偷懒，而是一个可靠兜底。

## 8. Docker Compose 在本项目里的定位

你现在已经有：

```text
YYmysql -> localhost:3306
YYredis -> localhost:6379
```

所以当前学习不需要强行使用 `docker compose up`。

你的一键启动方式应该是：

```bash
docker start YYmysql YYredis
```

停止：

```bash
docker stop YYmysql YYredis
```

`docker-compose.yml` 的价值是：

- 把 MySQL / Redis 的启动配置写成文件。
- 换电脑或重新搭环境时更容易复现。
- 但它不会直接管理你已经手动创建的 `YYmysql` 和 `YYredis` 容器。

## 9. Day5 最小演示链路

最终可以这样演示：

```text
1. docker start YYmysql YYredis
2. 启动后端 uvicorn
3. 启动前端 npm run dev
4. 注册用户 A
5. 登录用户 A
6. A 发布带 #后端 的视频
7. 注册并登录用户 B
8. B 关注 A
9. B 点赞 A 的视频
10. B 评论 A 的视频
11. 查看最新 Feed / 点赞榜 / 关注流 / 标签流
12. 观察 Redis 中的 token、详情缓存、Feed 短缓存、限流 key
```

## 10. 面试表达

可以这样讲 Day5：

> Day 5 我主要做工程化收口。首先用 Redis 的 `INCR + EXPIRE` 实现固定窗口限流，注册和登录按 IP 限流，点赞、评论、关注按账号限流。限流 Redis 异常时当前选择 fail-open，也就是放行请求，因为在这个项目里 Redis 是保护层和性能层，不是业务真相。然后我加了 `EventPublisher` 事件发布接口，当前没有接 RabbitMQ，所以默认返回 False，业务仍然走同步 MySQL 事务；以后如果要接 MQ，只需要替换 Publisher，并保留当前同步路径作为降级兜底。

可能被追问：为什么限流不用 MySQL？

> 因为限流是高频、短生命周期的计数，Redis 的内存计数和 TTL 更适合。MySQL 更适合保存长期业务事实，不适合为每次请求做频繁计数更新。

可能被追问：固定窗口有什么缺点？

> 固定窗口实现简单，但窗口边界可能有突刺。例如 12:00:59 请求 20 次，12:01:00 又请求 20 次，短时间内实际放过了 40 次。更精细可以用滑动窗口、令牌桶或漏桶。当前 MVP 选择固定窗口，是为了先掌握限流基本思想。

可能被追问：为什么现在不接 RabbitMQ？

> 当前目标是 5 天内完成能跑、能讲、能演示的 MVP。点赞、评论、关注这类写链路先用 MySQL 事务保证一致性。RabbitMQ 会带来最终一致性、重复消费、失败重试、死信队列、Worker 运维等新复杂度，所以当前只预留接口，不提前引入复杂系统。
