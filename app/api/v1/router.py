"""
API v1版本路由汇总
"""
from fastapi import APIRouter

from app.api.v1 import auth, users, rbac

api_router = APIRouter()

# 注册子路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户管理"])
api_router.include_router(rbac.router, prefix="/rbac", tags=["权限管理"])
