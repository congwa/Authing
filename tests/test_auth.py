"""
认证相关测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserPool
from app.services.auth_service import AuthService
from app.core.security import jwt_utils
from tests.conftest import TEST_USER_DATA


class TestAuthAPI:
    """认证API测试"""
    
    def test_login_success(self, client: TestClient, test_user_pool: UserPool, test_user: User):
        """测试登录成功"""
        login_data = {
            "identifier": "testuser",
            "password": "testpassword123",
            "user_pool_id": test_user_pool.id
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "登录成功"
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client: TestClient, test_user_pool: UserPool):
        """测试登录失败-错误凭证"""
        login_data = {
            "identifier": "testuser",
            "password": "wrongpassword",
            "user_pool_id": test_user_pool.id
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "用户名或密码错误"
    
    def test_login_user_not_found(self, client: TestClient, test_user_pool: UserPool):
        """测试登录失败-用户不存在"""
        login_data = {
            "identifier": "nonexistent",
            "password": "testpassword123",
            "user_pool_id": test_user_pool.id
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "用户名或密码错误"
    
    def test_register_success(self, client: TestClient, test_user_pool: UserPool):
        """测试注册成功"""
        import uuid
        unique_suffix = str(uuid.uuid4())[:8]
        register_data = {
            "username": f"newuser_{unique_suffix}",
            "email": f"newuser_{unique_suffix}@example.com",
            "password": "newpassword123",
            "nickname": "新用户",
            "user_pool_id": test_user_pool.id
        }
        
        response = client.post("/api/v1/auth/register", json=register_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "注册成功"
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
    
    def test_register_duplicate_username(self, client: TestClient, test_user_pool: UserPool, test_user: User):
        """测试注册失败-用户名重复"""
        register_data = {
            "username": "testuser",  # 已存在的用户名
            "email": "new@example.com",
            "password": "newpassword123",
            "user_pool_id": test_user_pool.id
        }
        
        response = client.post("/api/v1/auth/register", json=register_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "用户名已存在" in data["detail"]
    
    def test_register_duplicate_email(self, client: TestClient, test_user_pool: UserPool, test_user: User):
        """测试注册失败-邮箱重复"""
        import uuid
        unique_suffix = str(uuid.uuid4())[:8]
        register_data = {
            "username": f"uniqueuser_{unique_suffix}",  # 确保用户名唯一
            "email": "testuser@example.com",  # 使用test_user的邮箱
            "password": "newpassword123",
            "user_pool_id": test_user_pool.id
        }
        
        response = client.post("/api/v1/auth/register", json=register_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "邮箱已被注册" in data["detail"]
    
    def test_refresh_token_success(self, client: TestClient, test_user_pool: UserPool, test_user: User):
        """测试刷新令牌成功"""
        # 先登录获取refresh_token
        login_data = {
            "identifier": "testuser",
            "password": "testpassword123",
            "user_pool_id": test_user_pool.id
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        refresh_token = login_response.json()["data"]["refresh_token"]
        
        # 刷新令牌
        refresh_data = {"refresh_token": refresh_token}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "令牌刷新成功"
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
    
    def test_refresh_token_invalid(self, client: TestClient):
        """测试刷新令牌失败-无效令牌"""
        refresh_data = {"refresh_token": "invalid_token"}
        response = client.post("/api/v1/auth/refresh", json=refresh_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "无效的刷新令牌"
    
    def test_logout_success(self, client: TestClient, auth_headers: dict):
        """测试登出成功"""
        response = client.post("/api/v1/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "登出成功"
        assert data["data"] is True
    
    def test_logout_unauthorized(self, client: TestClient):
        """测试登出失败-未认证"""
        response = client.post("/api/v1/auth/logout")
        
        assert response.status_code == 403
    
    def test_send_otp_success(self, client: TestClient, test_user_pool: UserPool):
        """测试发送验证码成功"""
        otp_data = {
            "identifier": "13812345678",
            "type": "login",
            "user_pool_id": test_user_pool.id
        }
        
        response = client.post("/api/v1/auth/otp/send", json=otp_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "验证码发送成功"
        assert data["data"] is True
    
    def test_create_qr_login_success(self, client: TestClient, test_user_pool: UserPool):
        """测试创建扫码登录成功"""
        params = {
            "user_pool_id": test_user_pool.id,
            "app_id": "test_app"
        }
        
        response = client.post("/api/v1/auth/qr/create", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "扫码会话创建成功"
        assert "scene_id" in data["data"]
        assert "qr_code_url" in data["data"]
        assert "expires_at" in data["data"]


class TestAuthService:
    """认证服务测试"""
    
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, db_session: AsyncSession, test_user: User):
        """测试用户认证成功"""
        auth_service = AuthService(db_session)
        
        user = await auth_service.authenticate_user(
            identifier="testuser",
            password="testpassword123",
            user_pool_id=test_user.user_pool_id
        )
        
        assert user is not None
        assert user.id == test_user.id
        assert user.username == "testuser"
    
    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self, db_session: AsyncSession, test_user: User):
        """测试用户认证失败-密码错误"""
        auth_service = AuthService(db_session)
        
        user = await auth_service.authenticate_user(
            identifier="testuser",
            password="wrongpassword",
            user_pool_id=test_user.user_pool_id
        )
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, db_session: AsyncSession, test_user_pool: UserPool):
        """测试用户认证失败-用户不存在"""
        auth_service = AuthService(db_session)
        
        user = await auth_service.authenticate_user(
            identifier="nonexistent",
            password="testpassword123",
            user_pool_id=test_user_pool.id
        )
        
        assert user is None
    
    @pytest.mark.asyncio
    async def test_create_user_tokens(self, db_session: AsyncSession, test_user: User):
        """测试创建用户令牌"""
        auth_service = AuthService(db_session)
        
        tokens = await auth_service.create_user_tokens(test_user)
        
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"
        assert tokens.expires_in > 0
        
        # 验证access_token内容
        payload = jwt_utils.verify_token(tokens.access_token)
        assert payload is not None
        assert payload["sub"] == str(test_user.id)
        assert payload["type"] == "access"
        
        # 验证refresh_token内容
        payload = jwt_utils.verify_token(tokens.refresh_token)
        assert payload is not None
        assert payload["sub"] == str(test_user.id)
        assert payload["type"] == "refresh"
    
    @pytest.mark.asyncio
    async def test_register_user_success(self, db_session: AsyncSession, test_user_pool: UserPool):
        """测试注册用户成功"""
        auth_service = AuthService(db_session)
        
        user = await auth_service.register_user(
            user_pool_id=test_user_pool.id,
            username="newuser",
            email="newuser@example.com",
            password="newpassword123",
            nickname="新用户"
        )
        
        assert user is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.nickname == "新用户"
        assert user.user_pool_id == test_user_pool.id
    
    @pytest.mark.asyncio
    async def test_send_otp_code_success(self, db_session: AsyncSession, test_user_pool: UserPool):
        """测试发送验证码成功"""
        auth_service = AuthService(db_session)
        
        # 清理可能存在的OTP记录以避免冷却期限制
        from app.models.auth import OTPCode
        from sqlmodel import delete
        await db_session.execute(
            delete(OTPCode).where(OTPCode.identifier == "13812345678")
        )
        await db_session.commit()
        
        result = await auth_service.send_otp_code(
            identifier="13812345678",
            otp_type="login",
            user_pool_id=test_user_pool.id
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_create_qr_login_session(self, db_session: AsyncSession, test_user_pool: UserPool):
        """测试创建扫码登录会话"""
        auth_service = AuthService(db_session)
        
        session = await auth_service.create_qr_login_session(
            user_pool_id=test_user_pool.id,
            app_id="test_app"
        )
        
        assert session is not None
        assert session.scene_id is not None
        assert session.user_pool_id == test_user_pool.id
        assert session.app_id == "test_app"
        assert session.status == "pending"
