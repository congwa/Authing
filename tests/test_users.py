"""
用户管理相关测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserPool, Application
from app.services.user_service import UserService
from app.models.user import UserStatus, UserPoolStatus, ApplicationType
from tests.conftest import TEST_USER_DATA, TEST_USER_POOL_DATA


class TestUserPoolAPI:
    """用户池API测试"""
    
    def test_create_user_pool_success(self, client: TestClient, admin_auth_headers: dict):
        """测试创建用户池成功"""
        response = client.post(
            "/api/v1/users/user-pools",
            json=TEST_USER_POOL_DATA,
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "用户池创建成功"
        assert data["data"]["name"] == TEST_USER_POOL_DATA["name"]
        assert data["data"]["description"] == TEST_USER_POOL_DATA["description"]
    
    def test_get_user_pools_success(self, client: TestClient, admin_auth_headers: dict):
        """测试获取用户池列表成功"""
        response = client.get("/api/v1/users/user-pools", headers=admin_auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "items" in data["data"]
        assert "total" in data["data"]
    
    def test_get_user_pool_by_id_success(self, client: TestClient, admin_auth_headers: dict, test_user_pool: UserPool):
        """测试根据ID获取用户池成功"""
        response = client.get(
            f"/api/v1/users/user-pools/{test_user_pool.id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == test_user_pool.id
        assert data["data"]["name"] == test_user_pool.name
    
    def test_update_user_pool_success(self, client: TestClient, admin_auth_headers: dict, test_user_pool: UserPool):
        """测试更新用户池成功"""
        update_data = {
            "name": "更新后的用户池",
            "description": "更新后的描述"
        }
        
        response = client.put(
            f"/api/v1/users/user-pools/{test_user_pool.id}",
            json=update_data,
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["name"] == update_data["name"]
        assert data["data"]["description"] == update_data["description"]
    
    def test_delete_user_pool_success(self, client: TestClient, admin_auth_headers: dict):
        """测试删除用户池成功"""
        # 先创建一个用户池用于删除
        create_response = client.post(
            "/api/v1/users/user-pools",
            json=TEST_USER_POOL_DATA,
            headers=admin_auth_headers
        )
        user_pool_id = create_response.json()["data"]["id"]
        
        # 删除用户池
        response = client.delete(
            f"/api/v1/users/user-pools/{user_pool_id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"] is True


class TestApplicationAPI:
    """应用API测试"""
    
    def test_create_application_success(self, client: TestClient, admin_auth_headers: dict, test_user_pool: UserPool):
        """测试创建应用成功"""
        app_data = {
            "name": "测试应用",
            "type": ApplicationType.WEB.value,
            "description": "用于测试的应用",
            "user_pool_id": test_user_pool.id
        }
        
        response = client.post(
            "/api/v1/users/applications",
            json=app_data,
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "应用创建成功"
        assert data["data"]["name"] == app_data["name"]
        assert data["data"]["type"] == app_data["type"]
    
    def test_get_applications_success(self, client: TestClient, admin_auth_headers: dict, test_user_pool: UserPool):
        """测试获取应用列表成功"""
        response = client.get(
            f"/api/v1/users/applications?user_pool_id={test_user_pool.id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "items" in data["data"]
        assert "total" in data["data"]


class TestUserAPI:
    """用户API测试"""
    
    def test_create_user_success(self, client: TestClient, admin_auth_headers: dict, test_user_pool: UserPool):
        """测试创建用户成功"""
        user_data = {
            **TEST_USER_DATA,
            "user_pool_id": test_user_pool.id
        }
        
        response = client.post(
            "/api/v1/users/users",
            json=user_data,
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["message"] == "用户创建成功"
        assert data["data"]["username"] == user_data["username"]
        assert data["data"]["email"] == user_data["email"]
    
    def test_get_users_success(self, client: TestClient, admin_auth_headers: dict, test_user_pool: UserPool):
        """测试获取用户列表成功"""
        response = client.get(
            f"/api/v1/users/users?user_pool_id={test_user_pool.id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "items" in data["data"]
        assert "total" in data["data"]
    
    def test_get_user_by_id_success(self, client: TestClient, admin_auth_headers: dict, test_user: User):
        """测试根据ID获取用户成功"""
        response = client.get(
            f"/api/v1/users/users/{test_user.id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["id"] == test_user.id
        assert data["data"]["username"] == test_user.username
    
    def test_update_user_success(self, client: TestClient, admin_auth_headers: dict, test_user: User):
        """测试更新用户成功"""
        update_data = {
            "nickname": "更新后的昵称",
            "phone": "13987654321"
        }
        
        response = client.put(
            f"/api/v1/users/users/{test_user.id}",
            json=update_data,
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["nickname"] == update_data["nickname"]
        assert data["data"]["phone"] == update_data["phone"]
    
    def test_delete_user_success(self, client: TestClient, admin_auth_headers: dict, test_user_pool: UserPool):
        """测试删除用户成功"""
        # 先创建一个用户用于删除
        user_data = {
            "username": "deleteme",
            "email": "deleteme@example.com",
            "password": "password123",
            "user_pool_id": test_user_pool.id
        }
        
        create_response = client.post(
            "/api/v1/users/users",
            json=user_data,
            headers=admin_auth_headers
        )
        user_id = create_response.json()["data"]["id"]
        
        # 删除用户
        response = client.delete(
            f"/api/v1/users/users/{user_id}",
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"] is True
    
    def test_change_password_success(self, client: TestClient, auth_headers: dict, test_user: User):
        """测试修改密码成功"""
        password_data = {
            "old_password": "testpassword123",
            "new_password": "newpassword123"
        }
        
        response = client.post(
            f"/api/v1/users/users/{test_user.id}/change-password",
            json=password_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"] is True
    
    def test_reset_password_success(self, client: TestClient, admin_auth_headers: dict, test_user: User):
        """测试重置密码成功"""
        reset_data = {
            "new_password": "resetpassword123"
        }
        
        response = client.post(
            f"/api/v1/users/users/{test_user.id}/reset-password",
            json=reset_data,
            headers=admin_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"] is True


class TestUserService:
    """用户服务测试"""
    
    @pytest.mark.asyncio
    async def test_create_user_pool_success(self, db_session: AsyncSession):
        """测试创建用户池成功"""
        user_service = UserService(db_session)
        
        user_pool = await user_service.create_user_pool(
            name="新用户池",
            description="新创建的用户池",
            settings={"theme": "dark"}
        )
        
        assert user_pool is not None
        assert user_pool.name == "新用户池"
        assert user_pool.description == "新创建的用户池"
        assert user_pool.settings == {"theme": "dark"}
        assert user_pool.status == UserPoolStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_get_user_pool_by_id(self, db_session: AsyncSession, test_user_pool: UserPool):
        """测试根据ID获取用户池"""
        user_service = UserService(db_session)
        
        user_pool = await user_service.get_user_pool_by_id(test_user_pool.id)
        
        assert user_pool is not None
        assert user_pool.id == test_user_pool.id
        assert user_pool.name == test_user_pool.name
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, db_session: AsyncSession, test_user_pool: UserPool):
        """测试创建用户成功"""
        user_service = UserService(db_session)
        
        user = await user_service.create_user(
            user_pool_id=test_user_pool.id,
            username="newuser",
            email="newuser@example.com",
            password="password123",
            nickname="新用户"
        )
        
        assert user is not None
        assert user.username == "newuser"
        assert user.email == "newuser@example.com"
        assert user.nickname == "新用户"
        assert user.user_pool_id == test_user_pool.id
        assert user.status == UserStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_get_user_by_id(self, db_session: AsyncSession, test_user: User):
        """测试根据ID获取用户"""
        user_service = UserService(db_session)
        
        user = await user_service.get_user_by_id(test_user.id)
        
        assert user is not None
        assert user.id == test_user.id
        assert user.username == test_user.username
    
    @pytest.mark.asyncio
    async def test_update_user_success(self, db_session: AsyncSession, test_user: User):
        """测试更新用户成功"""
        user_service = UserService(db_session)
        
        updated_user = await user_service.update_user(
            user_id=test_user.id,
            nickname="更新后的昵称",
            phone="13987654321"
        )
        
        assert updated_user is not None
        assert updated_user.nickname == "更新后的昵称"
        assert updated_user.phone == "13987654321"
    
    @pytest.mark.asyncio
    async def test_delete_user_success(self, db_session: AsyncSession, test_user_pool: UserPool):
        """测试删除用户成功"""
        user_service = UserService(db_session)
        
        # 先创建一个用户
        user = await user_service.create_user(
            user_pool_id=test_user_pool.id,
            username="deleteme",
            email="deleteme@example.com",
            password="password123"
        )
        
        # 删除用户
        result = await user_service.delete_user(user.id)
        
        assert result is True
        
        # 验证用户状态已被设置为BLOCKED（软删除）
        deleted_user = await user_service.get_user_by_id(user.id)
        assert deleted_user.status == UserStatus.BLOCKED
    
    @pytest.mark.asyncio
    async def test_change_user_password_success(self, db_session: AsyncSession, test_user: User):
        """测试修改用户密码成功"""
        user_service = UserService(db_session)
        
        result = await user_service.change_password(
            user_id=test_user.id,
            old_password="testpassword123",
            new_password="newpassword123"
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_change_user_password_wrong_old_password(self, db_session: AsyncSession, test_user: User):
        """测试修改用户密码失败-旧密码错误"""
        user_service = UserService(db_session)
        
        with pytest.raises(Exception) as exc_info:
            await user_service.change_password(
                user_id=test_user.id,
                old_password="wrongpassword",
                new_password="newpassword123"
            )
        
        assert "原密码错误" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_reset_user_password_success(self, db_session: AsyncSession, test_user: User):
        """测试重置用户密码成功"""
        user_service = UserService(db_session)
        
        result = await user_service.reset_password(
            user_id=test_user.id,
            new_password="resetpassword123"
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_create_application_success(self, db_session: AsyncSession, test_user_pool: UserPool):
        """测试创建应用成功"""
        user_service = UserService(db_session)
        
        app = await user_service.create_application(
            user_pool_id=test_user_pool.id,
            app_name="测试应用"
        )
        
        assert app is not None
        assert app.app_name == "测试应用"
        assert app.user_pool_id == test_user_pool.id
