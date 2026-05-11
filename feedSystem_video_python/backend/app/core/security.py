import bcrypt


def hash_password(password: str) -> str:
    """注册或改密时调用：把明文密码转换成可以安全入库的 bcrypt 哈希。"""
    password_bytes = password.encode("utf-8")
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt())
    return hashed.decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    """登录时调用：比较用户输入的明文密码和数据库里的 bcrypt 哈希是否匹配。"""
    password_bytes = password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    return bcrypt.checkpw(password_bytes, hashed_bytes)
