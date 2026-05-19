# feedSystem_video_python 执行过程记录

> 这个文件用于记录 Python 重构项目的真实推进过程。后续每次继续学习/开发前，先读 `plan.md` 和本文件，就能知道我们走到哪里、做过什么、下一步该做什么。

## 当前状态

- 当前阶段：Day 4 - 关注、标签与 Redis 缓存
- 当前日期：2026-05-11
- 当前目标：完成关注关系、标签流、视频详情缓存和 Feed 短缓存，并理解 Cache-Aside
- 当前运行方式：
  - 后端 FastAPI：本地运行
  - 前端：本地运行
  - MySQL：用户已手动启动 Docker 容器 `YYmysql`，`localhost:3306`
  - Redis：用户已手动启动 Docker 容器 `YYredis`，`localhost:6379`，无密码

## 已完成

1. 已完整阅读 Go 参考项目与说明文档。
2. 已确认 Go 项目核心定位：
   - 短视频 Feed 系统。
   - Go 版本作为参考实现。
   - Python 版本用于学习式重构，不逐行翻译。
3. 已创建 `plan.md`。
4. 已将计划调整为 5 天学习路线。
5. 已确认本阶段暂不实现 RabbitMQ，但预留 `EventPublisher` 扩展点。
6. 已根据本地 Docker MySQL 配置修正端口：
   - MySQL 使用 `localhost:3306`。
   - `DATABASE_URL` 使用 `mysql+asyncmy://root:123456@127.0.0.1:3306/feedsystem`。
7. 已创建前后端分离目录：
   - `backend/`
   - `frontend/`
8. 已创建 Day 1 后端分层结构：
   - `app/api`
   - `app/core`
   - `app/models`
   - `app/repositories`
   - `app/schemas`
   - `app/services`
   - `app/learning`
9. 已实现 Day 1 后端代码：
   - FastAPI 应用入口 `app/main.py`
   - 配置加载 `app/config.py`
   - MySQL async SQLAlchemy 连接 `app/database.py`
   - `Account` 模型 `app/models/account.py`
   - 注册、登录、查用户 API `app/api/account.py`
   - 密码哈希工具 `app/core/security.py`
   - 账号 Repository / Service
10. 已创建 Day 1 学习材料：
   - `backend/app/learning/day1_notes.md`
   - `backend/app/learning/day1_practice.py`
11. 已添加 `.gitignore`，忽略 Python 缓存、虚拟环境和本地 `.env`。
12. 已运行 `python -m compileall backend\app`，Day 1 代码语法检查通过。
13. 已将 README、代码注释/docstring、Day 1 学习材料改为中文。
14. 已增强 `day1_notes.md`，补充每个功能的数据流、函数链路、输入来源和输出去向。
15. 已新增 `backend/requirements.txt`，用于在虚拟环境中安装 Python 后端依赖。
16. 已确认用户本机已有 MySQL/Redis 容器，`docker-compose.yml` 仅作为备用环境配置，不是必须执行。
17. 已将默认 Redis 连接改为无密码：`redis://127.0.0.1:6379/0`。
18. 已发现手动启动的 `YYmysql` 未创建 `feedsystem` 数据库；已在 README 和 Day 1 notes 中补充建库命令。
19. 已给 Day 1 后端现有每个函数补充中文注释/文档字符串，帮助阅读函数职责和数据链路。
20. 已完成 Day 1 面试表达复盘，补充异步方法、bcrypt 线程池、MySQL 建库等追问素材。
21. 已新增 Day 2 依赖：
   - `PyJWT`
   - `redis`
22. 已将 Day 1 临时 token 升级为 JWT access token + refresh token。
23. 已新增 Redis token 缓存工具：
   - `cache_access_token`
   - `get_cached_access_token`
   - `delete_cached_access_token`
24. 已实现硬鉴权依赖 `get_current_user`。
25. 已实现软鉴权依赖 `get_optional_user`。
26. 已实现账号接口：
   - `POST /account/refresh`
   - `POST /account/logout`
   - `POST /account/me`
27. 已创建 `videos` 表模型。
28. 已实现视频模块分层结构：
   - `app/models/video.py`
   - `app/schemas/video.py`
   - `app/repositories/video_repo.py`
   - `app/services/video_service.py`
   - `app/api/video.py`
29. 已实现视频接口：
   - `POST /video/publish`
   - `POST /video/listByAuthorID`
   - `POST /video/getDetail`
30. 已新增 Day 2 学习材料：
   - `backend/app/learning/day2_notes.md`
   - `backend/app/learning/day2_practice.py`
31. 已更新后端 README，补充 Day 2 依赖安装与 Swagger 验证顺序。
32. 已运行 `python -m compileall backend\app`，Day 2 代码语法检查通过。
33. 用户已通过 Swagger 验证 Day2 接口，MySQL 写入正常。
34. 用户已确认 Redis 中存在 `v1:account:1`，说明 access token 已写入 Redis。
35. 已参考 Go 版本前端创建 Python 版本前端联调工作台。
36. 已实现前端 API client：
   - 统一 `/api` 代理请求。
   - 自动携带 `Authorization: Bearer <token>`。
   - 401 时尝试使用 refresh token 自动续签并重试。
37. 已实现 Day1-2 前端页面：
   - 注册
   - 登录
   - 当前用户
   - 刷新 token
   - 登出
   - 用户查询
   - 发布视频
   - 作者视频列表
   - 视频详情
   - 接口日志
38. 已运行前端构建 `npm run build`，TypeScript 和 Vite 构建通过。
39. 已启动前端开发服务：`http://127.0.0.1:5173`。
40. 已启动后端服务并通过前端代理验证 `/api/health`。
41. 已通过前端代理完成接口联调：
   - 注册临时用户
   - 登录获取 token
   - 发布视频
   - 查询作者视频列表
   - 查询视频详情
