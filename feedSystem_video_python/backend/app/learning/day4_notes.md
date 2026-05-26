# Day 4 学习笔记：关注、标签与 Redis 缓存

## 1. 今天解决了什么问题

Day 4 开始把系统从“能看公共视频”推进到“有关系、有分类、有缓存”的阶段。

本阶段完成：

- `socials` 表：保存用户关注作者的关系。
- `tags` 表和 `video_tags` 表：保存 `#标签` 和视频之间的多对多关系。
- 关注、取关、粉丝列表、关注列表、关注统计接口。
- 发布视频时自动提取标题和描述里的 `#tag`。
- 标签 Feed：按标签查询视频。
- 关注 Feed：只看自己关注作者的视频。
- 视频详情 Redis 缓存。
- 最新 Feed Redis 短 TTL 缓存。

## 2. 为什么关注关系是多对多

一个用户可以关注很多作者，一个作者也可以被很多用户关注。

所以不能把关注关系简单写在 `accounts` 表某一个字段里，而是要用关系表：

```text
socials
  follower_id  关注者
  vlogger_id   被关注的作者
```

并加联合唯一约束：

```text
uq_socials_follower_vlogger
```

它保证同一个用户不能重复关注同一个作者。

## 3. 关注接口的数据流

输入来源：

- 前端或 Swagger 调用 `POST /social/follow`。
- 请求头带 `Authorization: Bearer <token>`。
- 请求体是 `FollowRequest`，包含 `vlogger_id`。

函数链路：

1. `get_current_user`
   - 硬鉴权，拿到当前登录用户。
2. `api/social.py::follow`
   - 创建 `SocialService`。
3. `SocialService.follow`
   - 判断不能关注自己。
   - 调用 `AccountRepository.find_by_id` 确认作者存在。
   - 调用 `SocialRepository.is_followed` 做业务层重复检查。
   - 调用 `SocialRepository.follow` 插入关注关系。
4. `api/social.py::follow`
   - `db.commit()` 提交事务。

输出去向：

- 成功返回 `{ "message": "followed" }`。
- 数据写入 MySQL 的 `socials` 表。

## 4. 关注流的数据流

输入来源：

- 前端或 Swagger 调用 `POST /feed/listByFollowing`。
- 请求头带登录 token。
- 请求体包含 `limit` 和 `latest_time`。

函数链路：

1. `get_current_user`
   - 拿到当前用户 ID。
2. `api/feed.py::list_by_following`
   - 调用 `FeedService.list_by_following`。
3. `FeedService.list_by_following`
   - 把毫秒时间戳游标转成 `datetime`。
   - 调用 `FeedRepository.list_by_following`。
4. `FeedRepository.list_by_following`
   - 调用 `VideoRepository.list_by_following`。
5. `VideoRepository.list_by_following`
   - 先用子查询找出当前用户关注的 `vlogger_id`。
   - 再查 `videos.author_id IN (关注作者列表)`。
   - 按 `create_time DESC, id DESC` 返回。
6. `FeedService._build_feed_items`
   - 批量查询当前用户点赞过哪些视频。
   - 给每条 Feed 补充 `is_liked`。

输出去向：

- 返回 `video_list`、`next_time` 和 `has_more`。
- `next_time` 给前端作为下一页游标。

## 4.5 粉丝列表、关注列表和计数的数据流

粉丝列表输入来源：

- 前端或 Swagger 调用 `POST /social/getAllFollowers`。
- 请求体可以传 `vlogger_id`。
- 如果不传，默认查询当前登录用户的粉丝。

函数链路：

1. `api/social.py::get_all_followers`
   - `get_current_user` 解析 JWT，拿到当前用户。
2. `SocialService.get_all_followers`
   - 确定目标用户 ID。
   - 调用 `AccountRepository.find_by_id` 校验目标用户存在。
   - 调用 `SocialRepository.list_followers` 查询粉丝账号列表。
   - 调用 `SocialRepository.count_followers` 查询粉丝数。
