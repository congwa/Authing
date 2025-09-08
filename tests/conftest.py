"""
最终的测试架构 - 彻底解决数据库隔离问题
核心策略：
1. 使用单一数据库连接和会话
2. 每个测试函数前后清理数据
3. 同步创建测试数据确保可见性
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


# 向后兼容 - 测试数据常量
TEST_USER_DATA = {
    "username": "testuser",
    "email": "testuser@example.com",
    "phone": "13812345678",
    "nickname": "测试用户",
    "password": "testpassword123"
}

TEST_USER_POOL_DATA = {
    "name": "测试用户池",
    "description": "用于测试的用户池",
    "settings": {}
}

TEST_ROLE_DATA = {
    "code": "test_role",
    "name": "测试角色",
    "description": "用于测试的角色"
}

TEST_PERMISSION_DATA = {
    "code": "test_permission",
    "name": "测试权限",
    "description": "用于测试的权限",
    "resource": "test_resource",
    "action": "read"
}


# 全局测试引擎和会话 - 确保所有测试使用同一连接
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    echo=False,
    future=True,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False}
)

TestSessionMaker = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# 向后兼容性别名
TestAsyncSessionLocal = TestSessionMaker

# 全局会话实例
_test_session = None


async def get_test_session():
    """获取测试会话"""
    global _test_session
    if _test_session is None:
        _test_session = TestSessionMaker()
    return _test_session


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_env():
    """设置测试环境"""
    # 创建所有表
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield
    
    # 清理
    global _test_session
    if _test_session:
        await _test_session.close()
    
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def clean_db():
    """清理数据库 - 每个测试前执行"""
    session = await get_test_session()
    
    # 删除所有数据，保留表结构
    from sqlalchemy import text
    tables = [
        "user_role_assignments",
        "role_permission_assignments", 
        "credentials",
        "users",
        "permissions",
        "roles",
        "applications",
        "user_pools"
    ]
    
    for table in tables:
        try:
            await session.execute(text(f"DELETE FROM {table}"))
        except Exception:
            # 表可能不存在，忽略错误
            pass
    
    await session.commit()


@pytest_asyncio.fixture(scope="function")
async def db_session(clean_db) -> AsyncGenerator[AsyncSession, None]:
    """提供数据库会话"""
    session = await get_test_session()
    yield session


@pytest.fixture(scope="function")
def client() -> Generator[TestClient, None, None]:
    """测试客户端"""
    async def get_test_db():
        session = await get_test_session()
        yield session
    
    # 同时覆盖两个依赖项
    from app.db.database import get_db_session
    from app.api.deps import get_db
    
    app.dependency_overrides[get_db_session] = get_test_db
    app.dependency_overrides[get_db] = get_test_db
    
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


# 同步测试数据创建工具
class SyncTestDataCreator:
    """同步测试数据创建器 - 确保数据立即可见"""
    
    @staticmethod
    async def create_user_pool(session: AsyncSession, **kwargs) -> UserPool:
        """创建用户池"""
        data = {
            "name": "测试用户池",
            "description": "用于测试的用户池",
            "settings": {},
            "status": UserPoolStatus.ACTIVE,
            **kwargs
        }
        user_pool = UserPool(**data)
        session.add(user_pool)
        await session.commit()
        await session.refresh(user_pool)
        return user_pool
    
    @staticmethod
    async def create_user_with_credentials(session: AsyncSession, user_pool_id: int, 
                                         username: str = "testuser", 
                                         password: str = "testpassword123", **kwargs) -> User:
        """创建用户和凭证"""
        # 创建用户
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
        session.add(user)
        await session.flush()  # 获取ID
        await session.refresh(user)
        
        # 创建密码凭证
        password_hash = security.get_password_hash(password)
        credential = Credential(
            user_id=user.id,
            type=CredentialType.PASSWORD,
            identifier=username,
            credential=password_hash
        )
        session.add(credential)
        
        # 提交所有更改
        await session.commit()
        await session.refresh(user)
        
        return user


@pytest.fixture
def sync_data_creator():
    """同步数据创建器fixture"""
    return SyncTestDataCreator


# 简化的登录助手
@pytest.fixture
def login_helper(client: TestClient):
    """登录助手"""
    def do_login(username: str, password: str, user_pool_id: int) -> dict:
        """执行登录"""
        login_data = {
            "identifier": username,
            "password": password,
            "user_pool_id": user_pool_id
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        if response.status_code != 200:
            raise AssertionError(f"登录失败 {response.status_code}: {response.json()}")
        
        response_data = response.json()
        token_data = response_data["data"]
        return {
            "Authorization": f"Bearer {token_data['access_token']}",
            "token_data": token_data
        }
    
    return do_login


# 向后兼容的传统fixtures
@pytest_asyncio.fixture
async def test_user_pool(db_session: AsyncSession, sync_data_creator: SyncTestDataCreator) -> UserPool:
    """测试用户池fixture - 向后兼容"""
    return await sync_data_creator.create_user_pool(db_session, **TEST_USER_POOL_DATA)


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession, test_user_pool: UserPool, sync_data_creator: SyncTestDataCreator) -> User:
    """测试用户fixture - 向后兼容"""
    return await sync_data_creator.create_user_with_credentials(
        db_session,
        user_pool_id=test_user_pool.id,
        **TEST_USER_DATA
    )


@pytest_asyncio.fixture
async def test_role(db_session: AsyncSession, test_user_pool: UserPool) -> Role:
    """测试角色fixture - 向后兼容"""
    session = await get_test_session()
    role = Role(
        user_pool_id=test_user_pool.id,
        **TEST_ROLE_DATA
    )
    session.add(role)
    await session.commit()
    await session.refresh(role)
    return role


@pytest_asyncio.fixture
async def test_permission(db_session: AsyncSession, test_user_pool: UserPool) -> Permission:
    """测试权限fixture - 向后兼容"""
    session = await get_test_session()
    permission = Permission(
        user_pool_id=test_user_pool.id,
        **TEST_PERMISSION_DATA
    )
    session.add(permission)
    await session.commit()
    await session.refresh(permission)
    return permission


@pytest_asyncio.fixture
async def test_admin_user(db_session: AsyncSession, test_user_pool: UserPool, sync_data_creator: SyncTestDataCreator) -> User:
    """测试管理员用户fixture - 向后兼容"""
    return await sync_data_creator.create_user_with_credentials(
        db_session,
        user_pool_id=test_user_pool.id,
        username="admin",
        email="admin@example.com",
        nickname="管理员",
        password="adminpassword123"
    )


@pytest.fixture
def auth_headers(client: TestClient, login_helper) -> dict:
    """认证头fixture - 向后兼容"""
    import asyncio
    
    async def setup_auth():
        from tests.conftest import get_test_session, SyncTestDataCreator
        
        session = await get_test_session()
        creator = SyncTestDataCreator()
        
        user_pool = await creator.create_user_pool(session)
        await creator.create_user_with_credentials(
            session,
            user_pool_id=user_pool.id,
            username="authuser",
            password="authpassword123"
        )
        
        auth_data = login_helper("authuser", "authpassword123", user_pool.id)
        return {"Authorization": auth_data["Authorization"]}
    
    return asyncio.run(setup_auth())
