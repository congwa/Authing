"""
API依赖项
"""
from typing import Generator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db_session
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.services.rbac_service import RBACService


async def get_db() -> Generator[AsyncSession, None, None]:
    """获取数据库会话"""
    async for session in get_db_session():
        yield session


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """获取认证服务"""
    return AuthService(db)


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    """获取用户服务"""
    return UserService(db)


async def get_rbac_service(db: AsyncSession = Depends(get_db)) -> RBACService:
    """获取RBAC服务"""
    return RBACService(db)
