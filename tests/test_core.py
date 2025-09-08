"""
核心模块测试
"""
import pytest
import jwt
from datetime import datetime, timedelta

from app.core.security import SecurityUtils, JWTUtils
from app.core.exceptions import (
    AuthError, 
    PermissionError, 
    ValidationError, 
    ConflictError,
    RateLimitError,
    OTPError
)


class TestSecurityUtils:
    """安全工具测试"""
    
    def test_password_hash_and_verify(self):
        """测试密码哈希和验证"""
        password = "testpassword123"
        
        # 测试哈希
        hash_password = SecurityUtils.get_password_hash(password)
        assert hash_password != password
        assert len(hash_password) > 50  # bcrypt哈希长度
        
        # 测试验证正确密码
        assert SecurityUtils.verify_password(password, hash_password) is True
        
        # 测试验证错误密码
        assert SecurityUtils.verify_password("wrongpassword", hash_password) is False
    
    def test_generate_otp_code(self):
        """测试生成验证码"""
        # 测试默认长度
        code1 = SecurityUtils.generate_otp_code()
        assert len(code1) == 6
        assert code1.isdigit()
        
        # 测试自定义长度
        code2 = SecurityUtils.generate_otp_code(length=4)
        assert len(code2) == 4
        assert code2.isdigit()
        
        # 测试生成多个验证码不相同（概率很小）
        codes = [SecurityUtils.generate_otp_code() for _ in range(10)]
        assert len(set(codes)) > 1  # 至少有一个不同
    
    def test_verify_otp_code(self):
        """测试验证码验证"""
        code = SecurityUtils.generate_otp_code()
        
        # 测试正确验证码
        assert SecurityUtils.verify_otp_code(code, code) is True
        
        # 测试错误验证码
        assert SecurityUtils.verify_otp_code(code, "000000") is False
        
        # 测试空验证码
        assert SecurityUtils.verify_otp_code("", "") is True
        assert SecurityUtils.verify_otp_code(code, "") is False
    
    def test_generate_random_string(self):
        """测试生成随机字符串"""
        # 测试默认长度
        str1 = SecurityUtils.generate_random_string()
        assert len(str1) == 32
        
        # 测试自定义长度
        str2 = SecurityUtils.generate_random_string(length=16)
        assert len(str2) == 16
        
        # 测试生成多个字符串不相同
        strings = [SecurityUtils.generate_random_string() for _ in range(10)]
        assert len(set(strings)) == 10  # 所有字符串都不同
    
    def test_encrypt_decrypt_data(self):
        """测试数据加密解密"""
        data = "sensitive_data_123"
        
        # 测试加密
        encrypted = SecurityUtils.encrypt_data(data)
        assert encrypted != data
        assert len(encrypted) > len(data)
        
        # 测试解密
        decrypted = SecurityUtils.decrypt_data(encrypted)
        assert decrypted == data
        
        # 测试空数据
        empty_encrypted = SecurityUtils.encrypt_data("")
        empty_decrypted = SecurityUtils.decrypt_data(empty_encrypted)
        assert empty_decrypted == ""


