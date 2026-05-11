# feedSystem_video_python 执行过程记录

> 这个文件用于记录 Python 重构项目的真实推进过程。后续每次继续学习/开发前，先读 `plan.md` 和本文件，就能知道我们走到哪里、做过什么、下一步该做什么。

## 当前状态

- 当前阶段：Day 2.5 - Day1-2 前端联调工作台
- 当前日期：2026-05-11
- 当前目标：用前端页面联调 Day1-2 已有后端接口
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