42. 已开始 Day3 后端任务：点赞、评论、事务和基础 Feed。
43. 已参考 Go 版本点赞、评论和 Feed 关键流程。
44. 已新增 `likes` 表模型，并建立 `(video_id, account_id)` 联合唯一约束。
45. 已新增 `comments` 表模型。
46. 已实现点赞模块：
   - `POST /like/like`
   - `POST /like/unlike`
   - `POST /like/isLiked`
47. 已实现评论模块：
   - `POST /comment/publish`
   - `POST /comment/delete`
   - `POST /comment/listAll`
48. 已实现基础 Feed：
   - `POST /feed/listLatest`
   - `POST /feed/listLikesCount`
49. 已将点赞关系写入和 `videos.likes_count` 更新放入同一个请求事务。
50. 已实现取消点赞时 `likes_count` 防负数。
51. 已实现 Feed 的 `is_liked` 批量补充逻辑。
52. 已新增 Day3 学习材料：
   - `backend/app/learning/day3_notes.md`
   - `backend/app/learning/day3_practice.py`
53. 已更新后端 README，补充 Day3 Swagger 验证顺序。
54. 已运行 `python -m compileall backend\app`，Day3 代码语法检查通过。
55. 已通过本地接口验证 Day3 最小链路：
   - 用户 A 发布视频。
   - 用户 B 点赞。
   - 用户 B 查询是否点赞。
   - 用户 B 发布评论。
   - 查询评论列表。
   - 查询最新 Feed。
   - 查询点赞榜 Feed。
   - 用户 B 取消点赞后视频点赞数回到 0。
56. 已验证同一用户重复点赞会返回 409。
57. 已将前端从“联调工作台”改成“正常业务主页面 + 右侧接口日志栏”。
58. 前端已接入 Day3 接口：
   - 最新 Feed
   - 点赞榜 Feed
   - 点赞 / 取消点赞 / 是否点赞
   - 评论发布 / 评论列表
59. 已确定当前视频和封面资源策略：
   - 暂不收集真实图片也不做上传。
   - 前端根据视频 ID 生成稳定色块占位。
   - `play_url` 和 `cover_url` 仍保留入库字段，默认使用 `debug://...` 占位值。
60. 已运行 `npm run build`，前端新布局构建通过。
61. 已确认 `http://127.0.0.1:5173` 返回 200。
62. 已根据用户反馈继续调整前端：
   - 参考 Go 版本 AppShell，把主区域改成左侧导航 + 中间业务主区域。
   - 右侧继续保留接口日志。
   - 中等宽度下日志自动下移，避免主功能区被挤压。
   - 窄屏下导航、Feed、详情改为单列布局。
63. 已再次运行 `npm run build`，新版响应式布局构建通过。
64. 根据用户反馈做前端小调整：
   - 删除 Feed 区顶部“最新/点赞榜”重复切换按钮。
   - 只保留左侧导航作为榜单切换入口。
   - Feed 标题区只展示当前模式和刷新按钮。
   - 放宽宽屏下 Feed 与详情的网格宽度。
   - Feed 卡片描述改为最多两行，降低文字堆积感。
65. 已再次运行 `npm run build`，本次 UI 小改构建通过。
66. 根据浏览器截图修复视频详情卡布局：
   - 视频占位区改为详情卡顶部完整宽度展示。
   - 标题、描述、计数和按钮放在视频下方。
   - 避免宽屏时详情文字堆积在视频右侧。
67. 已再次运行 `npm run build`，详情卡修复构建通过。
68. 根据用户截图继续修复前端：
   - 清空登录和注册表单默认用户名/密码，只保留 placeholder。
   - 缩小左侧导航和右侧日志栏宽度占用。
   - 取消详情列过大的最小宽度，避免视频详情卡超出外层容器。
   - 视频占位高度改为 `clamp` 响应式高度。
69. 已再次运行 `npm run build`，本次修复构建通过。
70. 开始 Day4：关注、标签与 Redis 缓存。
71. 新增 `socials` 表模型，并使用 `(follower_id, vlogger_id)` 联合唯一约束防止重复关注。
72. 新增关注模块：
   - `app/models/social.py`
   - `app/schemas/social.py`
   - `app/repositories/social_repo.py`
   - `app/services/social_service.py`
   - `app/api/social.py`
73. 实现关注接口：
   - `POST /social/follow`
   - `POST /social/unfollow`
   - `POST /social/getAllFollowers`
   - `POST /social/getAllVloggers`
   - `POST /social/getCounts`
74. 新增标签模块：
   - `app/models/tag.py`
   - `app/core/tags.py`
   - `app/repositories/tag_repo.py`
75. 发布视频时会从标题和描述中提取 `#tag`，写入 `tags` 和 `video_tags` 表。
76. 新增 Feed 查询：
   - `POST /feed/listByFollowing`
   - `POST /feed/listByTag`
77. 扩展 Redis 工具：
   - JSON 缓存读写。
   - 视频详情缓存 key。
   - 最新 Feed 短缓存 key。
   - 按前缀删除缓存。
78. 视频详情接口接入 Cache-Aside：
   - 先查 Redis。
   - miss 后查 MySQL。
   - 回填 Redis，TTL 300 秒。
79. 最新 Feed 接入短 TTL 缓存，缓存 key 包含 `viewer_id`，避免 `is_liked` 个性化字段串用户。
80. 点赞、取消点赞、评论发布、评论删除后会删除视频详情缓存。
81. 发布视频后会删除最新 Feed 缓存，避免新视频发布后列表短时间不刷新。
82. 前端新增 Day4 API 封装：
   - `frontend/src/api/social.ts`
   - `listByFollowing`
   - `listByTag`
83. 前端左侧导航新增关注流和标签流入口，视频详情区新增关注作者和取关作者按钮。
84. 新增 Day4 学习材料：
   - `backend/app/learning/day4_notes.md`
   - `backend/app/learning/day4_practice.py`
