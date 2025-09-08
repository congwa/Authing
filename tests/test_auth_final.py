"""
使用最终测试架构的认证测试用例
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.conftest import SyncTestDataCreator


class TestAuthAPIFinal:
    """认证API测试 - 使用最终架构"""

    @pytest.mark.asyncio
    async def test_login_success_final(self, client: TestClient, db_session: AsyncSession, sync_data_creator: SyncTestDataCreator):
        """测试成功登录 - 最终版本"""
        # 创建测试数据
        user_pool = await sync_data_creator.create_user_pool(db_session)
        user = await sync_data_creator.create_user_with_credentials(
            db_session, 
            user_pool_id=user_pool.id,
            username="testuser",
            password="testpassword123"
        )
        
        print(f"创建用户池ID: {user_pool.id}, 用户ID: {user.id}")
        
        # 测试登录
        login_data = {
            "identifier": "testuser",
            "password": "testpassword123",
            "user_pool_id": user_pool.id
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        print(f"登录响应状态: {response.status_code}")
        print(f"登录响应内容: {response.json()}")
        
        # 验证登录成功
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["code"] == 200
        assert "data" in response_data
        
        token_data = response_data["data"]
        assert "access_token" in token_data
        assert "refresh_token" in token_data
        assert "user" in token_data
        assert token_data["user"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_login_invalid_credentials_final(self, client: TestClient, db_session: AsyncSession, sync_data_creator: SyncTestDataCreator):
        """测试无效凭证登录"""
        user_pool = await sync_data_creator.create_user_pool(db_session)
        await sync_data_creator.create_user_with_credentials(
            db_session,
            user_pool_id=user_pool.id,
            username="testuser",
            password="testpassword123"
        )
        
        login_data = {
            "identifier": "testuser",
            "password": "wrongpassword",
            "user_pool_id": user_pool.id
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_with_helper_final(self, client: TestClient, login_helper):
        """测试使用登录辅助函数"""
        import asyncio
        
        async def run_test():
            # 首先创建测试数据
            from tests.conftest import get_test_session, SyncTestDataCreator
            
            session = await get_test_session()
            creator = SyncTestDataCreator()
            
            user_pool = await creator.create_user_pool(session)
            await creator.create_user_with_credentials(
                session,
                user_pool_id=user_pool.id,
                username="testuser",
                password="testpassword123"
            )
            
            # 使用辅助函数登录
            auth_data = login_helper("testuser", "testpassword123", user_pool.id)
            assert "Authorization" in auth_data
            assert "token_data" in auth_data
            
            # 验证token有效性
            token_data = auth_data["token_data"]
            assert token_data["user"]["username"] == "testuser"
            
            print("登录辅助函数测试通过!")

        asyncio.run(run_test())
