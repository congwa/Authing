"""
集成测试
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserPool, Role, Permission
from tests.conftest import TEST_USER_DATA, TEST_ROLE_DATA, TEST_PERMISSION_DATA


class TestCompleteWorkflow:
    """完整工作流程测试"""
    
    def test_complete_user_lifecycle(self, client: TestClient, test_user_pool: UserPool):
        """测试完整的用户生命周期"""
        # 1. 注册新用户
        register_data = {
            **TEST_USER_DATA,
            "user_pool_id": test_user_pool.id
        }
        
        register_response = client.post("/api/v1/auth/register", json=register_data)
        assert register_response.status_code == 200
        
        user_data = register_response.json()["data"]
        access_token = user_data["access_token"]
        user_id = user_data["user"]["id"]
        
        # 2. 使用token访问受保护的资源
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = client.get(f"/api/v1/users/users/{user_id}", headers=auth_headers)
        assert profile_response.status_code == 200
        
        # 3. 修改密码
        change_password_data = {
            "old_password": TEST_USER_DATA["password"],
            "new_password": "newpassword456"
        }
        
        password_response = client.post(
            f"/api/v1/users/users/{user_id}/change-password",
            json=change_password_data,
            headers=auth_headers
        )
        assert password_response.status_code == 200
        
        # 4. 使用新密码登录
        login_data = {
            "identifier": TEST_USER_DATA["username"],
            "password": "newpassword456",
            "user_pool_id": test_user_pool.id
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        new_token = login_response.json()["data"]["access_token"]
        new_auth_headers = {"Authorization": f"Bearer {new_token}"}
        
        # 5. 登出
        logout_response = client.post("/api/v1/auth/logout", headers=new_auth_headers)
        assert logout_response.status_code == 200
    
    def test_complete_rbac_workflow(self, client: TestClient, admin_auth_headers: dict, 
                                   test_user_pool: UserPool, test_user: User):
        """测试完整的RBAC工作流程"""
        # 1. 创建权限
        permission_data = {
            **TEST_PERMISSION_DATA,
            "user_pool_id": test_user_pool.id
        }
        
        permission_response = client.post(
            "/api/v1/rbac/permissions",
            json=permission_data,
            headers=admin_auth_headers
        )
        assert permission_response.status_code == 200
        permission_id = permission_response.json()["data"]["id"]
        
        # 2. 创建角色
        role_data = {
            **TEST_ROLE_DATA,
            "user_pool_id": test_user_pool.id
        }
        
        role_response = client.post(
            "/api/v1/rbac/roles",
            json=role_data,
            headers=admin_auth_headers
        )
        assert role_response.status_code == 200
        role_id = role_response.json()["data"]["id"]
        
        # 3. 为角色分配权限
        assign_permission_data = {
            "permission_ids": [permission_id]
        }
        
        assign_response = client.post(
            f"/api/v1/rbac/roles/{role_id}/permissions",
            json=assign_permission_data,
            headers=admin_auth_headers
        )
        assert assign_response.status_code == 200
        
        # 4. 为用户分配角色
        assign_role_data = {
            "role_ids": [role_id]
        }
        
        user_role_response = client.post(
            f"/api/v1/rbac/users/{test_user.id}/roles",
            json=assign_role_data,
            headers=admin_auth_headers
        )
        assert user_role_response.status_code == 200
        
        # 5. 验证用户权限
        user_permissions_response = client.get(
            f"/api/v1/rbac/users/{test_user.id}/permissions",
            headers=admin_auth_headers
        )
        assert user_permissions_response.status_code == 200
        
        permissions = user_permissions_response.json()["data"]["items"]
        assert len(permissions) > 0
        assert permissions[0]["permission_code"] == TEST_PERMISSION_DATA["permission_code"]
        
        # 6. 移除用户角色
        remove_role_data = {
            "role_ids": [role_id]
        }
        
        remove_response = client.delete(
            f"/api/v1/rbac/users/{test_user.id}/roles",
            json=remove_role_data,
            headers=admin_auth_headers
        )
        assert remove_response.status_code == 200
        
        # 7. 验证权限已移除
        final_permissions_response = client.get(
            f"/api/v1/rbac/users/{test_user.id}/permissions",
            headers=admin_auth_headers
        )
        assert final_permissions_response.status_code == 200
        
        final_permissions = final_permissions_response.json()["data"]["items"]
        assert len(final_permissions) == 0
    
    def test_token_refresh_workflow(self, client: TestClient, test_user_pool: UserPool):
        """测试令牌刷新工作流程"""
        # 1. 登录获取令牌
        login_data = {
            "identifier": "testuser",
            "password": "testpassword123",
            "user_pool_id": test_user_pool.id
        }
        
        login_response = client.post("/api/v1/auth/login", json=login_data)
        assert login_response.status_code == 200
        
        tokens = login_response.json()["data"]
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        
        # 2. 使用access_token访问资源
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        profile_response = client.get("/api/v1/users/user-pools", headers=auth_headers)
        assert profile_response.status_code == 200
        
        # 3. 使用refresh_token刷新令牌
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = client.post("/api/v1/auth/refresh", json=refresh_data)
        assert refresh_response.status_code == 200
        
        new_tokens = refresh_response.json()["data"]
        new_access_token = new_tokens["access_token"]
        new_refresh_token = new_tokens["refresh_token"]
        
        # 4. 使用新的access_token访问资源
        new_auth_headers = {"Authorization": f"Bearer {new_access_token}"}
        new_profile_response = client.get("/api/v1/users/user-pools", headers=new_auth_headers)
        assert new_profile_response.status_code == 200
        
        # 5. 验证旧的refresh_token不能再使用
        old_refresh_data = {"refresh_token": refresh_token}
        old_refresh_response = client.post("/api/v1/auth/refresh", json=old_refresh_data)
        # 应该返回401或400，因为旧的refresh_token已经无效
        assert old_refresh_response.status_code in [400, 401]
    
    def test_multi_user_pool_isolation(self, client: TestClient, admin_auth_headers: dict):
        """测试多用户池隔离"""
        # 1. 创建两个用户池
        pool1_data = {
            "name": "用户池1",
            "description": "第一个用户池"
        }
        
        pool1_response = client.post(
            "/api/v1/users/user-pools",
            json=pool1_data,
            headers=admin_auth_headers
        )
        assert pool1_response.status_code == 200
        pool1_id = pool1_response.json()["data"]["id"]
        
        pool2_data = {
            "name": "用户池2",
            "description": "第二个用户池"
        }
        
        pool2_response = client.post(
            "/api/v1/users/user-pools",
            json=pool2_data,
            headers=admin_auth_headers
        )
        assert pool2_response.status_code == 200
        pool2_id = pool2_response.json()["data"]["id"]
        
        # 2. 在两个用户池中创建同名用户
        user1_data = {
            "username": "sameuser",
            "email": "user1@example.com",
            "password": "password123",
            "user_pool_id": pool1_id
        }
        
        user1_response = client.post(
            "/api/v1/users/users",
            json=user1_data,
            headers=admin_auth_headers
        )
        assert user1_response.status_code == 200
        
        user2_data = {
            "username": "sameuser",  # 同样的用户名
            "email": "user2@example.com",
            "password": "password123",
            "user_pool_id": pool2_id
        }
        
        user2_response = client.post(
            "/api/v1/users/users",
            json=user2_data,
            headers=admin_auth_headers
        )
        # 应该成功，因为在不同的用户池中
        assert user2_response.status_code == 200
        
        # 3. 验证两个用户可以分别在各自的用户池中登录
        login1_data = {
            "identifier": "sameuser",
            "password": "password123",
            "user_pool_id": pool1_id
        }
        
        login1_response = client.post("/api/v1/auth/login", json=login1_data)
        assert login1_response.status_code == 200
        
        login2_data = {
            "identifier": "sameuser",
            "password": "password123",
            "user_pool_id": pool2_id
        }
        
        login2_response = client.post("/api/v1/auth/login", json=login2_data)
        assert login2_response.status_code == 200
        
        # 4. 验证用户不能跨用户池登录
        cross_login_data = {
            "identifier": "sameuser",
            "password": "password123",
            "user_pool_id": pool2_id  # 尝试用pool1的用户在pool2中登录
        }
        
        # 这个测试可能需要根据具体实现调整
        # 如果系统允许同名用户在不同用户池，这里应该成功
        # 如果不允许，应该失败
    
    def test_error_handling_integration(self, client: TestClient, test_user_pool: UserPool):
        """测试错误处理集成"""
        # 1. 尝试使用无效的用户池ID注册
        invalid_register_data = {
            **TEST_USER_DATA,
            "user_pool_id": 99999  # 不存在的用户池ID
        }
        
        register_response = client.post("/api/v1/auth/register", json=invalid_register_data)
        assert register_response.status_code in [400, 404, 422]
        
        # 2. 尝试重复注册
        valid_register_data = {
            **TEST_USER_DATA,
            "user_pool_id": test_user_pool.id
        }
        
        # 第一次注册应该成功
        first_response = client.post("/api/v1/auth/register", json=valid_register_data)
        assert first_response.status_code == 200
        
        # 第二次注册同样的用户应该失败
        second_response = client.post("/api/v1/auth/register", json=valid_register_data)
        assert second_response.status_code == 422
        
        # 3. 尝试使用无效令牌访问资源
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        profile_response = client.get("/api/v1/users/user-pools", headers=invalid_headers)
        assert profile_response.status_code in [401, 403]
        
        # 4. 尝试访问不存在的资源
        auth_headers = {"Authorization": f"Bearer {first_response.json()['data']['access_token']}"}
        not_found_response = client.get("/api/v1/users/users/99999", headers=auth_headers)
        assert not_found_response.status_code == 404
