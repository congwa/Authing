"""
认证相关API接口
"""
from fastapi import APIRouter, Depends, Request, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_auth_service
from app.core.dependencies import get_current_user, login_rate_limit, otp_rate_limit
from app.schemas.auth import (
    LoginRequest, OTPLoginRequest, SendOTPRequest, RegisterRequest,
    TokenResponse, RefreshTokenRequest, QRLoginCreateResponse,
    QRLoginStatusResponse, QRLoginConfirmRequest, ResetPasswordRequest
)
from app.schemas.common import ResponseModel
from app.services.auth_service import AuthService
from app.models import User
from app.models.auth import OTPType
from app.core.exceptions import AuthError, OTPError, ValidationError
import structlog

logger = structlog.get_logger()

router = APIRouter()


@router.post("/login", response_model=ResponseModel[TokenResponse])
async def login(
    request: Request,
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    _: bool = Depends(login_rate_limit)
):
    """用户名密码登录"""
    try:
        # 认证用户
        user = await auth_service.authenticate_user(
            identifier=login_data.identifier,
            password=login_data.password,
            user_pool_id=login_data.user_pool_id
        )
        
        if not user:
            await auth_service.log_audit(
                user_pool_id=login_data.user_pool_id,
                user_id=None,
                action="login_failed",
                details={"identifier": login_data.identifier, "reason": "invalid_credentials"},
                success=False,
                ip_address=request.client.host,
                user_agent=request.headers.get("user-agent")
            )
            raise AuthError("用户名或密码错误")
        
        # 生成令牌
        tokens = await auth_service.create_user_tokens(user)
        
        # 记录审计日志
        await auth_service.log_audit(
            user_pool_id=login_data.user_pool_id,
            user_id=user.id,
            action="login_success",
            details={"identifier": login_data.identifier, "method": "password"},
            success=True,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return ResponseModel(data=tokens, message="登录成功")
        
    except Exception as e:
        logger.error("登录失败", error=str(e), identifier=login_data.identifier)
        raise


@router.post("/otp/send", response_model=ResponseModel[bool])
async def send_otp(
    request: Request,
    otp_data: SendOTPRequest,
    auth_service: AuthService = Depends(get_auth_service),
    _: bool = Depends(otp_rate_limit)
):
    """发送验证码"""
    try:
        result = await auth_service.send_otp_code(
            identifier=otp_data.identifier,
            otp_type=otp_data.type,
            user_pool_id=otp_data.user_pool_id
        )
        
        return ResponseModel(data=result, message="验证码发送成功")
        
    except Exception as e:
        logger.error("发送验证码失败", error=str(e))
        raise


@router.post("/otp/login", response_model=ResponseModel[TokenResponse])
async def otp_login(
    request: Request,
    otp_data: OTPLoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    _: bool = Depends(login_rate_limit)
):
    """验证码登录"""
    try:
        # 验证码登录
        user = await auth_service.verify_otp_login(
            identifier=otp_data.identifier,
            code=otp_data.code,
            user_pool_id=otp_data.user_pool_id
        )
        
        # 生成令牌
        tokens = await auth_service.create_user_tokens(user)
        
        # 记录审计日志
        await auth_service.log_audit(
            user_pool_id=otp_data.user_pool_id,
            user_id=user.id,
            action="login_success",
            details={"identifier": otp_data.identifier, "method": "otp"},
            success=True,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return ResponseModel(data=tokens, message="登录成功")
        
    except Exception as e:
        logger.error("验证码登录失败", error=str(e))
        raise


@router.post("/register", response_model=ResponseModel[TokenResponse])
async def register(
    request: Request,
    register_data: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """用户注册"""
    try:
        # 注册用户
        user = await auth_service.register_user(
            user_pool_id=register_data.user_pool_id,
            username=register_data.username,
            email=register_data.email,
            phone=register_data.phone,
            password=register_data.password,
            nickname=register_data.nickname
        )
        
        # 生成令牌
        tokens = await auth_service.create_user_tokens(user)
        
        # 记录审计日志
        await auth_service.log_audit(
            user_pool_id=register_data.user_pool_id,
            user_id=user.id,
            action="user_register",
            details={"username": register_data.username, "email": register_data.email},
            success=True,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return ResponseModel(data=tokens, message="注册成功")
        
    except Exception as e:
        logger.error("用户注册失败", error=str(e))
        raise


@router.post("/refresh", response_model=ResponseModel[TokenResponse])
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """刷新访问令牌"""
    try:
        tokens = await auth_service.refresh_access_token(refresh_data.refresh_token)
        return ResponseModel(data=tokens, message="令牌刷新成功")
        
    except Exception as e:
        logger.error("刷新令牌失败", error=str(e))
        raise


@router.post("/logout", response_model=ResponseModel[bool])
async def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """用户登出"""
    try:
        # 记录审计日志
        await auth_service.log_audit(
            user_pool_id=current_user.user_pool_id,
            user_id=current_user.id,
            action="logout",
            success=True,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        # TODO: 实现令牌黑名单功能
        return ResponseModel(data=True, message="登出成功")
        
    except Exception as e:
        logger.error("登出失败", error=str(e))
        raise


@router.post("/qr/create", response_model=ResponseModel[QRLoginCreateResponse])
async def create_qr_login(
    user_pool_id: int,
    app_id: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """创建扫码登录会话"""
    try:
        session = await auth_service.create_qr_login_session(
            user_pool_id=user_pool_id,
            app_id=app_id
        )
        
        # 生成二维码URL（这里简化处理）
        qr_code_url = f"/qr/{session.scene_id}"
        
        response_data = QRLoginCreateResponse(
            scene_id=session.scene_id,
            qr_code_url=qr_code_url,
            expires_at=session.expires_at
        )
        
        return ResponseModel(data=response_data, message="扫码会话创建成功")
        
    except Exception as e:
        logger.error("创建扫码登录失败", error=str(e))
        raise


@router.get("/qr/{scene_id}/status", response_model=ResponseModel[QRLoginStatusResponse])
async def get_qr_login_status(
    scene_id: str,
    auth_service: AuthService = Depends(get_auth_service)
):
    """获取扫码登录状态"""
    try:
        session = await auth_service.get_qr_login_status(scene_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="扫码会话不存在"
            )
        
        response_data = QRLoginStatusResponse(
            scene_id=session.scene_id,
            status=session.status,
            user_id=session.user_id,
            expires_at=session.expires_at
        )
        
        return ResponseModel(data=response_data)
        
    except Exception as e:
        logger.error("获取扫码状态失败", error=str(e))
        raise


@router.post("/qr/{scene_id}/confirm", response_model=ResponseModel[bool])
async def confirm_qr_login(
    scene_id: str,
    confirm_data: QRLoginConfirmRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """确认扫码登录"""
    try:
        session = await auth_service.confirm_qr_login(
            scene_id=scene_id,
            user=current_user,
            confirm=confirm_data.confirm
        )
        
        # 记录审计日志
        await auth_service.log_audit(
            user_pool_id=current_user.user_pool_id,
            user_id=current_user.id,
            action="qr_login_confirm",
            details={
                "scene_id": scene_id,
                "confirm": confirm_data.confirm,
                "status": session.status.value
            },
            success=True,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        message = "登录确认成功" if confirm_data.confirm else "登录已取消"
        return ResponseModel(data=True, message=message)
        
    except Exception as e:
        logger.error("确认扫码登录失败", error=str(e))
        raise


@router.post("/reset-password", response_model=ResponseModel[bool])
async def reset_password(
    request: Request,
    reset_data: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """重置密码"""
    try:
        # 验证验证码
        user = await auth_service.verify_otp_login(
            identifier=reset_data.identifier,
            code=reset_data.code,  
            user_pool_id=reset_data.user_pool_id
        )
        
        # 重置密码（需要在UserService中实现）
        # 这里简化处理，实际应该调用用户服务
        
        # 记录审计日志
        await auth_service.log_audit(
            user_pool_id=reset_data.user_pool_id,
            user_id=user.id,
            action="password_reset",
            details={"identifier": reset_data.identifier},
            success=True,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent")
        )
        
        return ResponseModel(data=True, message="密码重置成功")
        
    except Exception as e:
        logger.error("重置密码失败", error=str(e))
        raise
