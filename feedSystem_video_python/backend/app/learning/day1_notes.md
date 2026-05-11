# Day 1 学习笔记：项目骨架、数据库、注册登录

## 1. 今天真正要学什么

Day 1 不是为了写很多接口，而是建立一个后端项目最小闭环：

```text
浏览器/Swagger 发请求
  -> FastAPI 路由接收
  -> Pydantic 校验输入
  -> Service 执行业务规则
  -> Repository 访问数据库
  -> SQLAlchemy 写入或查询 MySQL
  -> FastAPI 返回 JSON
```

这条链路跑通后，后面的视频、点赞、评论、Feed 都是在它上面继续扩展。

## 2. 为什么要分层

如果把所有逻辑都写在路由函数里，一开始会很快，但后面会变成：

- 路由里既有 HTTP 状态码，又有密码哈希。
- 路由里既有业务判断，又有 SQL 查询。
- 想改数据库查询时，可能影响接口返回。
- 想复用注册逻辑时，只能复制粘贴。

所以我们按职责拆开：

| 层 | 文件位置 | 负责什么 | 不负责什么 |
|---|---|---|---|
| API 层 | `app/api/account.py` | 接收请求、返回响应、决定 HTTP 状态码 | 不直接写 SQL，不做密码哈希细节 |
| Schema 层 | `app/schemas/account.py` | 定义输入输出结构，校验字段长度 | 不访问数据库 |
| Service 层 | `app/services/account_service.py` | 业务规则：用户名不能重复、密码要校验 | 不关心 HTTP 状态码 |
| Repository 层 | `app/repositories/account_repo.py` | 数据库查询和写入 | 不判断业务对错 |
| Model 层 | `app/models/account.py` | 数据库表结构 | 不处理请求 |
| Core 层 | `app/core/security.py` | 密码哈希等通用能力 | 不知道账号接口存在 |

面试表达：

> 我把项目拆成 API、Service、Repository、Model、Schema 几层。API 只处理 HTTP，Service 处理业务规则，Repository 封装数据库访问。这样后续加 Redis、换数据库查询或复用业务逻辑时，不需要把路由函数改得很乱。

## 3. 启动链路：应用是怎么跑起来的

入口文件：

```text
app/main.py
```

函数链路：

```text
uvicorn app.main:app
  -> 导入 `app/main.py`
  -> 创建 FastAPI app
  -> include_router(account_router)
  -> 应用启动时进入 lifespan
  -> init_models()
  -> Base.metadata.create_all()
  -> MySQL 中创建 accounts 表
```

输入从哪里来：

- 命令行输入：`uvicorn app.main:app --reload --host 127.0.0.1 --port 8000`
- 配置输入：`DATABASE_URL`，默认是 `mysql+asyncmy://root:123456@127.0.0.1:3306/feedsystem`

输出到哪里：

- FastAPI 服务监听 `127.0.0.1:8000`
- MySQL 中出现 `accounts` 表
- 浏览器可以打开 `http://127.0.0.1:8000/docs`

关键文件：

- `app/main.py`
- `app/database.py`
- `app/config.py`
- `app/models/account.py`

## 4. 注册功能链路

接口：

```text
POST /account/register
```

输入从哪里来：

Swagger 或前端发送 JSON：

```json
{
  "username": "alice",
  "password": "123456"
}
```

完整函数链路：

```text
register(req, db)
  -> RegisterRequest 校验 username/password 长度
  -> AccountService.register(username, password)
     -> username.strip()
     -> AccountRepository.find_by_username(username)
        -> SELECT * FROM accounts WHERE username = ?
     -> 如果用户已存在，抛 UsernameAlreadyExistsError
     -> hash_password(password)
        -> bcrypt.hashpw(...)
     -> AccountRepository.create(username, password_hash)
        -> INSERT INTO accounts (...)
        -> flush + refresh，拿到数据库生成的 id
  -> db.commit()
  -> 返回 {"message": "account created"}
```

数据怎么流：

```text
明文 password
  -> Service
  -> hash_password
  -> password_hash
  -> Repository
  -> MySQL accounts.password_hash
```

输出去哪：

- 成功：HTTP 200，返回 `{"message": "account created"}`
- 用户名重复：HTTP 409，返回错误信息
- 数据库中新增一行账号记录

为什么这样写：

- 查重放在 Service，因为“用户名不能重复”是业务规则。
- 插入放在 Repository，因为“怎么写数据库”是数据访问细节。
- 哈希放在 Core，因为密码哈希以后登录、改密也要复用。
- `db.commit()` 放在 API 层，是 Day 1 的简单做法；后续复杂事务会进一步收口。

## 5. 登录功能链路

接口：

```text
POST /account/login
```

输入从哪里来：

Swagger 或前端发送 JSON：

```json
{
  "username": "alice",
  "password": "123456"
}
```

完整函数链路：

