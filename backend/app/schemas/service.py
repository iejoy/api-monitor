"""
服务监控相关的Pydantic模式
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, HttpUrl, Field


class ServiceBase(BaseModel):
    """服务基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="服务名称")
    url: str = Field(..., description="监控URL")
    method: str = Field(default="GET", description="请求方法")
    timeout: int = Field(default=30, ge=1, le=300, description="超时时间(秒)")
    interval: int = Field(default=300, ge=60, le=86400, description="监控间隔(秒)")
    retry_count: int = Field(default=3, ge=0, le=10, description="重试次数")
    is_active: bool = Field(default=True, description="是否启用")
    enable_alert: bool = Field(default=True, description="是否启用告警")
    alert_methods: str = Field(default="email", description="告警方式")
    alert_contacts: Optional[str] = Field(None, description="告警联系人")
    description: Optional[str] = Field(None, description="服务描述")
    tags: Optional[str] = Field(None, description="标签")


class ServiceCreate(ServiceBase):
    """创建服务模式"""
    pass


class ServiceUpdate(BaseModel):
    """更新服务模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    url: Optional[str] = None
    method: Optional[str] = None
    timeout: Optional[int] = Field(None, ge=1, le=300)
    interval: Optional[int] = Field(None, ge=60, le=86400)
    retry_count: Optional[int] = Field(None, ge=0, le=10)
    is_active: Optional[bool] = None
    enable_alert: Optional[bool] = None
    alert_methods: Optional[str] = None
    alert_contacts: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None


class ServiceResponse(ServiceBase):
    """服务响应模式"""
    id: int
    status: str
    last_check_time: Optional[datetime]
    last_success_time: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ServiceListResponse(BaseModel):
    """服务列表响应模式"""
    total: int
    items: List[ServiceResponse]


class ServiceStatusUpdate(BaseModel):
    """服务状态更新模式"""
    status: str = Field(..., description="服务状态")
    last_check_time: datetime = Field(..., description="最后检查时间")
    last_success_time: Optional[datetime] = Field(None, description="最后成功时间")