"""
FastAPI主应用
"""
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from contextlib import asynccontextmanager
import logging
import json
from typing import Any
import structlog

from app.config import settings
from app.core.middleware import (
    RequestLoggingMiddleware, 
    SecurityHeadersMiddleware, 
    setup_cors_middleware
)
from app.core.exceptions import (
    AuthError, PermissionError, ValidationError, 
    NotFoundError, ConflictError, RateLimitError, OTPError
)
from app.schemas.common import ErrorResponse, ErrorDetail
from app.api.v1.router import api_router
from app.db.database import create_db_and_tables

# 配置结构化日志
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class CustomJSONResponse(JSONResponse):
    """自定义JSON响应类，处理datetime序列化"""
    
    def render(self, content: Any) -> bytes:
        return json.dumps(
            jsonable_encoder(content),
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


# 创建FastAPI应用
app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    default_response_class=CustomJSONResponse,
    description="统一身份认证与管理平台API",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url=f"{settings.api_v1_str}/openapi.json",
)

# 设置CORS中间件
setup_cors_middleware(app)

# 添加自定义中间件
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# 注册API路由
app.include_router(api_router, prefix=settings.api_v1_str)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理器"""
    logger.error(
        "HTTP异常",
        status_code=exc.status_code,
        detail=exc.detail,
        url=str(request.url),
        method=request.method
    )
    
    # 返回FastAPI标准格式以兼容测试
    return CustomJSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """请求验证异常处理器"""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append(ErrorDetail(
            field=field,
            message=error["msg"]
        ))
    
    logger.error(
        "请求验证错误",
        errors=[error.model_dump() for error in errors],
        url=str(request.url),
        method=request.method
    )
    
    return CustomJSONResponse(
        status_code=422,
        content=ErrorResponse(
            code=422,
            message="请求参数验证失败",
            errors=errors
        ).model_dump()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(
        "未处理的异常",
        error=str(exc),
        error_type=type(exc).__name__,
        url=str(request.url),
        method=request.method,
        exc_info=True
    )
    
    # 生产环境不暴露详细错误信息
    if settings.debug:
        detail = str(exc)
    else:
        detail = "服务器内部错误"
    
    return CustomJSONResponse(
        status_code=500,
        content=ErrorResponse(
            code=500,
            message=detail
        ).model_dump()
    )


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    logger.info("应用启动中...")
    
    # 创建数据库表
    await create_db_and_tables()
    
    logger.info("应用启动完成", version=settings.version)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("应用关闭中...")


@app.get("/", tags=["基础"])
async def root():
    """根路径"""
    return {
        "message": "统一身份认证平台API",
        "version": settings.version,
        "docs_url": "/docs" if settings.debug else None
    }


@app.get("/health", tags=["基础"])
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.version
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
