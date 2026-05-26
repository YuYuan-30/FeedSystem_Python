# feedSystem Video Python 后端

当前后端范围：

- FastAPI 应用启动。
- 通过 SQLAlchemy async 连接 MySQL。
- 创建 `accounts` 表。
- 实现账号注册、登录、查询接口。
- 实现 JWT access token、refresh token、登出主动失效。
- 通过 Redis 缓存当前有效 access token，Redis 不可用时回源 MySQL。
- 创建 `videos` 表。
- 实现视频发布、作者视频列表、视频详情接口。
- 创建 `likes` 和 `comments` 表。
- 实现点赞、取消点赞、是否点赞接口。
- 实现评论发布、删除、列表接口。
- 实现最新 Feed 和点赞榜 Feed。
- 创建 `socials`、`tags` 和 `video_tags` 表。
- 实现关注、取关、粉丝列表、关注列表。
- 实现关注流和标签流。
- 通过 Redis 缓存视频详情和最新 Feed 短缓存。
- 通过 Redis 固定窗口限流保护注册、登录、点赞、评论和关注写接口。
- 视频详情缓存已升级为带 Redis 锁的防击穿链路。
- 预留 `EventPublisher` 事件发布接口，后续可接 RabbitMQ。

如果你还没有 MySQL 和 Redis 容器，可以在项目根目录用 compose 启动依赖：

```bash
docker compose up -d mysql redis
```

如果你已经像现在这样手动启动了容器：

```text
YYmysql  -> localhost:3306
YYredis  -> localhost:6379
```

就不需要再执行 `docker compose up -d mysql redis`。`docker-compose.yml` 只是备用的依赖启动配置，作用等价于把 `docker run` 命令保存下来，方便以后复现环境。

如果是手动创建的 MySQL 容器，还需要先创建项目数据库：

```bash
docker exec -it YYmysql mysql -uroot -p123456 -e "CREATE DATABASE IF NOT EXISTS feedsystem CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
```

这个命令只需要执行一次。后端启动时会在 `feedsystem` 数据库中自动创建 `accounts`、`videos`、`likes`、`comments`、`socials`、`tags` 和 `video_tags` 表。

在 `backend/` 目录创建虚拟环境并安装依赖：

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

如果你已经安装过 Day 1 依赖，Day 2 新增了 `PyJWT` 和 `redis`，仍然需要在虚拟环境中重新执行一次：

```bash
pip install -r requirements.txt
```

在 `backend/` 目录启动后端：

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

打开接口文档：

```text
http://127.0.0.1:8000/docs
```

Day 2 推荐用 Swagger 按下面顺序验证：

1. `POST /account/register` 注册账号。
2. `POST /account/login` 登录，复制返回的 `token` 和 `refresh_token`。
3. 点击 Swagger 右上角 `Authorize`，填写 `Bearer token值`。
4. `POST /account/me` 验证硬鉴权能拿到当前用户。
5. `POST /video/publish` 发布视频。
6. `POST /video/listByAuthorID` 按作者 ID 查询视频列表。
7. `POST /video/getDetail` 不带 token 也能看详情。
8. `POST /account/refresh` 用 `refresh_token` 换新 `token`。
9. `POST /account/logout` 登出，再用旧 token 调硬鉴权接口应返回 401。

Day 3 推荐继续验证：

1. 用户 A 登录并发布视频。
2. 用户 B 登录，对 A 的视频调用 `POST /like/like`。
3. 用户 B 再次点赞同一视频，应返回 409。
4. 用户 B 调用 `POST /like/isLiked`，应返回 `true`。
5. 用户 B 调用 `POST /comment/publish` 发布评论。
6. 调用 `POST /comment/listAll` 查看评论列表。
7. 调用 `POST /feed/listLatest` 查看最新 Feed。
8. 调用 `POST /feed/listLikesCount` 查看点赞榜 Feed。
9. 用户 B 调用 `POST /like/unlike`，视频点赞数应减少且不会小于 0。

Day 4 推荐继续验证：

1. 用户 A 发布标题或描述带 `#backend` 的视频。
2. 用户 B 调用 `POST /social/follow` 关注用户 A。
3. 用户 B 调用 `POST /social/getAllVloggers`，应能看到 A。
4. 用户 A 调用 `POST /social/getAllFollowers`，应能看到 B。
5. 用户 B 调用 `POST /feed/listByFollowing`，应能看到 A 的视频。
6. 游客或用户 B 调用 `POST /feed/listByTag`，`tag_name` 填 `backend`，应能看到带标签的视频。
7. 连续两次调用 `POST /video/getDetail`，第二次会优先命中 Redis 详情缓存。
8. 调用 `POST /feed/listLatest` 后，Redis 中会短暂出现 `v1:feed:latest:*` 缓存 key，默认 TTL 为 5 秒。

Day 5 推荐继续验证：

1. 高频调用 `POST /account/login`，超过 1 分钟 20 次会返回 429。
2. 登录后高频调用点赞、评论或关注写接口，超过限制会返回 429。
3. 在 Redis 中可以看到类似 `v1:ratelimit:account_login:127.0.0.1` 的限流 key。
4. 暂停 Redis 后，核心业务仍会继续走 MySQL；当前限流策略会放行请求。
5. 阅读 `app/core/events.py`，确认当前 RabbitMQ 只预留扩展点，不做真实接入。

前端当前已接入 Day1-4 的主要联调入口：账号、视频、点赞、评论、推荐 Feed、点赞榜、关注流、标签流和右侧接口日志。Day5 的 429 响应会进入右侧接口日志，便于观察限流结果。

Day 6 推荐继续验证：

1. 调用 `POST /video/getDetail` 查询一个存在的视频，第一次会在 Redis 写入 `v1:video:detail:{id}`。
2. 再次调用同一个视频详情，应优先从 Redis 读取缓存。
3. 删除 Redis 中的视频详情 key 后再次请求，会触发缓存保护链路：先尝试写入 `v1:lock:v1:video:detail:{id}`，再回源 MySQL 并回填缓存。
4. 正常请求结束后，锁 key 会被 Lua 脚本释放，不应该长期存在。
5. 如果 Redis 不可用，视频详情仍会回源 MySQL；只是失去缓存加速和防击穿保护。