85. 更新后端 README，补充 Day4 验证顺序。
86. 已运行 `python -m compileall .\feedSystem_video_python\backend\app`，Day4 后端语法检查通过。
87. 已运行 `npm run build`，Day4 前端构建通过。
88. 已通过本地 HTTP 验证 Day4 最小链路：
   - 用户 A 发布带 `#backend` 的视频。
   - 用户 B 关注用户 A。
   - 标签流能查到视频。
   - 关注流能查到视频。
   - `socials`、`tags`、`video_tags` 均写入 MySQL。
   - 视频详情缓存和最新 Feed 短缓存均能写入 Redis。
89. 根据用户截图修复 Day4 后前端视频详情页样式：
   - 将详情元信息区 `.video-meta` 从两列改为单列。
   - 避免关注/取关按钮组挤压标题宽度。
   - 标题改用正常换行，避免被压成逐字竖排。
   - 已再次运行 `npm run build`，构建通过。

## 关键约定

### 学习节奏

每个模块都按下面顺序推进：

1. 先讲思想。
2. 再看 Go 参考实现的关键流程。
3. 再写 Python 代码。
4. 在 `learning/*_practice.py` 中安排亲手敲练习；练习前先讲清为什么这样写。
5. 最后做面试表达复盘。

### 代码策略

- 目标是 5 天内完成能跑、能讲、能演示的 MVP。
- 不追求覆盖 Go 项目所有细节。
- 优先掌握后端核心思想：分层、数据库设计、鉴权、事务、分页、Redis。
- MQ / Worker / SSE / 热榜滑动窗口暂不做真实实现，只保留扩展点。

### 运行策略

```text
本地运行:
  FastAPI 后端: http://127.0.0.1:8000
  前端开发服务: http://127.0.0.1:5173

Docker 运行:
  MySQL: localhost:3306
  Redis: localhost:6379
```

## Day 1 计划

主题：项目骨架、数据库、用户注册登录。

### 要学习的思想

- FastAPI 项目如何启动。
- 为什么后端项目要分层。
- SQLAlchemy Model / Schema / Repository / Service 的边界。
- 为什么密码不能明文存储。
- bcrypt 哈希密码的意义。

### 要完成的功能

- 创建 Python 项目骨架。
- 配置依赖文件。
- 配置环境变量。
- 接入 MySQL。
- 定义 `accounts` 表。
- 实现注册接口。
- 实现登录接口。

### 预留给用户亲手敲的重点

练习文件：`backend/app/learning/day1_practice.py`

练习重点：

- 为什么密码要哈希后入库。
- 为什么登录是校验哈希而不是解密。
- 为什么按用户名查询放在 Repository。

### Day 1 验收标准

- 能启动 FastAPI。
- Swagger 中能调用注册接口。
- Swagger 中能调用登录接口。
- MySQL 中能看到用户记录。
- 数据库中的密码是哈希值，不是明文。

## 执行日志

### 2026-05-09

- 创建本文件 `process.md`。
- 准备开始 Day 1：项目骨架、数据库、用户注册登录。
- 创建 `docker-compose.yml`，只管理 MySQL 和 Redis。
- 创建 `.env.example`。
- 创建 `backend/pyproject.toml`。
- 创建 `frontend/README.md`，前端 Day 1 暂不实现。
- 完成 Day 1 后端账号模块最小实现。
- Day 1 token 暂时使用随机 opaque token，Day 2 再替换成 JWT + Refresh Token。
- 完成基础语法检查并清理 `__pycache__`。
- 根据用户要求，将需要阅读的内容改成中文，并把 notes 写成链路说明。
- 新增 `backend/requirements.txt`，并在后端 README 中补充虚拟环境安装步骤。
- 说明 `docker-compose.yml` 的作用：它是备用的依赖启动配置；用户已有 `YYmysql`/`YYredis` 时不用再执行。
- 将 Redis 默认配置调整为无密码，匹配用户当前的 `YYredis` 容器。
- 排查后端启动失败：MySQL 报 `Unknown database 'feedsystem'`，原因是手动启动容器时没有创建业务数据库。
- 根据用户要求，给每个现有函数增加中文说明，降低阅读门槛。

### 2026-05-11

- 开始 Day 2：JWT、Refresh Token、鉴权依赖、视频发布。
- 在 `requirements.txt` 和 `pyproject.toml` 中新增 `PyJWT` 与 `redis`。
- 在 `.env.example` 中新增 JWT 配置：
  - `JWT_SECRET`
  - `JWT_ALGORITHM`
  - `ACCESS_TOKEN_MINUTES`
  - `REFRESH_TOKEN_DAYS`
- 新增 `app/core/auth.py`：
  - 生成 JWT access token。
  - 解析并校验 JWT。
  - 生成 refresh token。
  - 实现 `get_current_user` 硬鉴权。
  - 实现 `get_optional_user` 软鉴权。
- 新增 `app/core/redis.py`：
  - 使用 Redis 缓存当前有效 access token。
  - Redis 异常时返回 None，让鉴权链路回源 MySQL。
- 升级账号登录：
  - 登录成功后返回 access token 和 refresh token。
  - access token 写入 MySQL 和 Redis。
  - refresh token 写入 MySQL。
- 新增刷新 token 接口：
  - `POST /account/refresh`
  - 使用 refresh token 换新的 access token。
- 新增登出接口：
  - `POST /account/logout`
  - 清空 MySQL token 并删除 Redis token 缓存。
- 新增当前用户接口：
  - `POST /account/me`
  - 用来验证硬鉴权是否正常工作。
- 新增视频模块：
  - `videos` 表。
  - 视频发布。
  - 作者视频列表。
  - 视频详情。
