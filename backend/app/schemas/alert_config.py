"""
告警配置相关的Pydantic模式
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AlertConfigBase(BaseModel):
    """告警配置基础模式"""
    name: str = Field(..., min_length=1, max_length=100, description="配置名称")
    type: str = Field(..., description="告警类型: email/feishu/wechat")
    config: Dict[str, Any] = Field(..., description="告警配置参数")
    is_active: bool = Field(default=True, description="是否启用")
    description: Optional[str] = Field(None, description="配置描述")


class AlertConfigCreate(AlertConfigBase):
    """创建告警配置模式"""
    pass


class AlertConfigUpdate(BaseModel):
    """更新告警配置模式"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None


class AlertConfigResponse(AlertConfigBase):
    """告警配置响应模式"""
    id: int
    last_test_time: Optional[datetime]
    last_test_result: Optional[str]
    last_test_message: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AlertConfigListResponse(BaseModel):
    """告警配置列表响应模式"""
    total: int
    items: List[AlertConfigResponse]


class AlertTestRequest(BaseModel):
    """告警测试请求模式"""
    title: str = Field(default="测试告警", description="告警标题")
    message: str = Field(default="这是一条测试告警消息", description="告警内容")


class AlertTestResponse(BaseModel):
    """告警测试响应模式"""
    success: bool = Field(..., description="测试是否成功")
    message: str = Field(..., description="测试结果消息")
    details: Optional[str] = Field(None, description="详细信息")


class EmailConfig(BaseModel):
    """邮件配置模式"""
    smtp_host: str = Field(..., description="SMTP服务器")
    smtp_port: int = Field(..., description="SMTP端口")
    username: str = Field(..., description="用户名")
    password: str = Field(..., description="密码")
    from_email: str = Field(..., description="发件人邮箱")
    to_emails: List[str] = Field(..., description="收件人邮箱列表")
    use_tls: bool = Field(default=True, description="是否使用TLS")


class FeishuConfig(BaseModel):
    """飞书配置模式"""
    webhook_url: str = Field(..., description="飞书机器人Webhook URL")


class WechatConfig(BaseModel):
    """微信配置模式"""
    webhook_url: str = Field(..., description="企业微信机器人Webhook URL")