"""
依赖注入
"""
from typing import Optional, Generator
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db_session
from app.models import User, UserPool, Application
from app.core.security import jwt_utils
from app.core.exceptions import AuthError, PermissionError, RateLimitError
from app.core.security import rate_limiter


# HTTP Bearer token 验证
security = HTTPBearer()


async def get_db() -> Generator[AsyncSession, None, None]:
    """获取数据库会话依赖"""
    async for session in get_db_session():
        yield session


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """获取当前用户依赖"""
    token = credentials.credentials
    
    # 验证token
    payload = jwt_utils.verify_token(token)
    if payload is None:
        raise AuthError("无效的访问令牌")
    
    # 检查token类型
    if payload.get("type") != "access":
        raise AuthError("令牌类型错误")
    
    # 获取用户ID
    user_id = payload.get("sub")
    if user_id is None:
        raise AuthError("令牌格式错误")
    
    # 查询用户
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()
    
    if user is None:
        raise AuthError("用户不存在")
    
    if user.status != "active":
        raise AuthError("用户账户已被禁用")
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户依赖"""
    if current_user.status != "active":
        raise AuthError("用户账户已被禁用")
    return current_user


async def get_user_pool_by_id(
    user_pool_id: int,
    db: AsyncSession = Depends(get_db)
) -> UserPool:
    """根据ID获取用户池依赖"""
    result = await db.execute(select(UserPool).where(UserPool.id == user_pool_id))
    user_pool = result.scalar_one_or_none()
    
    if user_pool is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户池不存在"
        )
    
    if user_pool.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户池已被禁用"
        )
    
    return user_pool


async def get_application_by_id(
    app_id: str,
    db: AsyncSession = Depends(get_db)
) -> Application:
    """根据ID获取应用依赖"""
    result = await db.execute(select(Application).where(Application.app_id == app_id))
    application = result.scalar_one_or_none()
    
    if application is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="应用不存在"
        )
    
    if application.status != "active":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="应用已被禁用"
        )
    
    return application


def verify_user_pool_access(user: User, user_pool_id: int):
    """验证用户是否有访问指定用户池的权限"""
    if user.user_pool_id != user_pool_id:
        raise PermissionError("无权访问该用户池")


def rate_limit_check(
    request: Request,
    limit: int = 60,
    window: int = 60,
    key_prefix: str = "default"
):
    """限流检查依赖"""
    def _rate_limit_check():
        client_ip = request.client.host
        key = f"{key_prefix}:{client_ip}"
        
        if not rate_limiter.is_allowed(key, limit, window):
            raise RateLimitError("请求过于频繁，请稍后再试")
        
        return True
    
    return _rate_limit_check


def login_rate_limit(request: Request):
    """登录限流检查"""
    return rate_limit_check(request, limit=5, window=60, key_prefix="login")


def otp_rate_limit(request: Request):
    """验证码发送限流检查"""
    return rate_limit_check(request, limit=10, window=60, key_prefix="otp")


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """获取可选的当前用户（用于公开接口）"""
    if credentials is None:
        return None
    
    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


class PermissionChecker:
    """权限检查器"""
    
    def __init__(self, required_permissions: list[str]):
        self.required_permissions = required_permissions
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ) -> User:
        """检查用户权限"""
        # 这里可以实现具体的权限检查逻辑
        # 目前简化处理，后续可以根据RBAC系统扩展
        
        # 检查用户状态
        if current_user.status != "active":
            raise PermissionError("用户账户已被禁用")
        
        # TODO: 实现具体的权限检查逻辑
        # 可以查询用户的角色和权限，然后检查是否包含所需权限
        
        return current_user


def require_permissions(*permissions: str):
    """权限装饰器工厂"""
    return PermissionChecker(list(permissions))
