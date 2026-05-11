# feedSystem Video Python 前端

当前前端是 Day1-2 的联调工作台，目标不是做完整产品页面，而是把已经完成的后端能力从浏览器里跑通：

- 注册账号
- 登录并保存 access token / refresh token
- 自动携带 `Authorization: Bearer <token>`
- 手动刷新 token
- 登出并让后端 token 主动失效
- 查询当前用户和公开用户信息
- 发布视频元数据
- 按作者 ID 查询视频列表
- 查询视频详情

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

## 目前刻意不做的内容

- 文件上传：当前视频发布只填写 `play_url` 和 `cover_url`。
- Feed 流页面：等 Day3-4 后端 Feed 接口完成后再接。
- 点赞、评论、关注：等对应后端模块完成后再补到页面。
