"""
安全相关功能
"""
import secrets
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import hashlib

from app.config import settings


# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 对称加密（用于敏感数据）
encryption_key = settings.secret_key.encode()[:32].ljust(32, b'0')
cipher_suite = Fernet(Fernet.generate_key())


class SecurityUtils:
    """安全工具类"""
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return pwd_context.verify(plain_password, hashed_password)
    
    @staticmethod
    def get_password_hash(password: str) -> str:
        """获取密码哈希"""
        return pwd_context.hash(password)
    
    @staticmethod
    def generate_salt() -> str:
        """生成随机盐值"""
        return secrets.token_hex(16)
    
    @staticmethod
    def generate_otp_code(length: int = 6) -> str:
        """生成数字验证码"""
        return ''.join([str(secrets.randbelow(10)) for _ in range(length)])
    
    @staticmethod
    def hash_otp_code(code: str, salt: Optional[str] = None) -> tuple[str, str]:
        """哈希验证码"""
        if salt is None:
            salt = SecurityUtils.generate_salt()
        
        # 使用SHA256进行哈希
        hash_obj = hashlib.sha256()
        hash_obj.update((code + salt).encode('utf-8'))
        code_hash = hash_obj.hexdigest()
        
        return code_hash, salt
    
    @staticmethod
    def verify_otp_code(code: str, expected_code: str) -> bool:
        """验证OTP代码"""
        return secrets.compare_digest(code, expected_code)
    
    @staticmethod
    def generate_random_string(length: int = 32) -> str:
        """生成随机字符串"""
        return secrets.token_urlsafe(length)[:length]
    
    @staticmethod
    def generate_app_secret() -> str:
        """生成应用密钥"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_scene_id() -> str:
        """生成场景ID"""
        import uuid
        return str(uuid.uuid4())
    
    @staticmethod
    def encrypt_data(data: str) -> str:
        """加密数据"""
        return cipher_suite.encrypt(data.encode()).decode()
    
    @staticmethod
    def decrypt_data(encrypted_data: str) -> str:
        """解密数据"""
        return cipher_suite.decrypt(encrypted_data.encode()).decode()


class JWTUtils:
    """JWT工具类"""
    
    @staticmethod
    def create_access_token(user_id: str) -> str:
        """创建访问令牌"""
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
        
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "type": "access"
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.secret_key, 
            algorithm=settings.algorithm
        )
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """创建刷新令牌"""
        expire = datetime.now(UTC) + timedelta(
            days=settings.refresh_token_expire_days
        )
        
        to_encode = {
            "sub": user_id,
            "exp": expire,
            "type": "refresh"
        }
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.secret_key, 
            algorithm=settings.algorithm
        )
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        """验证令牌"""
        try:
            payload = jwt.decode(
                token, 
                settings.secret_key, 
                algorithms=[settings.algorithm]
            )
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """解码令牌（不验证过期时间）"""
        try:
            payload = jwt.decode(
                token, 
                settings.secret_key, 
                algorithms=[settings.algorithm],
                options={"verify_exp": False}
            )
            return payload
        except JWTError:
            return None
    
    @staticmethod
    def is_token_expired(token: str) -> bool:
        """检查令牌是否过期"""
        try:
            payload = jwt.decode(
                token, 
                settings.secret_key, 
                algorithms=[settings.algorithm]
            )
            return False
        except JWTError:
            return True
    
    @staticmethod
    def get_token_type(token: str) -> Optional[str]:
        """获取令牌类型"""
        payload = JWTUtils.decode_token(token)
        if payload:
            return payload.get("type")
    
    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[str]:
        """从令牌中获取用户ID"""
        payload = JWTUtils.verify_token(token)
        if payload:
            return payload.get("sub")
        return None


class RateLimiter:
    """简单的内存限流器"""
    
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300):
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts = {}
    
    def is_allowed(self, key: str) -> bool:
        """检查是否允许请求"""
        import time
        now = time.time()
        
        # 清理过期的记录
        if key in self.attempts:
            self.attempts[key] = [
                timestamp for timestamp in self.attempts[key] 
                if now - timestamp < self.window_seconds
            ]
        
        # 检查当前请求数
        current_attempts = len(self.attempts.get(key, []))
        
        if current_attempts >= self.max_attempts:
            return False
        
        # 记录本次请求
        if key not in self.attempts:
            self.attempts[key] = []
        self.attempts[key].append(now)
        
        return True


# 全局实例
security = SecurityUtils()
jwt_utils = JWTUtils()
rate_limiter = RateLimiter()