3. API 层把账号 ORM 对象转换为 `AccountPublic`。

输出去向：

- 返回 `followers` 和 `follower_count`。
- 数据来自 MySQL 的 `socials` 表和 `accounts` 表。
- 响应不会返回密码哈希、token、refresh token 等敏感字段。

关注列表输入来源：

- 前端或 Swagger 调用 `POST /social/getAllVloggers`。
- 请求体可以传 `follower_id`。
- 如果不传，默认查询当前登录用户关注了谁。

函数链路：

1. `api/social.py::get_all_vloggers`
2. `SocialService.get_all_vloggers`
3. `AccountRepository.find_by_id`
4. `SocialRepository.list_vloggers`
5. `SocialRepository.count_vloggers`

输出去向：

- 返回 `vloggers` 和 `vlogger_count`。
- 数据来自 MySQL。

关注计数输入来源：

- 前端调用 `POST /social/getCounts`。
- 当前用户来自 JWT。

函数链路：

1. `api/social.py::get_counts`
2. `SocialService.get_counts`
3. `SocialRepository.count_followers(current_user.id)`
4. `SocialRepository.count_vloggers(current_user.id)`

框架和数据库知识点：

- 这些接口都使用 FastAPI `Depends(get_current_user)`，因为它们是登录后用户关系数据。
- `socials(follower_id, vlogger_id)` 是关系表，保存“谁关注了谁”。
- 查询粉丝和关注列表本质上是通过关系表找到账号 ID，再回到 `accounts` 表取公开资料。

## 5. 为什么标签要拆成 tags 和 video_tags

一个视频可以有多个标签，一个标签也可以对应多个视频。

所以标签也是多对多：

```text
tags
  id
  name

video_tags
  video_id
  tag_id
```

这样做的好处：

- `tags.name` 可以唯一，避免同一个标签重复存很多份。
- `video_tags` 可以表达一个视频拥有多个标签。
- 标签 Feed 可以通过 join 查询出来。

## 6. 发布视频时标签如何流动

输入来源：

- 前端或 Swagger 调用 `POST /video/publish`。
- 标题或描述里包含 `#backend`、`#Python` 这样的文本。

函数链路：

1. `api/video.py::publish`
   - 硬鉴权拿到当前用户。
   - 创建 `VideoService`。
2. `VideoService.publish`
   - 调用 `VideoRepository.create` 写入 `videos` 表。
   - 调用 `extract_tags` 从标题和描述中提取标签。
   - 调用 `TagRepository.attach_tags` 写入标签关系。
   - 调用 `delete_cache_prefix("v1:feed:latest:")` 清理最新 Feed 缓存。
3. `TagRepository.attach_tags`
   - 对每个标签调用 `get_or_create`。
   - 不存在就写入 `tags` 表。
   - 再写入 `video_tags` 表。
4. `api/video.py::publish`
   - `db.commit()` 提交事务。

输出去向：

- 返回新发布的视频信息。
- MySQL 中新增 `videos`、`tags`、`video_tags` 数据。
- 最新 Feed 缓存会被删除，避免新视频发布后列表短时间不刷新。

## 7. 标签流的数据流

输入来源：

- 前端或 Swagger 调用 `POST /feed/listByTag`。
- 请求体包含 `tag_name`、`limit` 和 `latest_time`。

函数链路：

1. `api/feed.py::list_by_tag`
   - 软鉴权，游客也能查标签流。
2. `FeedService.list_by_tag`
   - 去掉用户可能传入的 `#` 前缀。
   - 把 `latest_time` 转成游标。
3. `FeedRepository.list_by_tag`
   - 调用 `VideoRepository.list_by_tag`。
4. `VideoRepository.list_by_tag`
   - `videos JOIN video_tags JOIN tags`。
   - 用 `tags.name = tag_name` 过滤。
   - 按发布时间倒序返回。
5. `FeedService._build_feed_items`
   - 如果用户登录，补充 `is_liked`。

