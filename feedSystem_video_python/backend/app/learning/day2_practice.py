"""
Day 2 亲手敲练习：JWT、Redis token 缓存与鉴权依赖。

练习方式：
1. 先阅读 app/core/auth.py 和 app/core/redis.py。
2. 再对照下面的提示，把关键函数自己敲一遍。
3. 重点不是背代码，而是能讲清“输入从哪里来，输出去哪里”。
"""


def practice_create_access_token() -> None:
    """练习 1：对照 create_access_token，理解 JWT payload 为什么需要 sub、iat、exp。"""
    # 你可以自己敲一遍：
    # now = datetime.now(UTC)
    # payload = {
    #     "sub": str(account_id),
    #     "username": username,
    #     "iat": now,
    #     "exp": now + timedelta(minutes=settings.access_token_minutes),
    # }
    # return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def practice_parse_access_token() -> None:
    """练习 2：对照 parse_access_token，理解为什么要捕获签名错误、过期和字段缺失。"""
    # 你可以自己敲一遍：
    # payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    # account_id = int(payload["sub"])
    # username = str(payload["username"])
    # return TokenPayload(account_id=account_id, username=username)


async def practice_get_current_user_flow() -> None:
    """练习 3：对照 _resolve_user_from_token，理解 Redis miss 后为什么要回源 MySQL。"""
    # 你可以自己画一遍流程：
    # 1. parse_access_token(token)
    # 2. get_cached_access_token(account_id)
    # 3. 命中且一致：返回 CurrentUser
    # 4. 未命中：repo.find_by_id(account_id)
    # 5. MySQL token 一致：cache_access_token(account_id, token)
    # 6. 返回 CurrentUser