- 将 `models/account.py` 中的 `func.now()` 改为 `datetime.now`，减少编辑器类型提示噪音，方便学习阅读。
- 新增 `day2_notes.md`，写清登录、鉴权、刷新、登出、视频发布、视频查询的数据流。
- 新增 `day2_practice.py`，预留 JWT 与鉴权依赖的亲手敲练习。
- 更新 README，补充 Day 2 的 Swagger 验证顺序。
- 运行 `python -m compileall .\feedSystem_video_python\backend\app`，语法检查通过。
- 用户通过 Redis CLI 看到 `v1:account:1`，确认 access token 已写入 Redis。
- 开始 Day1-2 前端同步工作，先不做完整 Feed 页面，只做当前已有接口的联调工作台。
- 参考 Go 前端的 Vite、Vue、API client、token 保存与 refresh 思路，创建 Python 前端工程。
- 新增前端工程文件：
  - `frontend/package.json`
  - `frontend/vite.config.ts`
  - `frontend/src/App.vue`
  - `frontend/src/style.css`
  - `frontend/src/api/client.ts`
  - `frontend/src/api/account.ts`
  - `frontend/src/api/video.ts`
  - `frontend/src/api/auth.ts`
  - `frontend/src/api/types.ts`
- 更新 `frontend/README.md`，补充启动方式和 `/api` 代理原理。
- 更新 `.gitignore`，忽略 `node_modules/`。
- 执行 `npm install`，前端依赖安装成功。
- 执行 `npm run build`，前端构建通过。
- 启动前端服务：`http://127.0.0.1:5173`。
- 启动后端服务：`http://127.0.0.1:8000`。
- 验证 `http://127.0.0.1:5173/api/health` 返回 `{"status":"ok"}`。
- 通过 Vite 代理完成最小业务联调：
  - 注册用户 `frontend_97522`
  - 登录返回账号 ID `3`
  - 发布视频 ID `3`
  - 作者视频列表返回 1 条
  - 视频详情标题为 `Frontend integration video`
- 记录用户新的前端想法：后续前端从“联调工作台”改成“正常业务页面 + 侧边栏日志输出”的形态。
- 开始 Day3：点赞、评论、事务和基础 Feed 分页。
- 新增 `likes` 表：
  - `video_id`
  - `account_id`
  - `created_at`
  - 联合唯一约束 `uq_likes_video_account`
- 新增 `comments` 表：
  - `video_id`
  - `author_id`
  - `username`
  - `content`
  - `created_at`
- 新增点赞 Repository / Service / API。
- 新增评论 Repository / Service / API。
- 新增 Feed Repository / Service / API。
- 扩展 `VideoRepository`：
  - 判断视频是否存在。
  - 增加点赞数和热度。
  - 减少点赞数和热度并防负数。
  - 最新 Feed 查询。
  - 点赞榜复合游标查询。
- 注册 Day3 路由到 `app/main.py`。
- 更新数据库初始化导入，让应用启动时自动创建 `likes` 和 `comments` 表。
- 新增 `day3_notes.md`，写清点赞、评论、Feed 的函数链路和数据流。
- 新增 `day3_practice.py`，预留事务和复合游标的亲手敲练习。
- 运行 `python -m compileall .\feedSystem_video_python\backend\app`，语法检查通过。
- 通过本地 HTTP 验证 Day3 链路：
  - 测试用户 A：`day3_a_41842`
  - 测试用户 B：`day3_b_41842`
  - 视频 ID：`5`
  - 评论 ID：`1`
  - 最新 Feed 返回 5 条
  - 点赞榜 Feed 返回 5 条
  - 取消点赞后 `likes_count = 0`
- 验证重复点赞：
  - 视频 ID：`6`
  - 第二次点赞返回 HTTP 409
- 按用户想法改造前端布局：
  - 主区域展示正常 Feed 页面和视频详情。
  - 右侧固定侧边栏展示接口日志。
  - 视频和封面暂时使用稳定色块占位，不需要先收集真实图片。
- 新增前端 Day3 API 封装：
  - `frontend/src/api/feed.ts`
  - `frontend/src/api/like.ts`
  - `frontend/src/api/comment.ts`
- 扩展前端类型：
  - Feed 响应。
  - 点赞响应。
  - 评论响应。
- 执行 `npm run build`，新前端构建通过。
- 根据用户反馈，继续精简主功能区并修复窗口大小变化时的布局挤压：
  - 参考 Go 版本的 `AppShell.vue` 和 `FeedVideoCard.vue`。
  - 改成左侧导航、主内容区、右侧日志区。
  - 删除原先占据主区域的大块账号表单，改成右上角账号弹层。
  - 增加 1260px、1040px、720px、460px 响应式断点。
  - 再次执行 `npm run build`，构建通过。
- 根据用户继续反馈，删除顶部重复榜单切换按钮，只保留左侧导航切换；同时调整 Feed 卡片宽度和描述行数，减少宽屏下文字堆积。
- 根据用户截图，修复视频详情页横向挤压问题：详情区改成上方视频占位、下方元信息和操作按钮。
- 根据用户继续截图反馈，修复详情容器超出外层容器的问题，并清空登录/注册表单预填值。

## 待办清单

