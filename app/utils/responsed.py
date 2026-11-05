"""统一响应信封与业务异常体系。

路由层只负责把 ``AppError`` 转成 ``HTTPException``；
成功响应统一由 ``info()`` 包装为::

    {"msg": "成功", "code": 200, "data": ...}
"""

from typing import Any


class AppError(Exception):
    """业务异常基类：默认 500。"""

    status_code = 500

    def __init__(self, msg: str):
        self.msg = msg
        super().__init__(msg)


class BadRequest(AppError):
    status_code = 400


class Unauthorized(AppError):
    status_code = 401


class Forbidden(AppError):
    status_code = 403


class NotFound(AppError):
    status_code = 404


class Conflict(AppError):
    status_code = 409


class PayloadTooLarge(AppError):
    status_code = 413


class Unprocessable(AppError):
    status_code = 422


class Busy(AppError):
    status_code = 429


# 兼容参考项目的命名
PwdError = Unauthorized
OpError = Forbidden
Invalid = Unprocessable


def info(msg: str = "成功", code: int = 200, data: Any = None) -> dict:
    return {"msg": msg, "code": code, "data": data}