"""
用户管理API接口
"""
from typing import List
from fastapi import APIRouter, Depends, Request, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_user_service
from app.core.dependencies import get_current_user, require_permissions
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserListQuery,
    ChangePasswordRequest, UserPoolCreate, UserPoolUpdate, 
    UserPoolResponse, ApplicationCreate, ApplicationResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse, PaginationMeta
from app.services.user_service import UserService
from app.models import User
from app.models.user import UserStatus, UserPoolStatus
import structlog

logger = structlog.get_logger()

router = APIRouter()

# ==================== 用户池管理 ====================

@router.post("/pools", response_model=ResponseModel[UserPoolResponse])
async def create_user_pool(
    pool_data: UserPoolCreate,
    request: Request,
    current_user: User = Depends(require_permissions("pool:write")),
    user_service: UserService = Depends(get_user_service)
):
    """创建用户池"""
    try:
        user_pool = await user_service.create_user_pool(
            name=pool_data.name,
            description=pool_data.description,
            settings=pool_data.settings
        )
        
        logger.info(
            "用户池创建成功",
            user_pool_id=user_pool.id,
            name=pool_data.name,
            creator_id=current_user.id
        )
        
        return ResponseModel(data=UserPoolResponse.from_orm(user_pool), message="用户池创建成功")
        
    except Exception as e:
        logger.error("创建用户池失败", error=str(e))
        raise


@router.get("/pools", response_model=PaginatedResponse[UserPoolResponse])
async def list_user_pools(
    status: UserPoolStatus = Query(None, description="状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(require_permissions("pool:read")),
    user_service: UserService = Depends(get_user_service)
):
    """获取用户池列表"""
    try:
        user_pools, total = await user_service.list_user_pools(
            status=status,
            page=page,
            per_page=per_page
        )
        
        data = [UserPoolResponse.from_orm(pool) for pool in user_pools]
        meta = PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page
        )
        
        return PaginatedResponse(data=data, meta=meta)
        
    except Exception as e:
        logger.error("获取用户池列表失败", error=str(e))
        raise


@router.get("/pools/{pool_id}", response_model=ResponseModel[UserPoolResponse])
async def get_user_pool(
    pool_id: int = Path(..., description="用户池ID"),
    current_user: User = Depends(require_permissions("pool:read")),
    user_service: UserService = Depends(get_user_service)
):
    """获取用户池详情"""
    try:
        user_pool = await user_service.get_user_pool_by_id(pool_id)
        return ResponseModel(data=UserPoolResponse.from_orm(user_pool))
        
    except Exception as e:
        logger.error("获取用户池详情失败", error=str(e), pool_id=pool_id)
        raise


@router.put("/pools/{pool_id}", response_model=ResponseModel[UserPoolResponse])
async def update_user_pool(
    pool_id: int,
    pool_data: UserPoolUpdate,
    current_user: User = Depends(require_permissions("pool:write")),
    user_service: UserService = Depends(get_user_service)
):
    """更新用户池"""
    try:
        user_pool = await user_service.update_user_pool(
            user_pool_id=pool_id,
            name=pool_data.name,
            description=pool_data.description,
            settings=pool_data.settings,
            status=pool_data.status
        )
        
        return ResponseModel(data=UserPoolResponse.from_orm(user_pool), message="用户池更新成功")
        
    except Exception as e:
        logger.error("更新用户池失败", error=str(e), pool_id=pool_id)
        raise

# ==================== 应用管理 ====================

@router.post("/applications", response_model=ResponseModel[ApplicationResponse])
async def create_application(
    app_data: ApplicationCreate,
    current_user: User = Depends(require_permissions("app:write")),
    user_service: UserService = Depends(get_user_service)
):
    """创建应用"""
    try:
        application = await user_service.create_application(
            user_pool_id=app_data.user_pool_id,
            app_name=app_data.app_name,
            callback_urls=app_data.callback_urls,
            logout_urls=app_data.logout_urls,
            allowed_origins=app_data.allowed_origins,
            token_lifetime=app_data.token_lifetime,
            refresh_token_lifetime=app_data.refresh_token_lifetime
        )
        
        return ResponseModel(data=ApplicationResponse.from_orm(application), message="应用创建成功")
        
    except Exception as e:
        logger.error("创建应用失败", error=str(e))
        raise

# ==================== 用户管理 ====================

