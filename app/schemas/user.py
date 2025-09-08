"""
用户相关数据模式
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, EmailStr, validator
from app.models.user import UserStatus, UserPoolStatus


class UserPoolCreate(BaseModel):
    """创建用户池请求"""
    name: str = Field(description="用户池名称")
    description: Optional[str] = Field(default=None, description="用户池描述")
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict, description="用户池配置")


class UserPoolUpdate(BaseModel):
    """更新用户池请求"""
    name: Optional[str] = Field(default=None, description="用户池名称")
    description: Optional[str] = Field(default=None, description="用户池描述")
    settings: Optional[Dict[str, Any]] = Field(default=None, description="用户池配置")
    status: Optional[UserPoolStatus] = Field(default=None, description="状态")


class UserPoolResponse(BaseModel):
    """用户池响应"""
    id: int = Field(description="用户池ID")
    name: str = Field(description="用户池名称")
    description: Optional[str] = Field(description="用户池描述")
    settings: Dict[str, Any] = Field(description="用户池配置")
    status: UserPoolStatus = Field(description="状态")
    created_at: datetime = Field(description="创建时间")
    updated_at: Optional[datetime] = Field(description="更新时间")


class ApplicationCreate(BaseModel):
    """创建应用请求"""
    user_pool_id: int = Field(description="用户池ID")
    app_name: str = Field(description="应用名称")
    callback_urls: Optional[List[str]] = Field(default_factory=list, description="回调地址列表")
    logout_urls: Optional[List[str]] = Field(default_factory=list, description="登出地址列表")
    allowed_origins: Optional[List[str]] = Field(default_factory=list, description="允许的来源域名")
    token_lifetime: Optional[int] = Field(default=3600, description="Token有效期(秒)")
    refresh_token_lifetime: Optional[int] = Field(default=2592000, description="Refresh Token有效期(秒)")


class ApplicationResponse(BaseModel):
    """应用响应"""
    id: int = Field(description="应用ID")
    user_pool_id: int = Field(description="用户池ID")
    app_name: str = Field(description="应用名称")
    app_id: str = Field(description="应用ID")
    app_secret: str = Field(description="应用密钥")
    callback_urls: List[str] = Field(description="回调地址列表")
    logout_urls: List[str] = Field(description="登出地址列表")
    allowed_origins: List[str] = Field(description="允许的来源域名")
    token_lifetime: int = Field(description="Token有效期(秒)")
    refresh_token_lifetime: int = Field(description="Refresh Token有效期(秒)")
    status: UserPoolStatus = Field(description="状态")
    created_at: datetime = Field(description="创建时间")


class UserCreate(BaseModel):
    """创建用户请求"""
    user_pool_id: int = Field(description="用户池ID")
    username: Optional[str] = Field(default=None, description="用户名")
    email: Optional[EmailStr] = Field(default=None, description="邮箱")
    phone: Optional[str] = Field(default=None, description="手机号")
    password: str = Field(description="密码")
    nickname: Optional[str] = Field(default=None, description="昵称")
    avatar_url: Optional[str] = Field(default=None, description="头像URL")
    profile_data: Optional[Dict[str, Any]] = Field(default_factory=dict, description="扩展信息")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度不能少于8位')
        return v


class UserUpdate(BaseModel):
    """更新用户请求"""
    username: Optional[str] = Field(default=None, description="用户名")
    email: Optional[EmailStr] = Field(default=None, description="邮箱")
    phone: Optional[str] = Field(default=None, description="手机号")
    nickname: Optional[str] = Field(default=None, description="昵称")
    avatar_url: Optional[str] = Field(default=None, description="头像URL")
    profile_data: Optional[Dict[str, Any]] = Field(default=None, description="扩展信息")
    status: Optional[UserStatus] = Field(default=None, description="用户状态")


class UserResponse(BaseModel):
    """用户响应"""
    id: int = Field(description="用户ID")
    user_pool_id: int = Field(description="用户池ID")
    username: Optional[str] = Field(description="用户名")
    email: Optional[str] = Field(description="邮箱")
    phone: Optional[str] = Field(description="手机号")
    nickname: Optional[str] = Field(description="昵称")
    avatar_url: Optional[str] = Field(description="头像URL")
    profile_data: Dict[str, Any] = Field(description="扩展信息")
    email_verified: bool = Field(description="邮箱是否已验证")
    phone_verified: bool = Field(description="手机号是否已验证")
    status: UserStatus = Field(description="用户状态")
    last_login_at: Optional[datetime] = Field(description="最后登录时间")
    created_at: datetime = Field(description="创建时间")
    updated_at: Optional[datetime] = Field(description="更新时间")


class UserListQuery(BaseModel):
    """用户列表查询参数"""
    user_pool_id: int = Field(description="用户池ID")
    status: Optional[UserStatus] = Field(default=None, description="用户状态筛选")
    keyword: Optional[str] = Field(default=None, description="关键词搜索（用户名/邮箱/手机号）")
    page: int = Field(default=1, ge=1, description="页码")
    per_page: int = Field(default=20, ge=1, le=100, description="每页数量")


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(description="原密码")
    new_password: str = Field(description="新密码")
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度不能少于8位')
        return v
