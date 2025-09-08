"""
认证相关数据模式
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, validator
from app.models.auth import OTPType, QRLoginStatus
from app.schemas.user import UserResponse


class LoginRequest(BaseModel):
    """登录请求"""
    identifier: str = Field(description="用户标识（用户名/邮箱/手机号）")
    password: str = Field(description="密码")
    user_pool_id: int = Field(description="用户池ID")
    
    @validator('identifier')
    def validate_identifier(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('用户标识不能为空')
        return v.strip()


class OTPLoginRequest(BaseModel):
    """验证码登录请求"""
    identifier: str = Field(description="手机号或邮箱")
    code: str = Field(description="验证码")
    user_pool_id: int = Field(description="用户池ID")
    
    @validator('code')
    def validate_code(cls, v):
        if not v or len(v) != 6 or not v.isdigit():
            raise ValueError('验证码必须是6位数字')
        return v


class SendOTPRequest(BaseModel):
    """发送验证码请求"""
    identifier: str = Field(description="手机号或邮箱")
    type: OTPType = Field(description="验证码类型")
    user_pool_id: int = Field(description="用户池ID")


class RegisterRequest(BaseModel):
    """注册请求"""
    username: Optional[str] = Field(default=None, description="用户名")
    email: Optional[EmailStr] = Field(default=None, description="邮箱")
    phone: Optional[str] = Field(default=None, description="手机号")
    password: str = Field(description="密码")
    nickname: Optional[str] = Field(default=None, description="昵称")
    user_pool_id: int = Field(description="用户池ID")
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度不能少于8位')
        return v
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.startswith('+'):
            # 简单的手机号验证
            if not v.isdigit() or len(v) != 11:
                raise ValueError('手机号格式不正确')
        return v


class TokenResponse(BaseModel):
    """Token响应"""
    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="过期时间（秒）")
    user: Optional[UserResponse] = Field(default=None, description="用户信息")


class RefreshTokenRequest(BaseModel):
    """刷新Token请求"""
    refresh_token: str = Field(description="刷新令牌")


class QRLoginCreateResponse(BaseModel):
    """创建扫码登录响应"""
    scene_id: str = Field(description="场景ID")
    qr_code_url: str = Field(description="二维码URL")
    expires_at: datetime = Field(description="过期时间")


class QRLoginStatusResponse(BaseModel):
    """扫码登录状态响应"""
    scene_id: str = Field(description="场景ID")
    status: QRLoginStatus = Field(description="状态")
    user_id: Optional[int] = Field(default=None, description="用户ID")
    expires_at: datetime = Field(description="过期时间")


class QRLoginConfirmRequest(BaseModel):
    """确认扫码登录请求"""
    scene_id: str = Field(description="场景ID")
    confirm: bool = Field(description="是否确认登录")


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    identifier: str = Field(description="手机号或邮箱")
    code: str = Field(description="验证码")
    new_password: str = Field(description="新密码")
    user_pool_id: int = Field(description="用户池ID")
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码长度不能少于8位')
        return v
