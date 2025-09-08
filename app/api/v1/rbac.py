"""
RBAC权限管理API接口
"""
from typing import List
from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_rbac_service
from app.core.dependencies import get_current_user, require_permissions
from app.schemas.rbac import (
    RoleCreate, RoleUpdate, RoleResponse, PermissionCreate, 
    PermissionUpdate, PermissionResponse, AssignRoleRequest,
    RevokeRoleRequest, UserRoleResponse, RolePermissionRequest,
    UserPermissionResponse
)
from app.schemas.common import ResponseModel, PaginatedResponse, PaginationMeta
from app.services.rbac_service import RBACService
from app.models import User
import structlog

logger = structlog.get_logger()

router = APIRouter()

# ==================== 角色管理 ====================

@router.post("/roles", response_model=ResponseModel[RoleResponse])
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(require_permissions("role:write")),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """创建角色"""
    try:
        role = await rbac_service.create_role(
            user_pool_id=role_data.user_pool_id,
            role_name=role_data.role_name,
            role_code=role_data.role_code,
            description=role_data.description
        )
        
        logger.info(
            "角色创建成功",
            role_id=role.id,
            role_code=role_data.role_code,
            creator_id=current_user.id
        )
        
        return ResponseModel(data=RoleResponse.model_validate(role.model_dump()), message="角色创建成功")
        
    except Exception as e:
        logger.error("创建角色失败", error=str(e))
        raise


