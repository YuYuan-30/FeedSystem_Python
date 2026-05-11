# Day 2 学习笔记：JWT、Redis Token 缓存与视频发布

## 1. 今天解决了什么问题

Day 1 的登录只返回一个临时随机 token，能跑通登录链路，但还不能很好地解释真实后端里的登录态。

Day 2 做了三件事：

1. 把登录态升级为 `access token + refresh token`。
2. 用 `Depends` 实现硬鉴权和软鉴权。
3. 建立 `videos` 表，并实现发布视频、作者视频列表、视频详情。

## 2. Access Token 与 Refresh Token

`access token` 用来访问接口，过期时间短。它是 JWT，里面带有 `account_id`、`username`、签发时间和过期时间。

`refresh token` 用来换新的 `access token`，过期时间更长。我们这里把它设计成不透明随机字符串，只存在服务端数据库里，不让前端自己解析。

这样拆分的原因是：

- access token 短，可以降低泄露后的风险。
- refresh token 长，可以减少用户频繁重新登录。
- 服务端保存当前 token，可以支持登出后主动失效。

## 3. 登录链路的数据流

输入来源：

- Swagger 或前端调用 `POST /account/login`。
- 请求体是 `LoginRequest`，包含 `username` 和 `password`。

函数链路：

1. `api/account.py::login`
   - 接收 HTTP 请求。
   - 创建 `AccountService`。
2. `AccountService.login`
   - 调用 `repo.find_by_username` 查用户。
   - 调用 `verify_password` 校验 bcrypt 密码哈希。
   - 调用 `create_access_token` 生成 JWT。
   - 调用 `create_refresh_token` 生成随机 refresh token。
   - 调用 `repo.save_tokens` 写入 MySQL。
   - 调用 `cache_access_token` 写入 Redis。
3. `AccountRepository.save_tokens`
   - 更新 `accounts.token` 和 `accounts.refresh_token`。
4. `api/account.py::login`
   - `db.commit()` 提交事务。
   - 返回 `LoginResponse`。

输出去向：

- 前端拿到 `token` 和 `refresh_token`。
- 后续访问需要登录的接口时，前端把 `token` 放到请求头：

```text
Authorization: Bearer <token>
```

## 4. 为什么 JWT 还要存 MySQL 和 Redis

纯 JWT 的特点是：只要签名正确且没过期，服务端不用查数据库就能相信它。

但这样有一个问题：用户登出后，旧 JWT 在过期前仍然理论有效。

所以我们做了一个折中设计：

- JWT 负责表达“这个 token 看起来是谁签发的、属于谁、什么时候过期”。
- MySQL 保存“这个账号当前真正有效的 token”。
- Redis 缓存“当前有效 token”，减少每次鉴权都查 MySQL。

数据真相是 MySQL，Redis 是性能层。

## 5. 鉴权链路的数据流

输入来源：

- 前端访问需要登录的接口，比如 `POST /video/publish`。
- 请求头带 `Authorization: Bearer <token>`。

函数链路：

1. `get_current_user`
   - FastAPI 通过 `Depends` 自动调用。
   - 如果请求头没有 token，直接返回 401。
2. `_resolve_user_from_token`
   - 调用 `parse_access_token` 校验 JWT 签名和过期时间。
   - 根据 JWT 里的 `account_id` 查 Redis key：`v1:account:{id}`。
3. Redis 命中
   - 如果 Redis token 和请求 token 一致，直接通过。
   - 返回 `CurrentUser(id, username)`。
4. Redis 未命中
   - 调用 `AccountRepository.find_by_id` 回源 MySQL。
   - 比较 `accounts.token` 和请求 token。
   - 一致就调用 `cache_access_token` 回填 Redis。
5. 不一致
   - 说明 token 过期、伪造、或已经登出失效。
   - 返回 401。

输出去向：

- 通过鉴权后，路由函数得到 `CurrentUser`。
- 业务代码可以使用 `current_user.id` 作为作者 ID 或操作者 ID。

## 6. 硬鉴权和软鉴权

硬鉴权用于必须登录的接口，例如：

- `POST /account/logout`
- `POST /account/me`
- `POST /video/publish`

它使用 `get_current_user`。没有 token 或 token 错误都会拒绝。

