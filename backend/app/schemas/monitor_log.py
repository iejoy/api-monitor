"""
监控日志相关的Pydantic模式
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class MonitorLogBase(BaseModel):
    """监控日志基础模式"""
    service_id: int = Field(..., description="服务ID")
    status: str = Field(..., description="检查状态")
    response_time: Optional[float] = Field(None, description="响应时间(毫秒)")
    status_code: Optional[int] = Field(None, description="HTTP状态码")
    response_size: Optional[int] = Field(None, description="响应大小(字节)")
    error_message: Optional[str] = Field(None, description="错误信息")
    error_type: Optional[str] = Field(None, description="错误类型")
    request_url: Optional[str] = Field(None, description="请求URL")
    request_method: Optional[str] = Field(None, description="请求方法")
    alert_sent: bool = Field(default=False, description="是否已发送告警")
    alert_methods: Optional[str] = Field(None, description="已发送的告警方式")


class MonitorLogCreate(MonitorLogBase):
    """创建监控日志模式"""
    pass


class MonitorLogResponse(MonitorLogBase):
    """监控日志响应模式"""
    id: int
    check_time: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True


class MonitorLogListResponse(BaseModel):
    """监控日志列表响应模式"""
    total: int
    items: List[MonitorLogResponse]


class MonitorLogQuery(BaseModel):
    """监控日志查询模式"""
    service_id: Optional[int] = Field(None, description="服务ID")
    status: Optional[str] = Field(None, description="状态筛选")
    start_time: Optional[datetime] = Field(None, description="开始时间")
    end_time: Optional[datetime] = Field(None, description="结束时间")
    page: int = Field(default=1, ge=1, description="页码")
    size: int = Field(default=20, ge=1, le=100, description="每页数量")


class MonitorStats(BaseModel):
    """监控统计模式"""
    total_checks: int = Field(..., description="总检查次数")
    success_count: int = Field(..., description="成功次数")
    failed_count: int = Field(..., description="失败次数")
    success_rate: float = Field(..., description="成功率")
    avg_response_time: Optional[float] = Field(None, description="平均响应时间")
    last_24h_checks: int = Field(..., description="最近24小时检查次数")
    last_24h_success_rate: float = Field(..., description="最近24小时成功率")