- [x] Day 1：讲解项目分层思想。
- [x] Day 1：创建 Python 项目骨架。
- [x] Day 1：配置依赖与环境变量。
- [x] Day 1：接入 MySQL。
- [x] Day 1：定义 Account 模型。
- [x] Day 1：实现注册。
- [x] Day 1：实现登录。
- [x] Day 1：复盘面试表达。
- [x] Day 1：安装依赖并启动后端验证。
- [x] Day 1：用 Swagger 测注册和登录。
- [x] Day 1：基础语法检查。
- [x] Day 2：讲解 JWT access token 与 refresh token 的区别。
- [x] Day 2：实现 JWT access token。
- [x] Day 2：实现 refresh token。
- [x] Day 2：接入 Redis token 缓存。
- [x] Day 2：实现硬鉴权 `get_current_user`。
- [x] Day 2：实现软鉴权 `get_optional_user`。
- [x] Day 2：实现登出主动失效。
- [x] Day 2：创建 `videos` 表。
- [x] Day 2：实现视频发布。
- [x] Day 2：实现作者视频列表。
- [x] Day 2：实现视频详情。
- [x] Day 2：新增学习笔记和练习文件。
- [x] Day 2：基础语法检查。
- [x] Day 2：用户本地重新安装依赖。
- [x] Day 2：用户本地启动后端并创建 `videos` 表。
- [x] Day 2：用 Swagger 验证 refresh/logout/me/video 接口。
- [x] Day 2：验证 MySQL 写入正常。
- [x] Day 2：验证 Redis token 缓存正常。
- [x] Day 2.5：创建前端工程。
- [x] Day 2.5：实现前端 API client。
- [x] Day 2.5：实现账号联调页面。
- [x] Day 2.5：实现视频联调页面。
- [x] Day 2.5：前端构建通过。
- [x] Day 2.5：前端代理到后端 health 通过。
- [x] Day 2.5：通过前端代理完成注册、登录、发布视频、列表、详情联调。
- [x] Day 3：讲解点赞为什么需要事务。
- [x] Day 3：创建 `likes` 表。
- [x] Day 3：创建 `comments` 表。
- [x] Day 3：实现点赞。
- [x] Day 3：实现取消点赞。
- [x] Day 3：实现是否点赞。
- [x] Day 3：实现评论发布。
- [x] Day 3：实现评论删除。
- [x] Day 3：实现评论列表。
- [x] Day 3：实现最新 Feed 游标分页。
- [x] Day 3：实现点赞榜复合游标分页。
- [x] Day 3：新增学习笔记和练习文件。
- [x] Day 3：基础语法检查。
- [x] Day 3：本地接口验证点赞、评论、Feed 链路。
- [x] Day 3：验证重复点赞返回 409。
- [x] Day 3：前端接入点赞、评论和 Feed。
- [x] 前端后续改版：正常业务页面 + 侧边栏日志输出。
- [x] Day 4：讲解关注关系为什么是多对多。
- [x] Day 4：创建 `socials` 表。
- [x] Day 4：实现关注和取关。
- [x] Day 4：实现粉丝列表和关注列表。
- [x] Day 4：创建 `tags` 和 `video_tags` 表。
- [x] Day 4：发布视频时提取 `#tag`。
- [x] Day 4：实现标签流。
- [x] Day 4：实现关注流。
- [x] Day 4：视频详情接入 Redis Cache-Aside。
- [x] Day 4：最新 Feed 接入 Redis 短 TTL 缓存。
- [x] Day 4：新增学习笔记和练习文件。
- [x] Day 4：后端语法检查。
- [x] Day 4：前端构建检查。
- [x] Day 4：本地接口验证关注、标签和缓存链路。

## 决策记录

| 日期 | 决策 | 原因 |
|---|---|---|
| 2026-05-09 | Python 重构不逐行翻译 Go 项目 | 目标是学习后端思想，而不是代码搬运 |
| 2026-05-09 | 5 天内完成 MVP | 用户希望快速获得后端经验与面试讨论材料 |
| 2026-05-09 | 后端和前端本地运行，MySQL/Redis 放 Docker | 本地调试方便，依赖环境隔离 |
| 2026-05-09 | MySQL 使用 `localhost:3306` | 与用户 Docker MySQL 当前配置一致 |
| 2026-05-09 | 暂不实现 RabbitMQ | 先掌握主要功能、数据库和 Redis 接入，MQ 只预留扩展点 |
| 2026-05-09 | Day 1 token 先使用随机 opaque token | 避免第一天引入太多概念，Day 2 再系统学习 JWT 双 Token |
| 2026-05-09 | Day 1 练习放在 `app/learning/day1_practice.py` | 保证主程序能运行，同时让用户对照关键实现亲手敲一遍 |
| 2026-05-09 | 每天 notes 必须写清函数链路和数据流 | 用户要重点理解输入从哪来、经过哪些函数、输出去哪 |
| 2026-05-09 | Docker 镜像优先使用明确版本，不跟随 `latest` | 避免以后 `latest` 变化导致环境不一致 |
| 2026-05-09 | 用户已有 `YYmysql` 和 `YYredis` 容器时不再强制使用 compose | 避免重复启动同端口服务导致冲突 |
| 2026-05-09 | Redis 默认无密码 | 用户当前 `YYredis` 启动命令未配置密码 |
| 2026-05-09 | 手动 MySQL 容器需要先创建 `feedsystem` 数据库 | SQLAlchemy `create_all()` 只能建表，不能自动创建 database |
| 2026-05-09 | 每个函数至少写一句中文说明 | 当前项目以学习为主，可读性优先，方便理解变量、职责和调用链路 |
| 2026-05-11 | access token 使用 JWT，refresh token 使用服务端随机字符串 | access token 适合短期访问，refresh token 适合服务端控制长期登录态 |
| 2026-05-11 | JWT 仍然保存到 MySQL，并缓存到 Redis | 纯 JWT 不方便主动登出；MySQL 是登录态真相，Redis 是性能层 |
| 2026-05-11 | Redis 失败时回源 MySQL | Redis 不应该成为核心登录链路的单点故障 |
| 2026-05-11 | 视频发布使用硬鉴权，视频详情使用软鉴权 | 发布必须知道操作者是谁；详情允许游客访问，后续可扩展个性化状态 |
| 2026-05-11 | 前端先做联调工作台，不做完整产品页 | 当前阶段的核心目标是把 Day1-2 后端链路从浏览器跑通 |
| 2026-05-11 | 前端通过 Vite `/api` 代理访问 FastAPI | 前后端都本地运行，避免浏览器跨域干扰学习 |
| 2026-05-11 | 前端暂不做文件上传，只保存视频 URL | 后端 Day2 只实现视频元数据，文件上传后续再扩展 |
| 2026-05-11 | Day3 先完成后端接口，前端 Day3 接入后置 | 用户希望先完成 Day3 任务，前端布局改版后续再做 |
| 2026-05-11 | 点赞关系和视频计数在同一个事务提交 | 防止 likes 表和 videos.likes_count 出现不一致 |
| 2026-05-11 | likes 表使用 `(video_id, account_id)` 联合唯一约束 | 从数据库层保证同一用户不能重复点赞同一视频 |
| 2026-05-11 | 点赞榜使用 `likes_count + id` 复合游标 | 解决点赞数相同导致翻页重复或漏数据的问题 |
| 2026-05-11 | 后续前端改成“主页面 + 侧边栏日志” | 既保留学习调试信息，又让主体验更像正常产品页面 |
| 2026-05-11 | 视频和封面先用稳定色块占位 | 当前后端还没有上传和静态资源服务，先避免被素材问题阻塞联调 |
| 2026-05-11 | 前端主区域参考 Go 版 AppShell 精简 | 让页面更像真实产品页，避免表单堆叠占据主要体验 |
| 2026-05-11 | 日志栏在中等宽度自动下移 | 避免浏览器窗口变化时主功能区被右侧日志挤压 |
| 2026-05-11 | 关注关系使用 `socials(follower_id, vlogger_id)` 关系表 | 用户和作者是多对多关系，不能塞进账号表单字段 |
| 2026-05-11 | 标签使用 `tags` + `video_tags` 建模 | 视频和标签也是多对多关系，标签名需要唯一复用 |
| 2026-05-11 | 发布视频时同步提取标签并写入关系表 | 当前 MVP 先保证发布后标签流立刻可查，MQ 后续再预留 |
| 2026-05-11 | Redis 继续只做性能层，不做数据真相 | Redis 清空或宕机时仍可回源 MySQL，避免核心业务依赖缓存正确性 |
| 2026-05-11 | 视频详情使用 Cache-Aside | 读多写少场景适合先查缓存、miss 查 DB、再回填缓存 |
| 2026-05-11 | 写操作后删除缓存，而不是直接更新缓存 | 删除更简单可靠，避免并发写时旧响应覆盖新响应 |
| 2026-05-11 | 最新 Feed 只做 5 秒短缓存 | Feed 变化频繁，短 TTL 平衡性能和新鲜度 |
| 2026-05-11 | 最新 Feed 缓存 key 包含 `viewer_id` | Feed 响应里有 `is_liked`，不同用户不能共享个性化缓存 |
| 2026-05-11 | 视频详情元信息区改为单列布局 | Day4 增加关注按钮后，两列布局会压缩标题宽度，导致标题逐字换行 |