软鉴权用于“登录和不登录都能访问，但登录后可以得到更多信息”的接口，例如：

- `POST /video/getDetail`
- 后续 Feed 列表、视频详情、是否点赞等接口

它使用 `get_optional_user`。不带 token 可以继续访问；带了错误 token 说明前端登录态异常，就返回 401。

## 7. Refresh Token 链路

输入来源：

- 前端发现 access token 过期，调用 `POST /account/refresh`。
- 请求体带 `refresh_token`。

函数链路：

1. `api/account.py::refresh`
2. `AccountService.refresh_access_token`
3. `AccountRepository.find_by_refresh_token`
4. `create_access_token`
5. `AccountRepository.save_access_token`
6. `cache_access_token`
7. `db.commit()`

输出去向：

- 返回新的 `token`。
- `refresh_token` 继续沿用。
- MySQL 和 Redis 都更新为新的 access token。

## 8. 登出链路

输入来源：

- 前端调用 `POST /account/logout`，请求头带 access token。

函数链路：

1. `get_current_user` 先确认这个请求确实是已登录用户发起的。
2. `AccountService.logout`
3. `AccountRepository.find_by_id`
4. `AccountRepository.clear_tokens`
5. `delete_cached_access_token`
6. `db.commit()`

输出去向：

- MySQL 中 `accounts.token` 和 `accounts.refresh_token` 被清空。
- Redis 中 `v1:account:{id}` 被删除。
- 旧 access token 再访问硬鉴权接口会失败。

## 9. 视频发布链路

输入来源：

- 前端调用 `POST /video/publish`。
- 请求头带 access token。
- 请求体包含 `title`、`description`、`play_url`、`cover_url`。

函数链路：

1. `get_current_user`
   - 先完成硬鉴权，拿到当前登录用户。
2. `api/video.py::publish`
   - 接收视频请求体。
   - 创建 `VideoService`。
3. `VideoService.publish`
   - 使用 `current_user.id` 作为 `author_id`。
   - 使用 `current_user.username` 冗余保存作者名，方便列表展示。
4. `VideoRepository.create`
   - 写入 `videos` 表。
   - `flush + refresh` 拿到数据库生成的自增 ID。
5. `db.commit()`
6. 返回 `VideoPublic`。

输出去向：

- 前端拿到新视频的公开信息，包括 `id`。
- MySQL 中新增一条 `videos` 记录。

## 10. 视频查询链路

作者视频列表：

1. 前端调用 `POST /video/listByAuthorID`。
2. `VideoService.list_by_author_id`
3. `VideoRepository.list_by_author_id`
4. SQL 按 `author_id` 查询，并按 `create_time desc, id desc` 排序。
5. 返回 `list[VideoPublic]`。

视频详情：

1. 前端调用 `POST /video/getDetail`。
2. `get_optional_user` 做软鉴权。
3. `VideoService.get_detail`
4. `VideoRepository.get_by_id`
5. 找到则返回 `VideoPublic`，找不到则返回 404。

## 11. 面试表达

可以这样讲 Day 2：

> 第二阶段我把登录态从 Day 1 的临时 token 升级成了更接近真实项目的双 token 模型。access token 使用 JWT，负责短期访问鉴权；refresh token 是服务端保存的随机字符串，用来刷新 access token。为了支持主动登出，我没有做纯无状态 JWT，而是把当前有效 token 存在 MySQL，同时把它缓存到 Redis。鉴权时先验 JWT，再查 Redis，Redis miss 时回源 MySQL 并回填缓存。这样既保留了 JWT 的自包含能力，又能实现服务端主动失效。

如果面试官问“Redis 挂了怎么办”，可以这样回答：

> Redis 在这里是性能层，不是数据真相。`get_cached_access_token` 读 Redis 失败会返回 None，然后鉴权链路回源 MySQL。Redis 挂了会让鉴权多查数据库，但不会导致核心登录态不可用。

如果面试官问“为什么视频详情用软鉴权”，可以这样回答：

> 视频详情和 Feed 这类接口通常允许游客访问，但如果用户登录了，后续可以顺便返回是否点赞、是否关注等个性化状态。所以我用软鉴权：不带 token 不影响访问；带了错误 token 则说明前端登录态异常，需要明确返回 401。
