# Day 3 学习笔记：点赞、评论、事务与基础 Feed 分页

## 1. 今天解决了什么问题

Day 3 不只是新增几个接口，而是开始进入真实后端里很常见的两个问题：

1. 写操作的一致性：点赞关系和视频计数必须一起成功或一起失败。
2. 列表分页的稳定性：Feed 不能简单依赖 offset，而要用游标继续向后翻。

本阶段完成：

- `likes` 表。
- `comments` 表。
- 点赞、取消点赞、是否点赞。
- 评论发布、删除、列表。
- 最新 Feed：`create_time < cursor`。
- 点赞榜 Feed：`likes_count + id` 复合游标。

## 2. 为什么点赞需要单独的 likes 表

如果只在 `videos` 表里存一个 `likes_count`，我们只能知道“多少人点了赞”，但不知道“谁点了赞”。

真实系统需要回答：

- 当前用户有没有点过这个视频。
- 同一个用户不能重复点赞。
- 用户取消点赞时，只能取消自己的点赞。
- Feed 里要显示 `is_liked`。

所以我们用 `likes` 表保存关系：

```text
video_id + account_id
```

并加联合唯一索引：

```text
uq_likes_video_account
```

这个索引是最后一道保险。即使业务层因为并发没拦住重复点赞，数据库也不会允许同一用户对同一视频插入两条点赞关系。

## 3. 为什么还要冗余 likes_count

如果每次展示视频都去 `likes` 表里 `count(*)`，会有两个问题：

- 列表页每条视频都动态 count，查询成本高。
- 点赞榜需要按点赞数排序，如果每次都聚合排序，成本更高。

所以我们在 `videos` 表中冗余 `likes_count`：

```text
likes 表：保存谁点过赞，负责关系正确性。
videos.likes_count：保存点赞数量，负责列表展示和排序性能。
```

冗余字段的代价是：写入时必须保证关系表和计数字段一致。

## 4. 点赞链路的数据流

输入来源：

- 前端或 Swagger 调用 `POST /like/like`。
- 请求头带 `Authorization: Bearer <token>`。
- 请求体是 `LikeRequest`，包含 `video_id`。

函数链路：

1. `get_current_user`
   - 硬鉴权，确认当前登录用户。
2. `api/like.py::like_video`
   - 创建 `LikeService`。
3. `LikeService.like`
   - 调用 `VideoRepository.exists` 确认视频存在。
   - 调用 `LikeRepository.is_liked` 做业务层重复检查。
   - 调用 `LikeRepository.create` 插入点赞关系。
   - 调用 `VideoRepository.increment_like_counters` 增加 `likes_count` 和 `popularity`。
4. `api/like.py::like_video`
   - `db.commit()` 提交事务。

输出去向：

- `likes` 表新增一条关系。
- `videos.likes_count` 加 1。
- 接口返回 `{"message": "video liked"}`。

如果中间任何一步失败，API 层会 `rollback`，这次请求不会留下半截数据。

## 5. 取消点赞链路

输入来源：

- `POST /like/unlike`。
- 请求头带 token。
- 请求体包含 `video_id`。

函数链路：

1. `get_current_user`
2. `LikeService.unlike`
3. `VideoRepository.exists`
4. `LikeRepository.delete`
5. `VideoRepository.decrement_like_counters`
6. `db.commit()`

关键点：

```python
likes_count = GREATEST(likes_count - 1, 0)
```

这样即使数据异常，也不会把点赞数减成负数。

## 6. 评论链路

发布评论：

1. `POST /comment/publish`
2. `get_current_user`
3. `CommentService.publish`
4. `VideoRepository.exists`
5. `CommentRepository.create`
6. `VideoRepository.increment_popularity`
7. `db.commit()`

删除评论：

1. `POST /comment/delete`
2. `get_current_user`
3. `CommentRepository.get_by_id`
4. 校验 `comment.author_id == current_user.id`
5. `CommentRepository.delete_by_id`
6. `VideoRepository.decrement_popularity`
7. `db.commit()`

评论列表：

1. `POST /comment/listAll`
2. `CommentService.list_all`
3. `VideoRepository.exists`
4. `CommentRepository.list_by_video_id`
5. 返回 `list[CommentPublic]`

## 7. Feed 最新流

最新 Feed 的请求体：

```json
{
  "limit": 10,
  "latest_time": 0
}
```

第一页传 `latest_time = 0`。

后端按：

```text
create_time DESC, id DESC
```

查询视频。

返回结果里有：

```text
next_time = 本页最后一条视频的 create_time 毫秒时间戳
```

下一页再带上这个 `next_time`，后端使用：

```text
create_time < cursor
```

继续往后查。

## 8. 点赞榜为什么要复合游标

点赞榜的核心问题是：`likes_count` 不是唯一字段。

真实数据里经常会出现很多视频点赞数相同，例如：

```text
id=10 likes_count=5
id=9  likes_count=5
id=8  likes_count=5
id=7  likes_count=4
id=6  likes_count=3
```

如果只写：

```sql
ORDER BY likes_count DESC
LIMIT 2;
```