## 面试素材积累

后续每完成一个模块，都在这里补充一段“面试可讲”的表述。

### 项目总述草稿

这是一个仿短视频平台的 Feed 流后端系统。我用 Python/FastAPI 重构 Go 参考项目，重点学习真实后端项目中的分层设计、数据库建模、JWT 鉴权、事务一致性、Feed 分页和 Redis 缓存。当前 MVP 先不接 RabbitMQ，而是通过同步 MySQL 事务保证核心数据正确，同时在 Service 层预留事件发布接口，方便后续升级为异步优先、失败降级直写的架构。

### Day 1：账号注册登录模块

面试官如果问“你第一阶段做了什么”，可以这样讲：

> 第一阶段我先搭了 FastAPI 后端骨架，并实现了账号注册、登录和查询接口。这个阶段重点不是接口数量，而是把一个后端项目最基本的链路跑通：请求从 Swagger 或前端进入 FastAPI 路由，先经过 Pydantic Schema 做参数校验，然后进入 Service 层处理业务规则，比如用户名查重、密码校验，再通过 Repository 层访问 MySQL。数据库表结构由 SQLAlchemy Model 定义，应用启动时通过 `create_all()` 自动创建 `accounts` 表。

涉及的后端知识点可以这样串起来：

1. **项目分层**：我没有把所有逻辑写在路由函数里，而是拆成 API、Schema、Service、Repository、Model、Core。这样 API 层只负责 HTTP 输入输出，Service 层负责业务规则，Repository 层负责数据库访问，后续加 Redis 或改查询逻辑时不会互相污染。
2. **参数校验与响应控制**：注册和登录请求用 Pydantic 定义输入结构，例如用户名和密码长度限制；查询用户时返回 `AccountPublic`，只暴露 `id`、`username`、`avatar_url`、`bio`，避免把 `password_hash`、`token` 这类敏感字段返回给前端。
3. **密码安全**：注册时不会明文存密码，而是用 bcrypt 生成哈希后写入数据库。登录时也不是解密密码，而是用 bcrypt 校验用户输入和数据库哈希是否匹配。这样即使数据库泄露，也不会直接暴露用户原始密码。
4. **数据库接入**：后端使用 SQLAlchemy async + asyncmy 连接 Docker 中的 MySQL。这里还踩到一个真实问题：SQLAlchemy 可以创建表，但不会自动创建 database，所以手动启动 MySQL 容器时，需要先创建 `feedsystem` 数据库。
5. **登录态雏形**：Day 1 先用随机 token 跑通登录链路，并把 token 存到 `accounts.token`。这么做是为了给 Day 2 的 JWT 双 Token、登出主动失效、Redis token 缓存打基础。

一句话总结：

> Day 1 我跑通的是“HTTP 请求 -> 参数校验 -> 业务规则 -> 数据库访问 -> JSON 响应”的后端最小闭环，并且在这个过程中落地了分层设计、密码哈希、响应脱敏和 MySQL 接入这些基础后端能力。

可能追问：为什么这里很多函数都用 `async def`，而不是普通 `def`？

可以这样回答：

> 因为这个项目的主要耗时点不是 CPU 计算，而是网络 I/O，比如连接 MySQL、后续连接 Redis、调用消息队列等。FastAPI 基于 ASGI，天然支持异步请求处理；SQLAlchemy async + asyncmy 也是异步数据库驱动。用 `async def` 后，当一个请求在等待 MySQL 返回结果时，事件循环可以切去处理其他请求，而不是让线程一直阻塞在那里。这样在 I/O 密集型后端服务里，可以用较少的线程承载更多并发连接。

