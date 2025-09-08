"""
pytest配置文件 - 异步模式+正确的事务隔离
"""
import asyncio
import pytest
import pytest_asyncio
from typing import Generator, AsyncGenerator
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.main import app
from app.db.database import get_db_session
from app.models import User, UserPool, Role, Permission, Credential
from app.models.user import UserStatus, UserPoolStatus, CredentialType
from app.core.security import security

# 测试数据库引擎 - 使用内存数据库，强制单连接
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    future=True,
    poolclass=StaticPool,
    pool_pre_ping=True,
    pool_recycle=-1,
    connect_args={
        "check_same_thread": False,
        "isolation_level": None,  # 禁用事务隔离
    }
)

# 创建异步测试会话工厂
TestAsyncSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# 移除自定义event_loop fixture，使用pytest-asyncio的默认配置


@pytest_asyncio.fixture(scope="session")
async def setup_database():
    """设置测试数据库 - session级别"""
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    # session结束时清理
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """为每个测试函数提供一个异步数据库会话。"""
    async with TestAsyncSessionLocal() as session:
        yield session


@pytest.fixture(scope="function")
def client(setup_database) -> Generator[TestClient, None, None]:
    """创建测试客户端"""
    def get_test_db():
        # 使用相同的sessionmaker
        session = TestAsyncSessionLocal()
        try:
            yield session
        finally:
            pass
    
    app.dependency_overrides[get_db_session] = get_test_db
    
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def test_user_pool(setup_database) -> UserPool:
    """创建测试用户池 - 使用独立会话提交"""
    async with TestAsyncSessionLocal() as session:
        user_pool = UserPool(
            name="测试用户池",
            description="用于测试的用户池",
            settings={},
            status=UserPoolStatus.ACTIVE
        )
        session.add(user_pool)
        await session.commit()  # 必须提交
        await session.refresh(user_pool)
        return user_pool


@pytest_asyncio.fixture
async def test_user(test_user_pool: UserPool) -> User:
    """创建测试用户 - 使用独立会话提交"""
    async with TestAsyncSessionLocal() as session:
        user = User(
            user_pool_id=test_user_pool.id,
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
        await session.commit()  # 必须提交
        await session.refresh(user)
        return user


@pytest_asyncio.fixture
async def test_admin_user(test_user_pool: UserPool) -> User:
    """创建测试管理员用户 - 使用独立会话提交"""
    async with TestAsyncSessionLocal() as session:
        user = User(
            user_pool_id=test_user_pool.id,
            username="admin",
            email="admin@example.com",
            nickname="管理员",
            status=UserStatus.ACTIVE
        )
        session.add(user)
        await session.flush()
        await session.refresh(user)
        
        # 创建密码凭证
        password_hash = security.get_password_hash("adminpassword123")
        credential = Credential(
            user_id=user.id,
            type=CredentialType.PASSWORD,
            identifier="admin",
            credential=password_hash
        )
        session.add(credential)
        await session.commit()  # 必须提交
        await session.refresh(user)
        return user


@pytest_asyncio.fixture(scope="function")
async def test_role(test_user_pool: UserPool) -> Role:
    """创建测试角色 - 使用独立会话提交"""
    import uuid
    async with TestAsyncSessionLocal() as session:
        unique_code = f"test_role_{str(uuid.uuid4())[:8]}"
        role = Role(
            user_pool_id=test_user_pool.id,
            role_name="测试角色",
            role_code=unique_code,
            description="用于测试的角色"
        )
        session.add(role)
        await session.commit()
        await session.refresh(role)
        return role


@pytest_asyncio.fixture(scope="function")
async def test_permission(test_user_pool: UserPool) -> Permission:
    """创建测试权限 - 使用独立会话提交"""
    import uuid
    async with TestAsyncSessionLocal() as session:
        unique_code = f"test_permission_{str(uuid.uuid4())[:8]}"
        permission = Permission(
            user_pool_id=test_user_pool.id,
            permission_name="测试权限",
            permission_code=unique_code,
            resource="test",
            action="read",
            description="用于测试的权限"
        )
        session.add(permission)
        await session.commit()
        await session.refresh(permission)
        return permission


@pytest.fixture
def auth_headers(client: TestClient, test_user: User, test_user_pool: UserPool) -> dict:
    """获取认证头"""
    # 登录获取token
    login_data = {
        "identifier": "testuser",
        "password": "testpassword123",
        "user_pool_id": test_user_pool.id
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"登录失败。响应: {response.text}")
        print(f"登录数据: {login_data}")
        print(f"用户池ID: {test_user_pool.id}")
        print(f"用户ID: {test_user.id}")
    
    assert response.status_code == 200, f"登录失败。响应: {response.text}"
    
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client: TestClient, test_admin_user: User, test_user_pool: UserPool) -> dict:
    """获取管理员认证头"""
    # 登录获取token
    login_data = {
        "identifier": "admin",
        "password": "adminpassword123",
        "user_pool_id": test_user_pool.id
    }
    
    response = client.post("/api/v1/auth/login", json=login_data)
    if response.status_code != 200:
        print(f"管理员登录失败。响应: {response.text}")
        print(f"登录数据: {login_data}")
    
    assert response.status_code == 200, f"管理员登录失败。响应: {response.text}"
    
    token = response.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


# 测试数据常量
TEST_USER_DATA = {
    "username": "newuser",
    "email": "newuser@example.com",
    "password": "newpassword123",
    "nickname": "新用户"
}

TEST_USER_POOL_DATA = {
    "name": "新用户池",
    "description": "新创建的用户池",
    "settings": {"theme": "default"}
}

TEST_ROLE_DATA = {
    "role_name": "新角色",
    "role_code": "new_role",
    "description": "新创建的角色"
}

TEST_PERMISSION_DATA = {
    "permission_name": "新权限",
    "permission_code": "new:write",
    "resource": "new",
    "action": "write",
    "description": "新创建的权限"
}
