"""
调试认证测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User, UserPool, Credential
from app.models.user import CredentialType, UserStatus, UserPoolStatus
from app.services.auth_service import AuthService
from tests.conftest import TestAsyncSessionLocal


class TestAuthDebug:
    """认证调试测试"""

    @pytest.mark.asyncio
    async def test_data_creation_and_auth_service(self, db_session: AsyncSession, test_user_pool: UserPool, test_user: User):
        """测试数据创建和认证服务"""
        print(f"用户池ID: {test_user_pool.id}")
        print(f"用户ID: {test_user.id}")
        print(f"用户名: {test_user.username}")
        
        # 检查用户是否存在
        result = await db_session.execute(
            select(User).where(User.id == test_user.id)
        )
        user = result.scalar_one_or_none()
        assert user is not None
        print(f"数据库中找到用户: {user.username}")
        
        # 检查凭证是否存在
        result = await db_session.execute(
            select(Credential).where(
                Credential.user_id == test_user.id,
                Credential.type == CredentialType.PASSWORD
            )
        )
        credential = result.scalar_one_or_none()
        assert credential is not None
        print(f"数据库中找到凭证: {credential.identifier}")
        
        # 测试认证服务
        auth_service = AuthService(db_session)
        authenticated_user = await auth_service.authenticate_user(
            identifier="testuser",
            password="testpassword123",
            user_pool_id=test_user_pool.id
        )
        
        assert authenticated_user is not None
        assert authenticated_user.id == test_user.id
        print("认证服务测试通过!")

    @pytest.mark.asyncio
    async def test_login_api_with_direct_data_creation(self, client: TestClient):
        """测试登录API - 直接在测试中创建数据"""
        from app.core.security import security
        
        # 直接创建测试数据到数据库
        async with TestAsyncSessionLocal() as session:
            # 创建用户池
            user_pool = UserPool(
                name="测试用户池",
                description="用于测试的用户池",
                settings={},
                status=UserPoolStatus.ACTIVE
            )
            session.add(user_pool)
            await session.flush()
            await session.refresh(user_pool)
            
            # 创建用户
            user = User(
                user_pool_id=user_pool.id,
                username="testuser",
                email="test@example.com",
                phone="13812345678",
                nickname="测试用户",
                status=UserStatus.ACTIVE
            )
            session.add(user)
            await session.flush()
            await session.refresh(user)
            
            # 创建密码凭证
            password_hash = security.get_password_hash("testpassword123")
            credential = Credential(
                user_id=user.id,
                type=CredentialType.PASSWORD,
                identifier="testuser",
                credential=password_hash
            )
            session.add(credential)
            await session.commit()  # 强制提交
            
            print(f"创建用户池: {user_pool.id}, 用户: {user.id}")
        
        # 现在测试登录API
        login_data = {
            "identifier": "testuser", 
            "password": "testpassword123",
            "user_pool_id": user_pool.id
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.json()}")
        
        # 断言登录成功
        assert response.status_code == 200
        response_data = response.json()
        assert "access_token" in response_data
        print("登录成功!")