输出去向：

- 返回对应标签下的视频列表。

## 8. Redis 在这里的定位

Redis 不是数据真相。

本项目里：

```text
MySQL：保存账号、视频、点赞、评论、关注、标签这些业务事实。
Redis：保存可以从 MySQL 重新计算出来的缓存。
```

所以 Redis 挂了，核心接口仍然能用，只是会回源 MySQL，性能下降。

## 9. 视频详情缓存的数据流

输入来源：

- 前端或 Swagger 调用 `POST /video/getDetail`。

函数链路：

1. `api/video.py::get_detail`
   - 软鉴权，游客可访问，坏 token 返回 401。
2. `VideoService.get_detail`
   - 生成 key：`v1:video:detail:{video_id}`。
   - 调用 `get_json_cache` 读 Redis。
3. 如果缓存命中：
   - 用 `VideoPublic.model_validate` 转回响应模型。
   - 直接返回。
4. 如果缓存未命中：
   - 调用 `VideoRepository.get_by_id` 查 MySQL。
   - 查不到抛 `VideoNotFoundError`。
   - 查到后转成 `VideoPublic`。
   - 调用 `set_json_cache` 写 Redis，TTL 为 300 秒。

输出去向：

- 返回视频详情。
- 第二次查询同一视频时优先从 Redis 读。

## 10. 为什么写操作后删除缓存，而不是更新缓存

写操作包括：

- 点赞。
- 取消点赞。
- 评论发布。
- 评论删除。
- 发布新视频。

这些操作都会影响详情或 Feed 列表。

我们选择“写 DB 后删缓存”，原因是：

- 更新缓存要重新组装完整响应，容易漏字段。
- 多个写操作并发时，直接更新缓存更容易出现旧数据覆盖新数据。
- 删除缓存更简单：下一次读发现 miss，再从 MySQL 重新读最新数据并回填。

这就是 Cache-Aside 的常见写法：

```text
读：先 Redis，miss 查 MySQL，再写 Redis。
写：先写 MySQL，再删除 Redis。
```

## 11. 最新 Feed 为什么只做短 TTL 缓存

最新 Feed 更新频率高，用户一发布新视频，第一页就应该尽快变化。

所以我们只给最新 Feed 做 5 秒短缓存：

```text
v1:feed:latest:viewer={viewer_id}:limit={limit}:before={latest_time}
```

这里包含 `viewer_id`，是因为 Feed 项里有 `is_liked`。同一批视频，游客和不同登录用户看到的 `is_liked` 可能不一样。

短 TTL 的意义是：

- 连续刷新时减少 MySQL 压力。
- 缓存最多只旧 5 秒，学习阶段可以接受。
- Redis 挂了直接查 MySQL，不影响正确性。

## 12. 面试表达

可以这样讲 Day 4：

> Day 4 我补了关系型业务和缓存层。关注关系用 `socials(follower_id, vlogger_id)` 表示多对多，并用联合唯一约束防重复。标签用 `tags` 和 `video_tags` 建模，因为视频和标签也是多对多；发布视频时从标题和描述里提取 `#tag`，在同一个数据库事务里写入视频和标签关系。Feed 部分新增了关注流和标签流，本质上都是在视频查询前增加关系过滤。
>
> Redis 这部分我没有把它当成数据真相，而是作为 Cache-Aside 性能层：视频详情先读 Redis，miss 后查 MySQL 并回填；点赞、评论这类写操作后删除详情缓存；最新 Feed 做 5 秒短 TTL 缓存。这样 Redis 不可用时系统仍然可以回源 MySQL，只是性能下降。

可能被追问：为什么 Feed 缓存 key 要带 `viewer_id`？

> 因为 Feed 返回里有 `is_liked`，这是和当前登录用户相关的字段。如果所有用户共用同一个 Feed 缓存，就可能把 A 用户的点赞状态返回给 B 用户。所以我把 `viewer_id` 放进 key；游客用 0，登录用户用自己的账号 ID。