```text
login(req, db)
  -> LoginRequest 校验 username/password 长度
  -> AccountService.login(username, password)
     -> AccountRepository.find_by_username(username)
        -> SELECT * FROM accounts WHERE username = ?
     -> 如果用户不存在，抛 InvalidCredentialsError
     -> verify_password(password, account.password_hash)
        -> bcrypt.checkpw(...)
     -> 如果密码不匹配，抛 InvalidCredentialsError
     -> 生成 Day 1 临时 token
     -> AccountRepository.save_login_token(account, token)
        -> UPDATE accounts SET token = ?
  -> db.commit()
  -> 返回 LoginResponse
```

数据怎么流：

```text
用户输入 password
  -> verify_password(password, 数据库里的 password_hash)
  -> 得到 True/False
  -> True 时生成 token
  -> token 写回 accounts.token
  -> token 返回给客户端
```

输出去哪：

成功时返回：

```json
{
  "token": "day1_xxx",
  "account_id": 1,
  "username": "alice"
}
```

客户端后续会保存 token。Day 2 我们会把它换成真正的 JWT。

失败时：

- 用户不存在：HTTP 401
- 密码错误：HTTP 401

为什么用户不存在和密码错误都返回 401：

- 不告诉攻击者到底是用户名错了还是密码错了。
- 这是登录接口常见的安全处理方式。

## 6. 按 ID 查询用户链路

接口：

```text
POST /account/findByID
```

输入：

```json
{
  "id": 1
}
```

函数链路：

```text
find_by_id(req, service)
  -> FindByIDRequest 校验 id > 0
  -> AccountService.find_by_id(id)
     -> AccountRepository.find_by_id(id)
        -> db.get(Account, id)
  -> 如果没有账号，返回 404
  -> AccountPublic.model_validate(account)
  -> 返回公开字段
```

输出：

```json
{
  "id": 1,
  "username": "alice",
  "avatar_url": "",
  "bio": ""
}
```

为什么不用直接返回数据库模型：

- 数据库模型里有 `password_hash`、`token`、`refresh_token`。
- 这些字段不能暴露给前端。
- 所以响应使用 `AccountPublic`，只输出安全字段。

## 7. 按用户名查询用户链路

接口：

```text
POST /account/findByUsername
```

输入：

```json
{
  "username": "alice"
}
```

函数链路：

```text
find_by_username(req, service)
  -> FindByUsernameRequest 校验 username 长度
  -> AccountService.find_by_username(username)
     -> username.strip()
     -> AccountRepository.find_by_username(username)
        -> select(Account).where(Account.username == username)
        -> db.execute(stmt)
        -> result.scalar_one_or_none()
  -> 如果没有账号，返回 404
  -> 返回 AccountPublic
```

这段为什么重要：

- 后面登录、关注、评论 @ 用户都会反复用到“按用户名查账号”。
- 这是 Repository 层最典型的查询方法。
- 所以它被放进 `day1_practice.py` 让你亲手敲一遍。

## 8. 为什么 Day 1 token 还不是 JWT

Day 1 的重点是跑通注册登录和分层，所以先返回一个随机字符串 token，并写入 `accounts.token`。

Day 2 会把它替换成：

- Access Token：JWT，短有效期。
- Refresh Token：随机字符串，长有效期。
- 主动失效：登出时清空数据库 token。

现在先保留 `token` 字段，是为了让后面的主动失效、登出、Redis token 缓存自然接上。

## 9. 你要亲手敲的重点

练习文件：

```text
app/learning/day1_practice.py
```

练习内容：

```python
hash_password(password: str) -> str
verify_password(password: str, hashed_password: str) -> bool
find_by_username_example(db, Account, username: str)
```

敲这三段不是为了记语法，而是为了理解：

- 密码为什么入库前要变成哈希。
- bcrypt 为什么校验而不是解密。
- Repository 为什么只写查询，不处理 HTTP 和业务错误。

## 10. 验收步骤

启动依赖：

```bash
# 如果你已经有 YYmysql / YYredis 在运行，可以跳过这一步。
docker compose up -d mysql redis
```

如果你是手动运行的 `YYmysql` 容器，并且启动时没有设置 `MYSQL_DATABASE=feedsystem`，需要先创建数据库：

```bash
docker exec -it YYmysql mysql -uroot -p123456 -e "CREATE DATABASE IF NOT EXISTS feedsystem CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;"
```

为什么需要这一步：

```text
SQLAlchemy 的 create_all()
  -> 只会在已有数据库里创建表
  -> 不会自动创建 database 本身
```

所以 `accounts` 表可以由后端自动创建，但 `feedsystem` 这个数据库要先存在。

启动后端：

```bash
cd backend
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

打开：

```text
http://127.0.0.1:8000/docs
```

依次测试：

1. `GET /health`
2. `POST /account/register`
3. `POST /account/login`
4. `POST /account/findByUsername`
5. `POST /account/findByID`

## 11. 今天的面试说法

可以这样讲：

> 我第一步先搭了 FastAPI 后端骨架，并按 API、Service、Repository、Model、Schema 分层。注册接口的数据从请求体进入 Pydantic 模型，经过 Service 做用户名查重和密码哈希，再通过 Repository 写入 MySQL。登录接口会先按用户名查账号，再用 bcrypt 校验密码，成功后生成临时 token 写回数据库。这里我没有直接返回数据库模型，而是用响应 Schema 控制输出字段，避免把密码哈希和 token 暴露给前端。
