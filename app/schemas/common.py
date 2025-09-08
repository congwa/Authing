"""
公共数据模式
"""
from datetime import datetime, UTC
from typing import Generic, TypeVar, Optional, List, Any
from pydantic import BaseModel, Field


T = TypeVar('T')


class ResponseModel(BaseModel, Generic[T]):
    """统一API响应格式"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: Optional[T] = Field(default=None, description="响应数据")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="时间戳")


class PaginationMeta(BaseModel):
    """分页元信息"""
    page: int = Field(description="当前页码")
    per_page: int = Field(description="每页数量")
    total: int = Field(description="总数量")
    total_pages: int = Field(description="总页数")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    code: int = Field(default=200, description="状态码")
    message: str = Field(default="success", description="响应消息")
    data: List[T] = Field(description="数据列表")
    meta: PaginationMeta = Field(description="分页信息")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="时间戳")


class ErrorDetail(BaseModel):
    """错误详情"""
    field: str = Field(description="错误字段")
    message: str = Field(description="错误消息")


class ErrorResponse(BaseModel):
    """错误响应格式"""
    code: int = Field(description="错误代码")
    message: str = Field(description="错误消息")
    errors: Optional[List[ErrorDetail]] = Field(default=None, description="详细错误信息")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC), description="时间戳")