@router.post("/", response_model=ResponseModel[UserResponse])
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_permissions("user:write")),
    user_service: UserService = Depends(get_user_service)
):
    """创建用户"""
    try:
        user = await user_service.create_user(
            user_pool_id=user_data.user_pool_id,
            username=user_data.username,
            email=user_data.email,
            phone=user_data.phone,
            password=user_data.password,
            nickname=user_data.nickname,
            avatar_url=user_data.avatar_url,
            profile_data=user_data.profile_data
        )
        
        return ResponseModel(data=UserResponse.from_orm(user), message="用户创建成功")
        
    except Exception as e:
        logger.error("创建用户失败", error=str(e))
        raise


@router.get("/", response_model=PaginatedResponse[UserResponse])
async def list_users(
    user_pool_id: int = Query(..., description="用户池ID"),
    status: UserStatus = Query(None, description="用户状态筛选"),
    keyword: str = Query(None, description="关键词搜索"),
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(require_permissions("user:read")),
    user_service: UserService = Depends(get_user_service)
):
    """获取用户列表"""
    try:
        query_params = UserListQuery(
            user_pool_id=user_pool_id,
            status=status,
            keyword=keyword,
            page=page,
            per_page=per_page
        )
        
        users, total = await user_service.list_users(query_params)
        
        data = [UserResponse.from_orm(user) for user in users]
        meta = PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page
        )
        
        return PaginatedResponse(data=data, meta=meta)
        
    except Exception as e:
        logger.error("获取用户列表失败", error=str(e))
        raise


@router.get("/{user_id}", response_model=ResponseModel[UserResponse])
async def get_user(
    user_id: int = Path(..., description="用户ID"),
    current_user: User = Depends(require_permissions("user:read")),
    user_service: UserService = Depends(get_user_service)
):
    """获取用户详情"""
    try:
        user = await user_service.get_user_by_id(user_id)
        return ResponseModel(data=UserResponse.from_orm(user))
        
    except Exception as e:
        logger.error("获取用户详情失败", error=str(e), user_id=user_id)
        raise


@router.put("/{user_id}", response_model=ResponseModel[UserResponse])
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_permissions("user:write")),
    user_service: UserService = Depends(get_user_service)
):
    """更新用户"""
    try:
        user = await user_service.update_user(
            user_id=user_id,
            username=user_data.username,
            email=user_data.email,
            phone=user_data.phone,
            nickname=user_data.nickname,
            avatar_url=user_data.avatar_url,
            profile_data=user_data.profile_data,
            status=user_data.status
        )
        
        return ResponseModel(data=UserResponse.from_orm(user), message="用户更新成功")
        
    except Exception as e:
        logger.error("更新用户失败", error=str(e), user_id=user_id)
        raise


@router.delete("/{user_id}", response_model=ResponseModel[bool])
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_permissions("user:delete")),
    user_service: UserService = Depends(get_user_service)
):
    """删除用户"""
    try:
        result = await user_service.delete_user(user_id)
        return ResponseModel(data=result, message="用户删除成功")
        
    except Exception as e:
        logger.error("删除用户失败", error=str(e), user_id=user_id)
        raise


@router.post("/{user_id}/change-password", response_model=ResponseModel[bool])
async def change_password(
    user_id: int,
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """修改密码"""
    try:
        # 只能修改自己的密码，除非是管理员
        if user_id != current_user.id:
            # TODO: 检查管理员权限
            pass
        
        result = await user_service.change_password(
            user_id=user_id,
            old_password=password_data.old_password,
            new_password=password_data.new_password
        )
        
        return ResponseModel(data=result, message="密码修改成功")
        
    except Exception as e:
        logger.error("修改密码失败", error=str(e), user_id=user_id)
        raise


@router.post("/{user_id}/reset-password", response_model=ResponseModel[bool])
async def reset_password(
    user_id: int,
    new_password: str,
    current_user: User = Depends(require_permissions("user:write")),
    user_service: UserService = Depends(get_user_service)
):
    """重置密码（管理员操作）"""
    try:
        result = await user_service.reset_password(user_id, new_password)
        return ResponseModel(data=result, message="密码重置成功")
        
    except Exception as e:
        logger.error("重置密码失败", error=str(e), user_id=user_id)
        raise


@router.get("/me", response_model=ResponseModel[UserResponse])
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """获取当前用户信息"""
    return ResponseModel(data=UserResponse.from_orm(current_user))
