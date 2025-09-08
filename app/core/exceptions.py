"""
自定义异常类
"""
from fastapi import HTTPException, status


class AuthError(HTTPException):
    """认证错误"""
    def __init__(self, detail: str = "认证失败"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class PermissionError(HTTPException):
    """权限错误"""
    def __init__(self, detail: str = "权限不足"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class ValidationError(HTTPException):
    """验证错误"""
    def __init__(self, detail: str = "数据验证失败"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )


class NotFoundError(HTTPException):
    """资源未找到错误"""
    def __init__(self, detail: str = "资源未找到"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
        )


class ConflictError(HTTPException):
    """冲突错误"""
    def __init__(self, detail: str = "资源冲突"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )


class RateLimitError(HTTPException):
    """限流错误"""
    def __init__(self, detail: str = "请求过于频繁"):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
        )


class OTPError(HTTPException):
    """验证码错误"""
    def __init__(self, detail: str = "验证码错误"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )


class UserPoolError(HTTPException):
    """用户池错误"""
    def __init__(self, detail: str = "用户池操作错误"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
        )
