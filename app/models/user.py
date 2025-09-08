"""
用户相关数据模型
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from sqlmodel import SQLModel, Field, Relationship, JSON, Column
from sqlalchemy import UniqueConstraint, Index

from .base import BaseModel


class UserStatus(str, Enum):
    """用户状态枚举"""
    ACTIVE = "active"
    BLOCKED = "blocked"
    PENDING = "pending"


class UserPoolStatus(str, Enum):
    """用户池状态枚举"""
    ACTIVE = "active"
    DISABLED = "disabled"


class ApplicationType(str, Enum):
    """应用类型枚举"""
    WEB = "web"
    NATIVE = "native"
    SPA = "spa"


class UserPool(BaseModel, table=True):
    """用户池表"""
    __tablename__ = "user_pools"
    
    name: str = Field(max_length=100, description="用户池名称")
    description: Optional[str] = Field(default=None, description="用户池描述")
    settings: Optional[Dict[str, Any]] = Field(
        default_factory=dict, 
        sa_column=Column(JSON),
        description="用户池配置信息"
    )
    status: UserPoolStatus = Field(default=UserPoolStatus.ACTIVE)
    
    # 关系
    applications: List["Application"] = Relationship(back_populates="user_pool")
    users: List["User"] = Relationship(back_populates="user_pool")
    roles: List["Role"] = Relationship(back_populates="user_pool")
    permissions: List["Permission"] = Relationship(back_populates="user_pool")
    qr_login_sessions: List["QRLoginSession"] = Relationship(back_populates="user_pool")
    audit_logs: List["AuditLog"] = Relationship(back_populates="user_pool")
    
    __table_args__ = (
        Index("idx_user_pools_name", "name"),
        Index("idx_user_pools_status", "status"),
    )


class Application(BaseModel, table=True):
    """应用表"""
    __tablename__ = "applications"
    
    user_pool_id: int = Field(foreign_key="user_pools.id")
    name: str = Field(max_length=100, description="应用名称")
    type: ApplicationType = Field(default=ApplicationType.WEB, description="应用类型")
    app_id: str = Field(max_length=64, unique=True, description="应用ID")
    app_secret: str = Field(max_length=128, description="应用密钥")
    description: Optional[str] = Field(default=None, description="应用描述")
    callback_urls: Optional[List[str]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="回调地址列表"
    )
    logout_urls: Optional[List[str]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="登出地址列表"
    )
    allowed_origins: Optional[List[str]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="允许的来源域名"
    )
    token_lifetime: int = Field(default=3600, description="Token有效期(秒)")
    refresh_token_lifetime: int = Field(default=2592000, description="Refresh Token有效期(秒)")
    status: UserPoolStatus = Field(default=UserPoolStatus.ACTIVE)
    
    # 关系
    user_pool: UserPool = Relationship(back_populates="applications")
    qr_login_sessions: List["QRLoginSession"] = Relationship(back_populates="application")
    
    __table_args__ = (
        Index("idx_applications_user_pool_id", "user_pool_id"),
        Index("idx_applications_app_id", "app_id"),
        Index("idx_applications_status", "status"),
    )


class User(BaseModel, table=True):
    """用户表"""
    __tablename__ = "users"
    
    user_pool_id: int = Field(foreign_key="user_pools.id")
    username: Optional[str] = Field(default=None, max_length=100, description="用户名")
    email: Optional[str] = Field(default=None, max_length=255, description="邮箱")
    phone: Optional[str] = Field(default=None, max_length=20, description="手机号")
    nickname: Optional[str] = Field(default=None, max_length=100, description="昵称")
    avatar_url: Optional[str] = Field(default=None, max_length=500, description="头像URL")
    profile_data: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="扩展用户信息"
    )
    email_verified: bool = Field(default=False, description="邮箱是否已验证")
    phone_verified: bool = Field(default=False, description="手机号是否已验证")
    status: UserStatus = Field(default=UserStatus.PENDING)
    last_login_at: Optional[datetime] = Field(default=None, description="最后登录时间")
    
    # 关系
    user_pool: UserPool = Relationship(back_populates="users")
    credentials: List["Credential"] = Relationship(back_populates="user")
    user_roles: List["UserRole"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "[UserRole.user_id]"}
    )
    granted_roles: List["UserRole"] = Relationship(
        back_populates="granted_by_user",
        sa_relationship_kwargs={"foreign_keys": "[UserRole.granted_by]"}
    )
    qr_login_sessions: List["QRLoginSession"] = Relationship(back_populates="user")
    audit_logs: List["AuditLog"] = Relationship(back_populates="user")
    
    __table_args__ = (
        UniqueConstraint("user_pool_id", "username", name="uq_user_pool_username"),
        UniqueConstraint("user_pool_id", "email", name="uq_user_pool_email"),
        UniqueConstraint("user_pool_id", "phone", name="uq_user_pool_phone"),
        Index("idx_users_user_pool_id", "user_pool_id"),
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
        Index("idx_users_phone", "phone"),
        Index("idx_users_status", "status"),
    )


class CredentialType(str, Enum):
    """凭证类型枚举"""
    PASSWORD = "password"
    SOCIAL = "social"
    MFA = "mfa"


class Credential(BaseModel, table=True):
    """凭证表"""
    __tablename__ = "credentials"
    
    user_id: int = Field(foreign_key="users.id")
    type: CredentialType = Field(description="凭证类型")
    identifier: str = Field(max_length=255, description="标识符(邮箱/手机/社交账号ID)")
    credential: str = Field(description="凭证(哈希密码/OAuth token等)")
    salt: Optional[str] = Field(default=None, max_length=32, description="密码盐值")
    provider: Optional[str] = Field(default=None, max_length=50, description="第三方提供商")
    expires_at: Optional[datetime] = Field(default=None, description="凭证过期时间")
    
    # 关系
    user: User = Relationship(back_populates="credentials")
    
    __table_args__ = (
        UniqueConstraint("user_id", "type", "identifier", name="uq_user_type_identifier"),
        Index("idx_credentials_user_id", "user_id"),
        Index("idx_credentials_type", "type"),
        Index("idx_credentials_identifier", "identifier"),
    )