class TestJWTUtils:
    """JWT工具测试"""
    
    def test_create_access_token(self):
        """测试创建访问令牌"""
        user_id = "12345"
        token = JWTUtils.create_access_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50  # JWT令牌应该相当长
    
    def test_create_refresh_token(self):
        """测试创建刷新令牌"""
        user_id = "12345"
        token = JWTUtils.create_refresh_token(user_id)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50
    
    def test_verify_token_success(self):
        """测试验证令牌成功"""
        user_id = "12345"
        access_token = JWTUtils.create_access_token(user_id)
        
        # 验证访问令牌
        payload = JWTUtils.verify_token(access_token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        
        # 验证刷新令牌
        refresh_token = JWTUtils.create_refresh_token(user_id)
        payload = JWTUtils.verify_token(refresh_token)
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
    
    def test_verify_token_invalid(self):
        """测试验证无效令牌"""
        # 测试完全无效的令牌
        payload = JWTUtils.verify_token("invalid_token")
        assert payload is None
        
        # 测试过期令牌（手动创建过期令牌）
        from app.config import settings
        expired_payload = {
            "sub": "12345",
            "type": "access",
            "exp": datetime.utcnow() - timedelta(hours=1)  # 1小时前过期
        }
        expired_token = jwt.encode(expired_payload, settings.secret_key, algorithm="HS256")
        payload = JWTUtils.verify_token(expired_token)
        assert payload is None
    
    def test_get_user_id_from_token(self):
        """测试从令牌获取用户ID"""
        user_id = "12345"
        token = JWTUtils.create_access_token(user_id)
        
        extracted_user_id = JWTUtils.get_user_id_from_token(token)
        assert extracted_user_id == user_id
        
        # 测试无效令牌
        invalid_user_id = JWTUtils.get_user_id_from_token("invalid_token")
        assert invalid_user_id is None


class TestExceptions:
    """异常测试"""
    
    def test_authentication_error(self):
        """测试认证错误"""
        with pytest.raises(AuthError) as exc_info:
            raise AuthError("认证失败")
        
        assert exc_info.value.status_code == 401
        assert str(exc_info.value.detail) == "认证失败"
    
    def test_permission_error(self):
        """测试权限错误"""
        with pytest.raises(PermissionError) as exc_info:
            raise PermissionError("权限不足")
        
        assert exc_info.value.status_code == 403
        assert str(exc_info.value.detail) == "权限不足"
    
    def test_validation_error(self):
        """测试验证错误"""
        with pytest.raises(ValidationError) as exc_info:
            raise ValidationError("验证失败")
        
        assert exc_info.value.status_code == 422
        assert str(exc_info.value.detail) == "验证失败"
    
    def test_conflict_error(self):
        """测试冲突错误"""
        with pytest.raises(ConflictError) as exc_info:
            raise ConflictError("资源冲突")
        
        assert exc_info.value.status_code == 409
        assert str(exc_info.value.detail) == "资源冲突"
    
    def test_rate_limit_error(self):
        """测试限流错误"""
        with pytest.raises(RateLimitError) as exc_info:
            raise RateLimitError("请求过于频繁")
        
        assert exc_info.value.status_code == 429
        assert str(exc_info.value.detail) == "请求过于频繁"
    
    def test_otp_error(self):
        """测试验证码错误"""
        with pytest.raises(OTPError) as exc_info:
            raise OTPError("验证码错误")
        
        assert exc_info.value.status_code == 400
        assert str(exc_info.value.detail) == "验证码错误"


class TestRateLimiter:
    """限流器测试"""
    
    def test_rate_limiter_allow(self):
        """测试限流器允许请求"""
        from app.core.security import RateLimiter
        
        limiter = RateLimiter()
        key = "test_key"
        
        # 第一次请求应该被允许
        assert limiter.is_allowed(key) is True
    
    def test_rate_limiter_block_after_limit(self):
        """测试限流器在达到限制后阻止请求"""
        from app.core.security import RateLimiter
        
        # 使用较小的限制进行测试
        limiter = RateLimiter(max_attempts=3, window_seconds=60)
        key = "test_key_block"
        
        # 前3次请求应该被允许
        for i in range(3):
            assert limiter.is_allowed(key) is True
        
        # 第4次请求应该被阻止
        assert limiter.is_allowed(key) is False
    
    def test_rate_limiter_reset_after_window(self):
        """测试限流器在时间窗口后重置"""
        from app.core.security import RateLimiter
        import time
        
        # 使用很短的时间窗口进行测试
        limiter = RateLimiter(max_attempts=2, window_seconds=1)
        key = "test_key_reset"
        
        # 用完限制
        assert limiter.is_allowed(key) is True
        assert limiter.is_allowed(key) is True
        assert limiter.is_allowed(key) is False  # 第3次被阻止
        
        # 等待时间窗口过期
        time.sleep(1.1)
        
        # 应该重新允许请求
        assert limiter.is_allowed(key) is True
