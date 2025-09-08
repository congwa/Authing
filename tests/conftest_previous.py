"""
全新的测试配置架构 - 解决数据库隔离问题
核心思路：
1. 使用全局数据库连接池
2. 每个测试自己管理测试数据
3. 简化fixture依赖关系
"""
import asyncio
import pytest
import pytest_asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.main import app
from app.db.database import get_db_session
from app.models import User, UserPool, Role, Permission, Credential
from app.models.user import UserStatus, UserPoolStatus, CredentialType
from app.core.security import security

# 全局测试数据库引擎 - 使用单连接池确保数据一致性
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    future=True,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
        "isolation_level": None,  # 禁用SQLite事务隔离
    }
)

# 全局会话工厂
TestSessionMaker = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 全局测试会话 - 所有测试共享
_global_test_session = None


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_database():
    """全局数据库设置 - session级别，自动执行"""
    global _global_test_session
    
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    # 创建全局会话
    _global_test_session = TestSessionMaker()
    
    yield
    
    # 清理
    if _global_test_session:
        await _global_test_session.close()
    
    # 删除所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def clean_database():
    """每个测试开始前清理数据库"""
    global _global_test_session
    
    if _global_test_session:
        from sqlalchemy import text
        
        # 清理所有表数据，但保留表结构
        try:
            await _global_test_session.execute(text("DELETE FROM user_role_assignments"))
        except:
            pass
        try:
            await _global_test_session.execute(text("DELETE FROM role_permission_assignments"))
        except:
            pass
        try:
            await _global_test_session.execute(text("DELETE FROM credentials"))
        except:
            pass
        try:
            await _global_test_session.execute(text("DELETE FROM users"))
        except:
            pass
        try:
            await _global_test_session.execute(text("DELETE FROM permissions"))
        except:
            pass
        try:
            await _global_test_session.execute(text("DELETE FROM roles"))
        except:
            pass
        try:
            await _global_test_session.execute(text("DELETE FROM applications"))
        except:
            pass
        try:
            await _global_test_session.execute(text("DELETE FROM user_pools"))
        except:
            pass
        await _global_test_session.commit()


@pytest_asyncio.fixture(scope="function")
async def db_session(clean_database) -> AsyncGenerator[AsyncSession, None]:
    """提供数据库会话 - 直接返回全局会话"""
    global _global_test_session
    yield _global_test_session


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """测试客户端 - 使用全局会话"""
    def get_test_db():
        # 返回全局会话的生成器
        yield _global_test_session
    
    app.dependency_overrides[get_db_session] = get_test_db
    
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


class TestDataFactory:
    """测试数据工厂 - 统一创建测试数据"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create_user_pool(self, **kwargs) -> UserPool:
        """创建测试用户池"""
        data = {
            "name": "测试用户池",
            "description": "用于测试的用户池",
            "settings": {},
            "status": UserPoolStatus.ACTIVE,
            **kwargs
        }
        user_pool = UserPool(**data)
        self.session.add(user_pool)
        await self.session.commit()
        await self.session.refresh(user_pool)
        return user_pool
    
    async def create_user(self, user_pool_id: int, username: str = "testuser", 
                         password: str = "testpassword123", **kwargs) -> User:
        """创建测试用户（包含凭证）"""
        user_data = {
            "user_pool_id": user_pool_id,
            "username": username,
            "email": f"{username}@example.com",
            "phone": "13812345678",
            "nickname": f"{username}昵称",
            "status": UserStatus.ACTIVE,
            **kwargs
        }
        
        user = User(**user_data)
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        
        # 创建密码凭证
        password_hash = security.get_password_hash(password)
        credential = Credential(
            user_id=user.id,
            type=CredentialType.PASSWORD,
            identifier=username,
            credential=password_hash
        )
        self.session.add(credential)
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
    
    async def create_role(self, user_pool_id: int, **kwargs) -> Role:
        """创建测试角色"""
        import uuid
        data = {
            "user_pool_id": user_pool_id,
            "role_name": "测试角色",
            "role_code": f"test_role_{str(uuid.uuid4())[:8]}",
            "description": "用于测试的角色",
            **kwargs
        }
        role = Role(**data)
        self.session.add(role)
        await self.session.commit()
        await self.session.refresh(role)
        return role
    
    async def create_permission(self, user_pool_id: int, **kwargs) -> Permission:
        """创建测试权限"""
        import uuid
        data = {
            "user_pool_id": user_pool_id,
            "permission_name": "测试权限",
            "permission_code": f"test_perm_{str(uuid.uuid4())[:8]}",
            "resource": "test",
            "action": "read", 
            "description": "用于测试的权限",
            **kwargs
        }
        permission = Permission(**data)
        self.session.add(permission)
        await self.session.commit()
        await self.session.refresh(permission)
        return permission


@pytest_asyncio.fixture(scope="function")
async def data_factory(db_session: AsyncSession) -> TestDataFactory:
    """测试数据工厂fixture"""
    return TestDataFactory(db_session)


@pytest.fixture(scope="function")
def login_user(client: TestClient, data_factory: TestDataFactory):
    """登录用户的辅助函数"""
    async def _login(username: str = "testuser", password: str = "testpassword123", 
                    user_pool_id: int = None) -> dict:
        """执行登录并返回认证头"""
        # 如果没有提供user_pool_id，创建一个默认的
        if user_pool_id is None:
            user_pool = await data_factory.create_user_pool()
            user_pool_id = user_pool.id
            await data_factory.create_user(user_pool_id, username, password)
        
        # 执行登录
        login_data = {
            "identifier": username,
            "password": password,
            "user_pool_id": user_pool_id
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        if response.status_code != 200:
            raise AssertionError(f"登录失败: {response.json()}")
        
        token_data = response.json()
        access_token = token_data["access_token"]
        
        return {
            "Authorization": f"Bearer {access_token}",
            "user_pool_id": user_pool_id,
            "token_data": token_data
        }
    
    return _login
