"""
RBAC权限管理数据模型
"""
from datetime import datetime
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship, Index, UniqueConstraint
from app.models.base import BaseModel, TimestampMixin


class Role(BaseModel, table=True):
    """角色表"""
    __tablename__ = "roles"
    
    user_pool_id: int = Field(foreign_key="user_pools.id")
    role_name: str = Field(max_length=100, description="角色名称")
    role_code: str = Field(max_length=100, description="角色代码")
    description: Optional[str] = Field(default=None, description="角色描述")
    is_system: bool = Field(default=False, description="是否系统角色")
    
    # 关系
    user_pool: "UserPool" = Relationship(back_populates="roles")
    user_roles: List["UserRole"] = Relationship(back_populates="role")
    role_permissions: List["RolePermission"] = Relationship(back_populates="role")
    
    __table_args__ = (
        UniqueConstraint("user_pool_id", "role_code", name="uq_pool_role_code"),
        Index("idx_roles_user_pool_id", "user_pool_id"),
        Index("idx_roles_role_code", "role_code"),
    )


class Permission(BaseModel, table=True):
    """权限表"""
    __tablename__ = "permissions"
    
    user_pool_id: int = Field(foreign_key="user_pools.id")
    permission_name: str = Field(max_length=100, description="权限名称")
    permission_code: str = Field(max_length=100, description="权限代码")
    resource: str = Field(max_length=100, description="资源标识")
    action: str = Field(max_length=50, description="操作类型(read/write/delete等)")
    description: Optional[str] = Field(default=None, description="权限描述")
    
    # 关系
    user_pool: "UserPool" = Relationship(back_populates="permissions")
    role_permissions: List["RolePermission"] = Relationship(back_populates="permission")
    
    __table_args__ = (
        UniqueConstraint("user_pool_id", "permission_code", name="uq_pool_permission_code"),
        Index("idx_permissions_user_pool_id", "user_pool_id"),
        Index("idx_permissions_resource_action", "resource", "action"),
    )


class UserRole(TimestampMixin, table=True):
    """用户角色关联表"""
    __tablename__ = "user_roles"
    
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    role_id: int = Field(foreign_key="roles.id", primary_key=True)
    granted_by: Optional[int] = Field(default=None, foreign_key="users.id", description="授权人ID")
    granted_at: datetime = Field(default_factory=lambda: datetime.now(UTC), description="授权时间")
    expires_at: Optional[datetime] = Field(default=None, description="权限过期时间")
    
    # 关系
    user: "User" = Relationship(
        back_populates="user_roles",
        sa_relationship_kwargs={"foreign_keys": "[UserRole.user_id]"}
    )
    role: Role = Relationship(back_populates="user_roles")
    granted_by_user: Optional["User"] = Relationship(
        back_populates="granted_roles",
        sa_relationship_kwargs={"foreign_keys": "[UserRole.granted_by]"}
    )
    
    __table_args__ = (
        Index("idx_user_roles_user_id", "user_id"),
        Index("idx_user_roles_role_id", "role_id"),
        Index("idx_user_roles_expires_at", "expires_at"),
    )


class RolePermission(SQLModel, table=True):
    """角色权限关联表"""
    __tablename__ = "role_permissions"
    
    role_id: int = Field(foreign_key="roles.id", primary_key=True)
    permission_id: int = Field(foreign_key="permissions.id", primary_key=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    # 关系
    role: Role = Relationship(back_populates="role_permissions")
    permission: Permission = Relationship(back_populates="role_permissions")
