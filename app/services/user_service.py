"""
用户管理服务
"""
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.models import User, UserPool, Application, Credential, UserRole, Role
from app.models.user import UserStatus, UserPoolStatus, CredentialType
from app.core.security import security
from app.core.exceptions import NotFoundError, ValidationError, ConflictError
from app.schemas.user import UserListQuery


class UserService:
    """用户管理服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user_pool(
        self,
        name: str,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None
    ) -> UserPool:
        """创建用户池"""
        # 检查名称是否已存在
        existing = await self.db.execute(
            select(UserPool).where(UserPool.name == name)
        )
        if existing.scalar_one_or_none():
            raise ConflictError("用户池名称已存在")
        
        user_pool = UserPool(
            name=name,
            description=description,
            settings=settings or {},
            status=UserPoolStatus.ACTIVE
        )
        
        self.db.add(user_pool)
        await self.db.commit()
        await self.db.refresh(user_pool)
        
        return user_pool
    
    async def update_user_pool(
        self,
        user_pool_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        settings: Optional[Dict[str, Any]] = None,
        status: Optional[UserPoolStatus] = None
    ) -> UserPool:
        """更新用户池"""
        user_pool = await self.get_user_pool_by_id(user_pool_id)
        
        if name and name != user_pool.name:
            # 检查新名称是否已存在
            existing = await self.db.execute(
                select(UserPool).where(
                    and_(
                        UserPool.name == name,
                        UserPool.id != user_pool_id
                    )
                )
            )
            if existing.scalar_one_or_none():
                raise ConflictError("用户池名称已存在")
            user_pool.name = name
        
        if description is not None:
            user_pool.description = description
        
        if settings is not None:
            user_pool.settings = settings
        
        if status is not None:
            user_pool.status = status
        
        await self.db.commit()
        await self.db.refresh(user_pool)
        
        return user_pool
    
    async def get_user_pool_by_id(self, user_pool_id: int) -> UserPool:
        """根据ID获取用户池"""
        result = await self.db.execute(
            select(UserPool).where(UserPool.id == user_pool_id)
        )
        user_pool = result.scalar_one_or_none()
        
        if not user_pool:
            raise NotFoundError("用户池不存在")
        
        return user_pool
    
    async def list_user_pools(
        self,
        status: Optional[UserPoolStatus] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[UserPool], int]:
        """获取用户池列表"""
        query = select(UserPool)
        
        if status:
            query = query.where(UserPool.status == status)
        
        # 计算总数
        count_query = select(func.count(UserPool.id))
        if status:
            count_query = count_query.where(UserPool.status == status)
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        query = query.offset((page - 1) * per_page).limit(per_page)
        query = query.order_by(UserPool.created_at.desc())
        
        result = await self.db.execute(query)
        user_pools = result.scalars().all()
        
        return list(user_pools), total
    
    async def create_application(
        self,
        user_pool_id: int,
        app_name: str,
        callback_urls: Optional[List[str]] = None,
        logout_urls: Optional[List[str]] = None,
        allowed_origins: Optional[List[str]] = None,
        token_lifetime: int = 3600,
        refresh_token_lifetime: int = 2592000
    ) -> Application:
        """创建应用"""
        # 验证用户池存在
        await self.get_user_pool_by_id(user_pool_id)
        
        # 生成应用ID和密钥
        app_id = f"app_{security.generate_scene_id()[:16]}"
        app_secret = security.generate_app_secret()
        
        application = Application(
            user_pool_id=user_pool_id,
            app_name=app_name,
            app_id=app_id,
            app_secret=app_secret,
            callback_urls=callback_urls or [],
            logout_urls=logout_urls or [],
            allowed_origins=allowed_origins or [],
            token_lifetime=token_lifetime,
            refresh_token_lifetime=refresh_token_lifetime,
            status=UserPoolStatus.ACTIVE
        )
        
        self.db.add(application)
        await self.db.commit()
        await self.db.refresh(application)
        
        return application
    
    async def create_user(
        self,
        user_pool_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        password: Optional[str] = None,
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None,
        profile_data: Optional[Dict[str, Any]] = None,
        status: UserStatus = UserStatus.ACTIVE
    ) -> User:
        """创建用户"""
        # 验证用户池存在
        await self.get_user_pool_by_id(user_pool_id)
        
        # 检查用户标识唯一性
        if username:
            existing = await self._find_user_by_field(user_pool_id, "username", username)
            if existing:
                raise ConflictError("用户名已存在")
        
        if email:
            existing = await self._find_user_by_field(user_pool_id, "email", email)
            if existing:
                raise ConflictError("邮箱已被注册")
        
        if phone:
            existing = await self._find_user_by_field(user_pool_id, "phone", phone)
            if existing:
                raise ConflictError("手机号已被注册")
        
        # 创建用户
        user = User(
            user_pool_id=user_pool_id,
            username=username,
            email=email,
            phone=phone,
            nickname=nickname,
            avatar_url=avatar_url,
            profile_data=profile_data or {},
            status=status
        )
        
        self.db.add(user)
        await self.db.flush()  # 获取用户ID
        
        # 创建密码凭证
        if password:
            password_hash = security.get_password_hash(password)
            credential = Credential(
                user_id=user.id,
                type=CredentialType.PASSWORD,
                identifier=username or email or phone,
                credential=password_hash
            )
            self.db.add(credential)
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def update_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None,
        profile_data: Optional[Dict[str, Any]] = None,
        status: Optional[UserStatus] = None
    ) -> User:
        """更新用户"""
        user = await self.get_user_by_id(user_id)
        
        # 检查唯一性约束
        if username and username != user.username:
            existing = await self._find_user_by_field(user.user_pool_id, "username", username)
            if existing and existing.id != user_id:
                raise ConflictError("用户名已存在")
            user.username = username
        
        if email and email != user.email:
            existing = await self._find_user_by_field(user.user_pool_id, "email", email)
            if existing and existing.id != user_id:
                raise ConflictError("邮箱已被注册")
            user.email = email
            user.email_verified = False  # 重置验证状态
        
        if phone and phone != user.phone:
            existing = await self._find_user_by_field(user.user_pool_id, "phone", phone)
            if existing and existing.id != user_id:
                raise ConflictError("手机号已被注册")
            user.phone = phone
            user.phone_verified = False  # 重置验证状态
        
        if nickname is not None:
            user.nickname = nickname
        
        if avatar_url is not None:
            user.avatar_url = avatar_url
        
        if profile_data is not None:
            user.profile_data = profile_data
        
        if status is not None:
            user.status = status
        
        await self.db.commit()
        await self.db.refresh(user)
        
        return user
    
    async def get_user_by_id(self, user_id: int) -> User:
        """根据ID获取用户"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise NotFoundError("用户不存在")
        
        return user
    
    async def list_users(self, query_params: UserListQuery) -> Tuple[List[User], int]:
        """获取用户列表"""
        query = select(User).where(User.user_pool_id == query_params.user_pool_id)
        
        # 状态筛选
        if query_params.status:
            query = query.where(User.status == query_params.status)
        
        # 关键词搜索
        if query_params.keyword:
            keyword = f"%{query_params.keyword}%"
            query = query.where(
                or_(
                    User.username.like(keyword),
                    User.email.like(keyword),
                    User.phone.like(keyword),
                    User.nickname.like(keyword)
                )
            )
        
        # 计算总数
        count_query = select(func.count(User.id)).where(User.user_pool_id == query_params.user_pool_id)
        if query_params.status:
            count_query = count_query.where(User.status == query_params.status)
        if query_params.keyword:
            keyword = f"%{query_params.keyword}%"
            count_query = count_query.where(
                or_(
                    User.username.like(keyword),
                    User.email.like(keyword),
                    User.phone.like(keyword),
                    User.nickname.like(keyword)
                )
            )
        
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        query = query.offset((query_params.page - 1) * query_params.per_page).limit(query_params.per_page)
        query = query.order_by(User.created_at.desc())
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        return list(users), total
    
    async def delete_user(self, user_id: int) -> bool:
        """删除用户"""
        user = await self.get_user_by_id(user_id)
        
        # 软删除：将状态设置为禁用
        user.status = UserStatus.BLOCKED
        await self.db.commit()
        
        return True
    
    async def change_password(
        self,
        user_id: int,
        old_password: str,
        new_password: str
    ) -> bool:
        """修改密码"""
        user = await self.get_user_by_id(user_id)
        
        # 查找当前密码凭证
        result = await self.db.execute(
            select(Credential).where(
                and_(
                    Credential.user_id == user_id,
                    Credential.type == CredentialType.PASSWORD
                )
            )
        )
        credential = result.scalar_one_or_none()
        
        if not credential:
            raise ValidationError("用户未设置密码")
        
        # 验证旧密码
        if not security.verify_password(old_password, credential.credential):
            raise ValidationError("原密码错误")
        
        # 更新密码
        credential.credential = security.get_password_hash(new_password)
        await self.db.commit()
        
        return True
    
    async def reset_password(
        self,
        user_id: int,
        new_password: str
    ) -> bool:
        """重置密码（管理员操作）"""
        user = await self.get_user_by_id(user_id)
        
        # 查找或创建密码凭证
        result = await self.db.execute(
            select(Credential).where(
                and_(
                    Credential.user_id == user_id,
                    Credential.type == CredentialType.PASSWORD
                )
            )
        )
        credential = result.scalar_one_or_none()
        
        if credential:
            credential.credential = security.get_password_hash(new_password)
        else:
            credential = Credential(
                user_id=user_id,
                type=CredentialType.PASSWORD,
                identifier=user.username or user.email or user.phone,
                credential=security.get_password_hash(new_password)
            )
            self.db.add(credential)
        
        await self.db.commit()
        return True
    
    async def _find_user_by_field(
        self,
        user_pool_id: int,
        field: str,
        value: str
    ) -> Optional[User]:
        """根据字段查找用户"""
        if field == "username":
            condition = User.username == value
        elif field == "email":
            condition = User.email == value
        elif field == "phone":
            condition = User.phone == value
        else:
            return None
        
        result = await self.db.execute(
            select(User).where(
                and_(
                    User.user_pool_id == user_pool_id,
                    condition
                )
            )
        )
        return result.scalar_one_or_none()
