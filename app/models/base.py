"""
基础数据模型
"""
from datetime import datetime, UTC
from typing import Optional
from sqlmodel import SQLModel, Field


class TimestampMixin(SQLModel):
    """时间戳混入类"""
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: Optional[datetime] = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column_kwargs={"onupdate": lambda: datetime.now(UTC)}
    )


class BaseModel(TimestampMixin):
    """基础模型类"""
    id: Optional[int] = Field(default=None, primary_key=True)
