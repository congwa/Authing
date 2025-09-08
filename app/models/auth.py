"""
认证相关数据模型
"""
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship, Index
from app.models.base import BaseModel, TimestampMixin


class OTPType(str, Enum):
    """验证码类型枚举"""
    LOGIN = "login"
    REGISTER = "register"
    RESET_PASSWORD = "reset_password"
    VERIFY = "verify"


class OTPCode(BaseModel, table=True):
    """一次性验证码表"""
    __tablename__ = "otp_codes"
    
    identifier: str = Field(max_length=255, description="手机号或邮箱")
    code_hash: str = Field(max_length=128, description="验证码哈希值")
    type: OTPType = Field(description="验证码类型")
    attempts: int = Field(default=0, description="尝试次数")
    max_attempts: int = Field(default=5, description="最大尝试次数")
    expires_at: datetime = Field(description="过期时间")
    used: bool = Field(default=False, description="是否已使用")
    ip_address: Optional[str] = Field(default=None, max_length=45, description="请求IP")
    user_agent: Optional[str] = Field(default=None, description="用户代理")
    
    __table_args__ = (
        Index("idx_otp_codes_identifier_type", "identifier", "type"),
        Index("idx_otp_codes_expires_at", "expires_at"),
        Index("idx_otp_codes_used", "used"),
    )


class QRLoginStatus(str, Enum):
    """扫码登录状态枚举"""
    PENDING = "pending"
    SCANNED = "scanned"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class QRLoginSession(TimestampMixin, table=True):
    """扫码登录会话表"""
    __tablename__ = "qr_login_sessions"
    
    scene_id: str = Field(primary_key=True, max_length=36, description="UUID")
    user_pool_id: int = Field(foreign_key="user_pools.id")
    app_id: str = Field(foreign_key="applications.app_id", max_length=64, description="发起登录的应用ID")
    status: QRLoginStatus = Field(default=QRLoginStatus.PENDING)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", description="确认登录的用户ID")
    expires_at: datetime = Field(description="过期时间")
    scanned_at: Optional[datetime] = Field(default=None, description="扫码时间")
    confirmed_at: Optional[datetime] = Field(default=None, description="确认时间")
    ip_address: Optional[str] = Field(default=None, max_length=45, description="Web端IP")
    user_agent: Optional[str] = Field(default=None, description="Web端用户代理")
    
    # 关系
    user_pool: "UserPool" = Relationship(back_populates="qr_login_sessions")
    application: "Application" = Relationship(back_populates="qr_login_sessions")
    user: Optional["User"] = Relationship(back_populates="qr_login_sessions")
    
    __table_args__ = (
        Index("idx_qr_login_sessions_status", "status"),
        Index("idx_qr_login_sessions_expires_at", "expires_at"),
        Index("idx_qr_login_sessions_user_id", "user_id"),
    )


class AuditLog(BaseModel, table=True):
    """审计日志表"""
    __tablename__ = "audit_logs"
    
    user_pool_id: Optional[int] = Field(default=None, foreign_key="user_pools.id")
    user_id: Optional[int] = Field(default=None, foreign_key="users.id")
    action: str = Field(max_length=100, description="操作类型")
    resource: Optional[str] = Field(default=None, max_length=100, description="操作资源")
    resource_id: Optional[str] = Field(default=None, max_length=100, description="资源ID")
    details: Optional[str] = Field(default=None, description="操作详情JSON字符串")
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None)
    success: bool = Field(description="操作是否成功")
    error_message: Optional[str] = Field(default=None, description="错误信息")
    
    # 关系
    user_pool: Optional["UserPool"] = Relationship(back_populates="audit_logs")
    user: Optional["User"] = Relationship(back_populates="audit_logs")
    
    __table_args__ = (
        Index("idx_audit_logs_user_pool_id", "user_pool_id"),
        Index("idx_audit_logs_user_id", "user_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_created_at", "created_at"),
        Index("idx_audit_logs_success", "success"),
    )