第一页可能返回：

```text
id=10 likes_count=5
id=9  likes_count=5
```

假设我们把第一页最后一条的 `likes_count=5` 当成下一页游标，然后下一页这样查：

```sql
WHERE likes_count < 5
ORDER BY likes_count DESC
LIMIT 2;
```

那么 `id=8 likes_count=5` 会被直接跳过，因为它的点赞数也等于 5，并不满足 `likes_count < 5`。

这就是只用单字段游标的问题：排序字段不唯一时，游标无法精确表达“上一页最后一条之后的位置”。

所以点赞榜排序必须先变成稳定排序：

```sql
ORDER BY likes_count DESC, id DESC
```

它的含义是：

```text
先按点赞数从高到低排；
如果点赞数相同，再按 id 从大到小排。
```

这样 MySQL 得到的顺序就是确定的：

```text
id=10 likes_count=5
id=9  likes_count=5
id=8  likes_count=5
id=7  likes_count=4
id=6  likes_count=3
```

第一页最后一条是：

```text
id=9 likes_count=5
```

下一页就要表达“从 `likes_count=5, id=9` 后面继续查”，SQL 条件是：

```sql
WHERE likes_count < 5
   OR (likes_count = 5 AND id < 9)
ORDER BY likes_count DESC, id DESC
LIMIT 2;
```

这样下一页会返回：

```text
id=8 likes_count=5
id=7 likes_count=4
```

不会漏掉 `id=8`。

从 MySQL 原理上看，`ORDER BY likes_count DESC, id DESC` 最好配合复合索引：

```sql
CREATE INDEX ix_videos_likes_count_id ON videos(likes_count, id);
```

索引可以理解成 MySQL 提前维护好的一份“有序目录”。如果查询的排序字段和索引字段一致，MySQL 可以更容易沿着索引顺序扫描结果，而不是每次都把大量数据取出来重新排序。

如果使用 offset 分页：

```sql
ORDER BY likes_count DESC, id DESC
LIMIT 10 OFFSET 10000;
```

MySQL 通常仍然要先沿着排序结果跳过前面 10000 条，再取后面 10 条。offset 越深，跳过的数据越多，性能越差。

游标分页则是告诉 MySQL：

```text
我已经看到上一页最后一条是 (likes_count=5, id=9)，请从它后面继续找。
```

所以点赞榜的复合游标不是为了“写法复杂一点”，而是为了解决两个问题：

1. `likes_count` 不唯一，必须用 `id` 补成稳定顺序。
2. 深分页不适合用 offset，游标能更自然地沿着索引继续扫描。

面试时可以这样说：

> 点赞榜不能只用 `likes_count` 做游标，因为点赞数不是唯一字段，很多视频可能点赞数相同。如果只用 `likes_count < cursor`，会漏掉同点赞数但还没展示的数据。所以我把排序设计成 `likes_count DESC, id DESC`，并把 `(likes_count, id)` 作为复合游标。下一页条件是 `likes_count < cursor_likes OR (likes_count = cursor_likes AND id < cursor_id)`，这样能保证翻页不重复、不遗漏；同时配合 `(likes_count, id)` 复合索引，比深 offset 更适合 Feed 场景。

## 9. Feed 响应里的 is_liked 怎么来

Feed 接口是软鉴权：

- 不登录也可以看 Feed。
- 登录后会返回每条视频的 `is_liked`。

函数链路：

1. `get_optional_user`
2. `FeedService.list_latest` 或 `FeedService.list_likes_count`
3. `FeedRepository` 查询视频列表。
4. `LikeRepository.batch_liked_video_ids` 一次性查出当前用户点赞过的视频 ID。
5. `_build_feed_items` 把 `Video` 转成 `FeedVideoItem`。

这里用批量查询，避免每条视频都单独查一次是否点赞。

## 10. 面试表达

可以这样讲 Day 3：

> 第三阶段我实现了点赞、评论和基础 Feed。点赞不是简单给视频计数加一，而是先在 `likes` 表保存用户和视频的关系，并用联合唯一索引保证同一用户不能重复点赞；同时在 `videos.likes_count` 中冗余计数，用于列表展示和点赞榜排序。点赞和计数更新在同一个数据库事务里完成，失败就回滚，避免关系表和计数字段不一致。

如果面试官问“为什么不每次动态 count likes 表”，可以回答：

> 动态 count 在单个详情页还可以接受，但 Feed 列表和点赞榜会涉及很多视频。如果每条视频都去聚合 count，查询成本高，也不利于排序。所以我用 `likes` 表保证关系正确性，用 `videos.likes_count` 做读优化，写入时通过事务维护一致性。

如果面试官问“什么是复合游标”，可以回答：

> 当排序字段不唯一时，只用一个游标会导致重复或漏数据。点赞榜按 `likes_count DESC` 排序，但很多视频点赞数可能相同，所以我把 `id DESC` 作为第二排序字段。下一页条件写成 `likes_count < cursor_likes OR (likes_count = cursor_likes AND id < cursor_id)`，这样就能稳定地从上一页最后一条之后继续查。