还可以补充取舍：

> 当然，并不是所有函数都必须异步。像 `hash_password` 这种纯 CPU 本地计算函数，用普通 `def` 就可以；而路由函数、Service、Repository 这些链路里会 `await` 数据库或外部服务，所以定义成 `async def`。我的原则是：涉及数据库、Redis、HTTP、MQ 这类 I/O 的链路用异步；纯计算和简单工具函数保持同步，这样代码既符合 FastAPI 的并发模型，也不会为了异步而异步。

更严谨的补充：`bcrypt` 这种密码哈希虽然是本地计算，但它不是“很轻的普通计算”，而是故意设计得比较慢，用来提高暴力破解成本。如果登录/注册并发比较高，在 `async def` 路由链路里直接调用同步的 `bcrypt` 可能短暂阻塞事件循环。生产里可以把它丢到线程池，例如用 FastAPI/Starlette 的 `run_in_threadpool` 或 AnyIO 的 `to_thread.run_sync` 包一层。

可以这样表达：

> 密码哈希函数本身我会保持同步函数，因为它不是 I/O 操作。但在异步 Web 链路中调用 bcrypt 时，如果并发较高，可以用线程池 offload，避免阻塞事件循环。一般不会为了每次登录校验单独上进程池，因为进程池开销更大、数据序列化成本更高，Web 服务通常更常见的做法是：轻量阻塞任务放线程池，CPU 很重的任务交给独立 Worker 或任务队列。

如果面试官继续追问 asyncio 和多线程的区别：

> 多线程是让操作系统调度多个线程，线程在阻塞 I/O 时会占用线程资源；asyncio 是协作式并发，遇到 `await` 主动把控制权交回事件循环。对于大量等待数据库或网络响应的场景，asyncio 的资源开销更低。但如果是 CPU 密集型任务，比如视频转码、复杂推荐计算，单纯 async 并不能提升性能，应该交给进程池、任务队列或独立 Worker。

### Day 2：JWT 鉴权、Redis token 缓存与视频模块

面试官如果问“你第二阶段做了什么”，可以这样讲：

> 第二阶段我把登录态从临时 token 升级成了 access token + refresh token。access token 使用 JWT，里面包含用户 ID、用户名、签发时间和过期时间，主要用于访问接口；refresh token 是服务端生成并保存的随机字符串，用于换取新的 access token。为了支持主动登出，我没有做纯无状态 JWT，而是把当前有效 access token 存在 MySQL，并用 Redis 做缓存。鉴权时先验证 JWT 签名和过期时间，再查 Redis；Redis miss 或 Redis 不可用时回源 MySQL，校验通过后再回填 Redis。

这段可以串起来讲的后端知识点：

1. **JWT 的作用**：JWT 不是用来加密用户信息，而是用签名保证 token 没被篡改。后端可以从 payload 中拿到用户 ID，但仍要注意过期时间和服务端失效策略。
2. **为什么要 refresh token**：access token 应该短期有效，降低泄露风险；refresh token 生命周期更长，用来续签 access token，避免用户频繁登录。
3. **为什么 JWT 还要存服务端**：纯 JWT 在过期前难以主动失效。把当前 token 存 MySQL 后，登出时清空 token，就能让旧 token 立刻失效。
4. **Redis 的定位**：Redis 缓存当前有效 token，减少每次鉴权都查 MySQL。Redis 挂了不会影响正确性，只是性能下降，因为 MySQL 才是数据真相。
5. **FastAPI Depends 鉴权**：用 `get_current_user` 做硬鉴权，没有 token 直接拒绝；用 `get_optional_user` 做软鉴权，不带 token 可以访问，带了坏 token 则返回 401。
6. **视频发布链路**：发布视频必须先通过硬鉴权拿到当前用户，再把 `current_user.id` 写成 `author_id`，把标题、播放地址、封面地址写入 `videos` 表。

可能追问：为什么 Redis token key 设计成 `v1:account:{id}`？

可以这样回答：

> 这个 key 表示“某个账号当前有效的 access token”。`v1` 是版本前缀，后续如果 token 结构或缓存策略改变，可以平滑迁移；`account:{id}` 用账号 ID 定位当前登录态。它不是保存所有历史 token，而是只保存当前有效 token，所以用户刷新或重新登录后，旧 token 会自然失效。

可能追问：为什么 Redis 只存 access token，不存 refresh token？

可以这样回答：

> refresh token 的安全级别更高，生命周期更长，我更希望它以 MySQL 为准。Redis 主要优化高频鉴权，也就是 access token 校验。刷新 token 的频率远低于普通接口访问，所以直接查 MySQL 更简单，也更容易保证一致性。

可能追问：视频详情为什么是软鉴权？

可以这样回答：

> 视频详情和 Feed 这种接口通常允许游客访问，但登录用户后续可以看到更多个性化状态，比如是否点赞、是否关注作者。所以我先用软鉴权预留这个能力：不带 token 正常返回公共详情，带了错误 token 则说明前端登录态异常，需要返回 401。

### Day 2.5：前后端联调与 Token 在浏览器中的流转

面试官如果问“你怎么证明这些后端接口不是只在 Swagger 里能跑”，可以这样讲：

> 我参考 Go 版本前端做了一个轻量的 Vue/Vite 联调工作台，把 Day1-2 已经完成的接口串起来。前端通过 Vite 的 `/api` 代理访问本地 FastAPI，避免跨域问题。登录成功后，前端把 access token 和 refresh token 存到 localStorage，后续请求统一由 API client 加上 `Authorization: Bearer <token>`。如果接口返回 401，client 会尝试用 refresh token 调 `/account/refresh` 换新 access token，然后重试原请求。

这段可以串起来讲的后端知识点：

