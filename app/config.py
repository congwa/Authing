"""
应用配置管理
"""
import os
from functools import lru_cache
from typing import Optional, List
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    project_name: str = "统一身份认证平台"
    version: str = "0.1.0"
    debug: bool = False
    api_v1_str: str = "/api/v1"
    
    # 数据库配置
    database_url: str = "sqlite+aiosqlite:///./authing.db"
    
    # JWT配置
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 30
    
    # CORS配置
    backend_cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ]
    
    # Redis配置
    redis_url: str = "redis://localhost:6379/0"
    
    # 短信/邮件配置
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # OTP配置
    otp_expire_minutes: int = 5
    otp_max_attempts: int = 5
    
    # 二维码登录配置
    qr_login_expire_minutes: int = 2
    
    # 限流配置
    rate_limit_per_minute: int = 60
    login_rate_limit_per_minute: int = 5
    
    # 日志配置
    log_level: str = "INFO"
    
    @validator("backend_cors_origins", pre=True)
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """获取配置实例（单例模式）"""
    return Settings()


# 导出配置实例
settings = get_settings()