@router.get("/roles", response_model=ResponseModel[dict])
async def list_roles(
    user_pool_id: int = Query(..., description="用户池ID"),
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(require_permissions("role:read")),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """获取角色列表"""
    try:
        roles, total = await rbac_service.list_roles(
            user_pool_id=user_pool_id,
            page=page,
            per_page=per_page
        )
        
        role_data = [RoleResponse.model_validate(role.model_dump()) for role in roles]
        
        # 返回符合测试期望的格式
        response_data = {
            "items": role_data,
            "total": total
        }
        
        return ResponseModel(data=response_data)
        
    except Exception as e:
        logger.error("获取角色列表失败", error=str(e))
        raise


@router.get("/roles/{role_id}", response_model=ResponseModel[RoleResponse])
async def get_role(
    role_id: int = Path(..., description="角色ID"),
    current_user: User = Depends(require_permissions("role:read")),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """获取角色详情"""
    try:
        role = await rbac_service.get_role_by_id(role_id)
        return ResponseModel(data=RoleResponse.model_validate(role.model_dump()))
        
    except Exception as e:
        logger.error("获取角色详情失败", error=str(e), role_id=role_id)
        raise


@router.put("/roles/{role_id}", response_model=ResponseModel[RoleResponse])
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_user: User = Depends(require_permissions("role:write")),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """更新角色"""
    try:
        role = await rbac_service.update_role(
            role_id=role_id,
            role_name=role_data.role_name,
            description=role_data.description
        )
        
        return ResponseModel(data=RoleResponse.model_validate(role.model_dump()), message="角色更新成功")
        
    except Exception as e:
        logger.error("更新角色失败", error=str(e), role_id=role_id)
        raise


@router.delete("/roles/{role_id}", response_model=ResponseModel[bool])
async def delete_role(
    role_id: int,
    current_user: User = Depends(require_permissions("role:delete")),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """删除角色"""
    try:
        result = await rbac_service.delete_role(role_id)
        return ResponseModel(data=result, message="角色删除成功")
        
    except Exception as e:
        logger.error("删除角色失败", error=str(e), role_id=role_id)
        raise

# ==================== 权限管理 ====================

@router.post("/permissions", response_model=ResponseModel[PermissionResponse])
async def create_permission(
    permission_data: PermissionCreate,
    current_user: User = Depends(require_permissions("permission:write")),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """创建权限"""
    try:
        permission = await rbac_service.create_permission(
            user_pool_id=permission_data.user_pool_id,
            permission_name=permission_data.permission_name,
            permission_code=permission_data.permission_code,
            resource=permission_data.resource,
            action=permission_data.action,
            description=permission_data.description
        )
        
        return ResponseModel(data=PermissionResponse.model_validate(permission.model_dump()), message="权限创建成功")
        
    except Exception as e:
        logger.error("创建权限失败", error=str(e))
        raise


@router.get("/permissions", response_model=ResponseModel[dict])
async def list_permissions(
    user_pool_id: int = Query(..., description="用户池ID"),
    page: int = Query(1, ge=1, description="页码"),
    per_page: int = Query(20, ge=1, le=100, description="每页数量"),
    current_user: User = Depends(require_permissions("permission:read")),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """获取权限列表"""
    try:
        permissions, total = await rbac_service.list_permissions(
            user_pool_id=user_pool_id,
            page=page,
            per_page=per_page
        )
        
        permission_data = [PermissionResponse.model_validate(permission.model_dump()) for permission in permissions]
        
        # 返回符合测试期望的格式
        response_data = {
            "items": permission_data,
            "total": total
        }
        
        return ResponseModel(data=response_data)
        
    except Exception as e:
        logger.error("获取权限列表失败", error=str(e))
        raise


@router.get("/permissions/{permission_id}", response_model=ResponseModel[PermissionResponse])
async def get_permission(
    permission_id: int = Path(..., description="权限ID"),
    current_user: User = Depends(require_permissions("permission:read")),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """获取权限详情"""
    try:
        permission = await rbac_service.get_permission_by_id(permission_id)
        return ResponseModel(data=PermissionResponse.model_validate(permission.model_dump()))
        
    except Exception as e:
        logger.error("获取权限详情失败", error=str(e), permission_id=permission_id)
        raise


@router.put("/permissions/{permission_id}", response_model=ResponseModel[PermissionResponse])
async def update_permission(
    permission_id: int,
    permission_data: PermissionUpdate,
    current_user: User = Depends(require_permissions("permission:write")),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """更新权限"""
    try:
        permission = await rbac_service.update_permission(
            permission_id=permission_id,
            permission_name=permission_data.permission_name,
            description=permission_data.description
        )
        
        return ResponseModel(data=PermissionResponse.model_validate(permission.model_dump()), message="权限更新成功")
        
    except Exception as e:
        logger.error("更新权限失败", error=str(e), permission_id=permission_id)
        raise


@router.delete("/permissions/{permission_id}", response_model=ResponseModel[bool])
async def delete_permission(
    permission_id: int,
    current_user: User = Depends(require_permissions("permission:delete")),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """删除权限"""
    try:
        result = await rbac_service.delete_permission(permission_id)
        return ResponseModel(data=result, message="权限删除成功")
        
    except Exception as e:
        logger.error("删除权限失败", error=str(e), permission_id=permission_id)
        raise

# ==================== 角色权限关联 ====================

@router.post("/roles/{role_id}/permissions", response_model=ResponseModel[bool])
async def assign_permissions_to_role(
    role_id: int,
    permission_data: RolePermissionRequest,
    current_user: User = Depends(require_permissions("role:write")),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """为角色分配权限"""
    try:
        result = await rbac_service.assign_permissions_to_role(
            role_id=role_id,
            permission_ids=permission_data.permission_ids
        )
        
        return ResponseModel(data=result, message="权限分配成功")
        
    except Exception as e:
        logger.error("分配权限失败", error=str(e), role_id=role_id)
        raise


@router.get("/roles/{role_id}/permissions", response_model=ResponseModel[List[PermissionResponse]])
async def get_role_permissions(
    role_id: int = Path(..., description="角色ID"),
    current_user: User = Depends(require_permissions("role:read")),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """获取角色的权限列表"""
    try:
        permissions = await rbac_service.get_role_permissions(role_id)
        data = [PermissionResponse.model_validate(permission.model_dump()) for permission in permissions]
        
        return ResponseModel(data=data)
        
    except Exception as e:
        logger.error("获取角色权限失败", error=str(e), role_id=role_id)
        raise

# ==================== 用户角色管理 ====================

@router.post("/users/{user_id}/roles", response_model=ResponseModel[bool])
async def assign_roles_to_user(
    user_id: int,
    role_data: AssignRoleRequest,
    current_user: User = Depends(require_permissions("user:write")),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """为用户分配角色"""
    try:
        result = await rbac_service.assign_roles_to_user(
            user_id=user_id,
            role_ids=role_data.role_ids,
            granted_by=current_user.id,
            expires_at=role_data.expires_at
        )
        
        return ResponseModel(data=result, message="角色分配成功")
        
    except Exception as e:
        logger.error("分配角色失败", error=str(e), user_id=user_id)
        raise


@router.delete("/users/{user_id}/roles", response_model=ResponseModel[bool])
async def revoke_roles_from_user(
    user_id: int,
    role_data: RevokeRoleRequest,
    current_user: User = Depends(require_permissions("user:write")),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """撤销用户角色"""
    try:
        result = await rbac_service.revoke_roles_from_user(
            user_id=user_id,
            role_ids=role_data.role_ids
        )
        
        return ResponseModel(data=result, message="角色撤销成功")
        
    except Exception as e:
        logger.error("撤销角色失败", error=str(e), user_id=user_id)
        raise


@router.get("/users/{user_id}/roles", response_model=ResponseModel[List[UserRoleResponse]])
async def get_user_roles(
    user_id: int = Path(..., description="用户ID"),
    current_user: User = Depends(require_permissions("user:read")),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """获取用户的角色列表"""
    try:
        user_roles = await rbac_service.get_user_roles(user_id)
        data = [UserRoleResponse(**role_data) for role_data in user_roles]
        
        return ResponseModel(data=data)
        
    except Exception as e:
        logger.error("获取用户角色失败", error=str(e), user_id=user_id)
        raise


@router.get("/users/{user_id}/permissions", response_model=ResponseModel[UserPermissionResponse])
async def get_user_permissions(
    user_id: int = Path(..., description="用户ID"),
    current_user: User = Depends(require_permissions("user:read")),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """获取用户的所有权限"""
    try:
        permissions = await rbac_service.get_user_permissions(user_id)
        permission_responses = [PermissionResponse.model_validate(p.model_dump()) for p in permissions]
        
        data = UserPermissionResponse(
            user_id=user_id,
            permissions=permission_responses
        )
        
        return ResponseModel(data=data)
        
    except Exception as e:
        logger.error("获取用户权限失败", error=str(e), user_id=user_id)
        raise


@router.get("/check-permission", response_model=ResponseModel[bool])
async def check_user_permission(
    resource: str = Query(..., description="资源标识"),
    action: str = Query(..., description="操作类型"),
    current_user: User = Depends(get_current_user),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """检查当前用户是否有特定权限"""
    try:
        has_permission = await rbac_service.check_user_permission(
            user_id=current_user.id,
            resource=resource,
            action=action
        )
        
        return ResponseModel(data=has_permission)
        
    except Exception as e:
        logger.error("检查用户权限失败", error=str(e))
        raise

# ==================== 初始化 ====================

@router.post("/init-defaults", response_model=ResponseModel[bool])
async def init_default_roles_and_permissions(
    user_pool_id: int = Query(..., description="用户池ID"),
    current_user: User = Depends(require_permissions("admin")),
    rbac_service: RBACService = Depends(get_rbac_service)
):
    """初始化默认角色和权限"""
    try:
        result = await rbac_service.init_default_roles_and_permissions(user_pool_id)
        return ResponseModel(data=result, message="默认角色和权限初始化成功")
        
    except Exception as e:
        logger.error("初始化默认角色权限失败", error=str(e))
        raise
