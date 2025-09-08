"""
认证服务
"""
import secrets
from datetime import datetime, timedelta, UTC
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models import User, Credential, OTPCode, QRLoginSession, AuditLog
from app.models.user import CredentialType, UserStatus
from app.models.auth import OTPType, QRLoginStatus
from app.core.security import security, jwt_utils
from app.core.exceptions import AuthError, OTPError, NotFoundError, ValidationError
from app.schemas.auth import TokenResponse
from app.schemas.user import UserResponse
from app.config import settings


class AuthService:
    """认证服务类"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def authenticate_user(
        self, 
        identifier: str, 
        password: str, 
        user_pool_id: int
    ) -> Optional[User]:
        """用户名密码认证"""
        # 查找用户
        user = await self._find_user_by_identifier(identifier, user_pool_id)
        if not user:
            return None
        
        # 查找密码凭证
        result = await self.db.execute(
            select(Credential).where(
                and_(
                    Credential.user_id == user.id,
                    Credential.type == CredentialType.PASSWORD
                )
            )
        )
        credential = result.scalar_one_or_none()
        
        if not credential:
            return None
        
        # 验证密码
        if not security.verify_password(password, credential.credential):
            return None
        
        return user
    
    async def create_user_tokens(self, user: User) -> TokenResponse:
        """创建用户令牌"""
        # 更新最后登录时间
        user.last_login_at = datetime.now(UTC)
        await self.db.commit()
        
        # 创建访问令牌和刷新令牌
        access_token = jwt_utils.create_access_token(str(user.id))
        refresh_token = jwt_utils.create_refresh_token(str(user.id))
        
        # 创建用户响应信息
        user_response = UserResponse(
            id=user.id,
            user_pool_id=user.user_pool_id,
            username=user.username,
            email=user.email,
            phone=user.phone,
            nickname=user.nickname,
            avatar_url=user.avatar_url,
            profile_data=user.profile_data or {},
            email_verified=user.email_verified,
            phone_verified=user.phone_verified,
            status=user.status,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.access_token_expire_minutes * 60,
            user=user_response
        )
    
    async def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """刷新访问令牌"""
        # 验证刷新令牌
        payload = jwt_utils.verify_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthError("无效的刷新令牌")
        
        user_id = payload.get("sub")
        if not user_id:
            raise AuthError("令牌格式错误")
        
        # 查找用户
        result = await self.db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        
        if not user or user.status != UserStatus.ACTIVE:
            raise AuthError("用户不存在或已被禁用")
        
        return await self.create_user_tokens(user)
    
    async def register_user(
        self,
        user_pool_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        password: str = None,
        nickname: Optional[str] = None,
        **kwargs
    ) -> User:
        """注册用户"""
        # 检查用户标识唯一性
        if username:
            existing = await self._find_user_by_identifier(username, user_pool_id)
            if existing:
                raise ValidationError("用户名已存在")
        
        if email:
            existing = await self._find_user_by_identifier(email, user_pool_id)
            if existing:
                raise ValidationError("邮箱已被注册")
        
        if phone:
            existing = await self._find_user_by_identifier(phone, user_pool_id)
            if existing:
                raise ValidationError("手机号已被注册")
        
        # 创建用户
        user = User(
            user_pool_id=user_pool_id,
            username=username,
            email=email,
            phone=phone,
            nickname=nickname or username,
            status=UserStatus.ACTIVE,
            **kwargs
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
        return user
    
    async def send_otp_code(
        self,
        identifier: str,
        otp_type: OTPType,
        user_pool_id: int
    ) -> bool:
        """发送验证码"""
        # 检查是否存在未过期的验证码
        existing_result = await self.db.execute(
            select(OTPCode).where(
                and_(
                    OTPCode.identifier == identifier,
                    OTPCode.type == otp_type,
                    OTPCode.expires_at > datetime.now(UTC),
                    OTPCode.used == False
                )
            )
        )
        existing_otp = existing_result.scalar_one_or_none()
        
        if existing_otp:
            # 检查是否在冷却期内（1分钟）
            # 处理时区兼容性：如果existing_otp.created_at是无时区的，将其转换为UTC
            created_at = existing_otp.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=UTC)
            time_since_created = datetime.now(UTC) - created_at
            if time_since_created.total_seconds() < 60:
                raise OTPError("验证码发送过于频繁，请稍后再试")
        
        # 生成验证码
        code = security.generate_otp_code()
        code_hash, salt = security.hash_otp_code(code)
        
        # 保存验证码
        otp = OTPCode(
            identifier=identifier,
            code_hash=code_hash,
            type=otp_type,
            expires_at=datetime.now(UTC) + timedelta(minutes=settings.otp_expire_minutes)
        )
        
        self.db.add(otp)
        await self.db.commit()
        
        # TODO: 实际发送验证码（短信/邮件）
        # 开发环境下可以打印到日志
        print(f"验证码发送到 {identifier}: {code}")
        
        return True
    
    async def verify_otp_login(
        self,
        identifier: str,
        code: str,
        user_pool_id: int
    ) -> User:
        """验证码登录"""
        # 查找有效的验证码
        result = await self.db.execute(
            select(OTPCode).where(
                and_(
                    OTPCode.identifier == identifier,
                    OTPCode.type == OTPType.LOGIN,
                    OTPCode.expires_at > datetime.now(UTC),
                    OTPCode.used == False
                )
            ).order_by(OTPCode.created_at.desc())
        )
        otp = result.scalar_one_or_none()
        
        if not otp:
            raise OTPError("验证码不存在或已过期")
        
        # 检查尝试次数
        if otp.attempts >= otp.max_attempts:
            raise OTPError("验证码尝试次数过多")
        
        # 验证验证码
        # 注意：这里简化处理，实际应该从数据库获取salt
        is_valid = security.verify_otp_code(code, otp.code_hash, "")
        
        # 增加尝试次数
        otp.attempts += 1
        
        if not is_valid:
            await self.db.commit()
            remaining = otp.max_attempts - otp.attempts
            raise OTPError(f"验证码错误，还可尝试 {remaining} 次")
        
        # 标记验证码为已使用
        otp.used = True
        await self.db.commit()
        
        # 查找或创建用户
        user = await self._find_user_by_identifier(identifier, user_pool_id)
        if not user:
            # 自动注册用户
            if "@" in identifier:
                user = await self.register_user(
                    user_pool_id=user_pool_id,
                    email=identifier,
                    nickname=identifier.split("@")[0]
                )
            else:
                user = await self.register_user(
                    user_pool_id=user_pool_id,
                    phone=identifier,
                    nickname=f"用户{identifier[-4:]}"
                )
        
        return user
    
    async def create_qr_login_session(
        self,
        user_pool_id: int,
        app_id: str
    ) -> QRLoginSession:
        """创建扫码登录会话"""
        scene_id = security.generate_scene_id()
        
        session = QRLoginSession(
            scene_id=scene_id,
            user_pool_id=user_pool_id,
            app_id=app_id,
            status=QRLoginStatus.PENDING,
            expires_at=datetime.now(UTC) + timedelta(minutes=settings.qr_login_expire_minutes)
        )
        
        self.db.add(session)
        await self.db.commit()
        
        return session
    
    async def get_qr_login_status(self, scene_id: str) -> Optional[QRLoginSession]:
        """获取扫码登录状态"""
        result = await self.db.execute(
            select(QRLoginSession).where(QRLoginSession.scene_id == scene_id)
        )
        return result.scalar_one_or_none()
    
    async def confirm_qr_login(
        self,
        scene_id: str,
        user: User,
        confirm: bool = True
    ) -> QRLoginSession:
        """确认扫码登录"""
        session = await self.get_qr_login_status(scene_id)
        if not session:
            raise NotFoundError("扫码会话不存在")
        
        if session.expires_at <= datetime.now(UTC):
            session.status = QRLoginStatus.EXPIRED
            await self.db.commit()
            raise OTPError("扫码会话已过期")
        
        if session.status != QRLoginStatus.PENDING:
            raise OTPError("扫码会话状态无效")
        
        # 检查用户池权限
        if user.user_pool_id != session.user_pool_id:
            raise AuthError("无权确认此扫码登录")
        
        if confirm:
            session.status = QRLoginStatus.CONFIRMED
            session.user_id = user.id
            session.confirmed_at = datetime.now(UTC)
            
            # 更新用户最后登录时间
            user.last_login_at = datetime.now(UTC)
        else:
            session.status = QRLoginStatus.CANCELLED
        
        await self.db.commit()
        return session
    
    async def _find_user_by_identifier(
        self,
        identifier: str,
        user_pool_id: int
    ) -> Optional[User]:
        """根据标识符查找用户"""
        result = await self.db.execute(
            select(User).where(
                and_(
                    User.user_pool_id == user_pool_id,
                    or_(
                        User.username == identifier,
                        User.email == identifier,
                        User.phone == identifier
                    )
                )
            )
        )
        return result.scalar_one_or_none()
    
    async def log_audit(
        self,
        user_pool_id: int,
        action: str,
        user_id: Optional[int] = None,
        resource: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """记录审计日志"""
        import json
        
        # 将details字典转换为JSON字符串
        details_str = None
        if details:
            details_str = json.dumps(details, ensure_ascii=False)
        
        audit_log = AuditLog(
            user_pool_id=user_pool_id,
            user_id=user_id,
            action=action,
            resource=resource,
            resource_id=resource_id,
            details=details_str,
            success=success,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        self.db.add(audit_log)
        await self.db.commit()