1. **前后端分离联调**：前端运行在 `127.0.0.1:5173`，后端运行在 `127.0.0.1:8000`，通过 Vite proxy 把 `/api` 转发到后端。
2. **浏览器中的登录态**：前端保存 token 后，每个需要登录的请求都在请求头里带 `Authorization`，后端通过 `get_current_user` 解析和校验。
3. **刷新 token 的位置**：刷新逻辑放在 API client，不散落在每个页面按钮里。这样页面只关心业务操作，登录态续签由统一请求层处理。
4. **联调验证链路**：浏览器/前端请求 -> Vite proxy -> FastAPI router -> Service -> Repository -> MySQL/Redis -> JSON 响应 -> 前端页面更新。

可能追问：为什么当前前端不直接请求 `http://127.0.0.1:8000`？

可以这样回答：

> 因为浏览器会遇到跨域限制。开发环境里用 Vite proxy 是很常见的做法，前端代码只请求同源的 `/api`，由开发服务器转发到后端。这样既贴近真实前后端分离开发，也避免我们现在为了联调先引入 CORS 配置干扰学习重点。

### Day 3：点赞、评论、事务与游标分页

面试官如果问“点赞模块你是怎么设计的”，可以这样讲：

> 点赞不是简单地把视频表的点赞数字段加一。我设计了 `likes` 关系表保存用户和视频的点赞关系，并给 `(video_id, account_id)` 加联合唯一约束，从数据库层保证同一用户不能重复点赞同一视频。同时在 `videos.likes_count` 里冗余点赞数，用于 Feed 列表展示和点赞榜排序。点赞接口会在同一个数据库事务里插入 `likes` 记录并更新 `videos.likes_count`，任何一步失败都会回滚，避免关系表和计数字段不一致。

这段可以串起来讲的后端知识点：

1. **关系表与冗余计数**：`likes` 表保证“谁点过赞”的正确性，`videos.likes_count` 优化列表读取和排序。
2. **唯一索引**：业务层先查是否已点赞，数据库层再用联合唯一索引兜底，防止并发重复插入。
3. **事务一致性**：点赞关系插入和计数更新必须一起提交，取消点赞也要删除关系并减少计数。
4. **防负数**：取消点赞时用 `GREATEST(likes_count - 1, 0)` 防止计数异常变成负数。
5. **软鉴权 Feed**：Feed 不登录也能看，登录后批量查询当前用户点赞过的视频 ID，补充 `is_liked`。
6. **游标分页**：最新 Feed 用 `create_time` 游标；点赞榜用 `likes_count + id` 复合游标。

可能追问：为什么不每次动态 `count(likes)`？

可以这样回答：

> 动态 count 在单个视频详情页还可以接受，但 Feed 一页会有多条视频，点赞榜还要按点赞数排序。如果每次都从 `likes` 表聚合，查询成本会很高。所以我用 `likes` 表保存关系，用 `videos.likes_count` 做读优化，写入时通过事务维护两边一致。

可能追问：为什么点赞榜不用 offset 分页？

可以这样回答：

> offset 在深分页时性能会变差，而且 Feed 数据会不断变化，容易出现重复或漏数据。点赞榜使用 `likes_count DESC, id DESC` 排序，下一页带上上一页最后一条的 `likes_count` 和 `id`，条件是 `likes_count < cursor_likes OR (likes_count = cursor_likes AND id < cursor_id)`，这样即使很多视频点赞数相同，也能稳定向后翻页。

### Day 4：关注、标签与 Redis 缓存

面试官如果问“关注和标签模块你是怎么设计的”，可以这样讲：

> Day 4 我补了关系型业务和缓存层。关注关系用 `socials(follower_id, vlogger_id)` 表示多对多，并用联合唯一约束防止重复关注。标签用 `tags` 和 `video_tags` 建模，因为视频和标签也是多对多；发布视频时从标题和描述里提取 `#tag`，在同一个数据库事务里写入视频和标签关系。Feed 部分新增了关注流和标签流，本质上都是在视频查询前增加关系过滤。

这段可以串起来讲的后端知识点：

1. **多对多关系建模**：关注是用户和作者的多对多，标签是视频和标签的多对多，所以都需要关系表。
2. **唯一约束兜底**：`socials(follower_id, vlogger_id)` 和 `tags.name` 都用唯一约束保证数据不会重复。
3. **发布链路扩展**：发布视频不只写 `videos`，还会提取 `#tag` 并写入 `tags/video_tags`，让标签流立即可查。
4. **关注流查询**：先从 `socials` 查当前用户关注的作者，再查询这些作者发布的视频。
5. **标签流查询**：通过 `videos JOIN video_tags JOIN tags` 查指定标签下的视频。
6. **Redis Cache-Aside**：视频详情先读 Redis，miss 查 MySQL，再回填 Redis。
7. **写后删缓存**：点赞、取消点赞、评论变化会影响详情，所以写 DB 后删除详情缓存。
8. **短 TTL Feed 缓存**：最新 Feed 变化快，所以只做 5 秒短缓存。

可能追问：Redis 挂了为什么数据不会丢？

可以这样回答：

> 因为项目里 MySQL 才保存业务事实，比如账号、视频、点赞、评论、关注和标签；Redis 只保存能从 MySQL 重新查出来的缓存。Redis 挂了以后，缓存读写函数会失败返回，业务继续查 MySQL，所以正确性不受影响，只是性能下降。

可能追问：为什么写操作后删除缓存，而不是更新缓存？

可以这样回答：

> 更新缓存需要重新组装完整响应，容易漏字段；并发写时也可能出现旧数据覆盖新数据。删除缓存更简单可靠：下一次读请求发现 miss，就从 MySQL 读最新数据并回填。这就是 Cache-Aside 里常见的写策略。

可能追问：为什么最新 Feed 缓存 key 里要带 `viewer_id`？

可以这样回答：

> 因为 Feed 响应里有 `is_liked`，它和当前用户有关。同一条视频，A 用户可能点过赞，B 用户没有点过赞。如果 Feed 缓存不区分用户，就可能把 A 的点赞状态返回给 B。所以游客用 `viewer=0`，登录用户用自己的账号 ID。
