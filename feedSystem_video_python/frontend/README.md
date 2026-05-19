# feedSystem Video Python 前端

当前前端已经参考 Go 版本前端，从纯联调工作台调整成“正常业务主页面 + 侧边栏接口日志”的形态。目标是既能像真实页面一样浏览 Feed、看详情、点赞评论，又保留学习阶段需要的请求/响应日志。

主页面结构：

```text
左侧导航      推荐 / 点赞榜 / 健康检查
中间主区域    Feed 列表 + 视频详情 + 发布与评论
右侧日志      最近接口请求和响应
```

响应式策略：

- 宽屏时日志固定在右侧。
- 中等宽度时日志移到主页面下方，避免主功能区被挤压。
- 窄屏时左侧导航、Feed、详情都会改成单列布局。

- 注册账号
- 登录并保存 access token / refresh token
- 自动携带 `Authorization: Bearer <token>`
- 手动刷新 token
- 登出并让后端 token 主动失效
- 查询当前用户和公开用户信息
- 发布视频元数据
- 按作者 ID 查询视频列表
- 查询视频详情
- 浏览最新 Feed
- 浏览点赞榜 Feed
- 点赞 / 取消点赞
- 评论发布 / 评论列表

## 运行方式

先确保后端已经启动：

```bash
cd E:\feedSystem_video\feedSystem_video_python\backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

再启动前端：

```bash
cd E:\feedSystem_video\feedSystem_video_python\frontend
npm install
npm run dev
```

浏览器打开：

```text
http://127.0.0.1:5173
```

## 联调原理

前端请求统一走 `/api`：

```text
浏览器 http://127.0.0.1:5173/api/account/login
  -> Vite dev server proxy
  -> FastAPI http://127.0.0.1:8000/account/login
```

这样前端和后端都在本地跑，不需要额外处理浏览器跨域问题。

## 视频和封面占位策略

当前后端只保存视频元数据，还没有做文件上传、对象存储或真实静态资源服务。

所以前端现在采用稳定色块占位：

- 封面区域根据视频 ID 生成固定颜色。
- 视频播放区域也用色块和视频 ID 展示。
- `play_url` 和 `cover_url` 字段仍然会正常入库，默认使用 `debug://...` 这类占位值。

后续如果你收集了图片 URL，或者我们实现了上传接口，只需要把真实 URL 写入 `cover_url` / `play_url`，页面展示逻辑再切换成真实媒体即可。

## 目前刻意不做的内容

- 文件上传：当前视频发布只填写 `play_url` 和 `cover_url`。
- 文件上传：当前视频发布只填写 `play_url` 和 `cover_url`。
- 关注：等对应后端模块完成后再补到页面。
