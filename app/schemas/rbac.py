"""
RBAC权限管理数据模式
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class RoleCreate(BaseModel):
    """创建角色请求"""
    user_pool_id: int = Field(description="用户池ID")
    role_name: str = Field(description="角色名称")
    role_code: str = Field(description="角色代码")
    description: Optional[str] = Field(default=None, description="角色描述")


class RoleUpdate(BaseModel):
    """更新角色请求"""
    role_name: Optional[str] = Field(default=None, description="角色名称")
    description: Optional[str] = Field(default=None, description="角色描述")


class RoleResponse(BaseModel):
    """角色响应"""
    id: int = Field(description="角色ID")
    user_pool_id: int = Field(description="用户池ID")
    role_name: str = Field(description="角色名称")
    role_code: str = Field(description="角色代码")
    description: Optional[str] = Field(description="角色描述")
    is_system: bool = Field(description="是否系统角色")
    created_at: datetime = Field(description="创建时间")
    updated_at: Optional[datetime] = Field(description="更新时间")


class PermissionCreate(BaseModel):
    """创建权限请求"""
    user_pool_id: int = Field(description="用户池ID")
    permission_name: str = Field(description="权限名称")
    permission_code: str = Field(description="权限代码")
    resource: str = Field(description="资源标识")
    action: str = Field(description="操作类型")
    description: Optional[str] = Field(default=None, description="权限描述")


class PermissionUpdate(BaseModel):
    """更新权限请求"""
    permission_name: Optional[str] = Field(default=None, description="权限名称")
    description: Optional[str] = Field(default=None, description="权限描述")


class PermissionResponse(BaseModel):
    """权限响应"""
    id: int = Field(description="权限ID")
    user_pool_id: int = Field(description="用户池ID")
    permission_name: str = Field(description="权限名称")
    permission_code: str = Field(description="权限代码")
    resource: str = Field(description="资源标识")
    action: str = Field(description="操作类型")
    description: Optional[str] = Field(description="权限描述")
    created_at: datetime = Field(description="创建时间")


class AssignRoleRequest(BaseModel):
    """分配角色请求"""
    user_id: int = Field(description="用户ID")
    role_ids: List[int] = Field(description="角色ID列表")
    expires_at: Optional[datetime] = Field(default=None, description="过期时间")


class RevokeRoleRequest(BaseModel):
    """撤销角色请求"""
    user_id: int = Field(description="用户ID")
    role_ids: List[int] = Field(description="角色ID列表")


class UserRoleResponse(BaseModel):
    """用户角色响应"""
    user_id: int = Field(description="用户ID")
    role_id: int = Field(description="角色ID")
    role_name: str = Field(description="角色名称")
    role_code: str = Field(description="角色代码")
    granted_by: Optional[int] = Field(description="授权人ID")
    granted_at: datetime = Field(description="授权时间")
    expires_at: Optional[datetime] = Field(description="过期时间")


class RolePermissionRequest(BaseModel):
    """角色权限关联请求"""
    role_id: int = Field(description="角色ID")
    permission_ids: List[int] = Field(description="权限ID列表")


class UserPermissionResponse(BaseModel):
    """用户权限响应"""
    user_id: int = Field(description="用户ID")
    permissions: List[PermissionResponse] = Field(description="权限列表")
