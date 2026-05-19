"""
Day 1 亲手敲练习。

这个文件不是为了让你“填空刷代码”，而是让你把最关键的三段逻辑在手上过一遍：

1. 密码入库前为什么要哈希。
2. 登录时为什么只校验哈希，不解密密码。
3. Repository 查询为什么只负责数据库，不掺业务判断。

建议做法：

1. 先读 `day1_notes.md` 的链路说明。
2. 再看真实代码：
   - `app/core/security.py`
   - `app/repositories/account_repo.py`
3. 然后回到本文件，照着思路亲手敲一遍。
4. 敲完后对比真实代码，重点看“为什么这样分层”，不是看自己有没有一字不差。
"""


def hash_password(password: str) -> str:
    """
    练习目标：把明文密码变成 bcrypt 哈希字符串。

    为什么要这样写：

    - 数据库不能保存明文密码。
    - bcrypt 需要 bytes，所以第一步要把字符串编码成 UTF-8。
    - bcrypt.gensalt() 会生成随机盐，让相同密码每次得到不同哈希。
    - 数据库存字符串更方便，所以最后要 decode 回字符串。
    """
    # 这一段练习对应真实的密码入库前处理逻辑。
    # 源码位置：`app/core/security.py` -> `hash_password(password: str) -> str`
    # 练习：对照上面的真实函数亲手敲一遍。
    raise NotImplementedError


def verify_password(password: str, hashed_password: str) -> bool:
    """
    练习目标：判断用户输入的明文密码是否匹配数据库里的哈希值。

    为什么要这样写：

    - 登录时不能“解密密码”，因为 bcrypt 哈希不可逆。
    - 正确做法是：把用户输入交给 bcrypt.checkpw，让它和已有哈希比较。
    - 返回值是布尔值，Service 层再根据 True/False 决定是否允许登录。
    """
    # 这一段练习对应真实的登录密码校验逻辑。
    # 源码位置：`app/core/security.py` -> `verify_password(password: str, hashed_password: str) -> bool`
    # 练习：对照上面的真实函数亲手敲一遍。
    raise NotImplementedError


async def find_by_username_example(db, Account, username: str):
    """
    练习目标：根据用户名查一条账号记录。

    为什么要这样写：

    - Repository 只关心“怎么查数据库”。
    - 它不判断密码是否正确，也不决定 HTTP 状态码。
    - `select(Account).where(...)` 表达的是 SQL 查询条件。
    - `scalar_one_or_none()` 表示：要么拿到一个账号对象，要么拿到 None。
    """
    # 这一段练习对应 Repository 中最典型的按条件查询一条记录。
    # 源码位置：`app/repositories/account_repo.py` -> `AccountRepository.find_by_username`
    # 练习：对照上面的真实方法亲手敲一遍。
    raise NotImplementedError
