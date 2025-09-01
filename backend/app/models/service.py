"""
服务监控模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class MonitorService(Base):
    """监控服务表"""
    __tablename__ = "monitor_services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="服务名称")
    url = Column(String(500), nullable=False, comment="监控URL")
    method = Column(String(10), default="GET", comment="请求方法")
    timeout = Column(Integer, default=30, comment="超时时间(秒)")
    interval = Column(Integer, default=300, comment="监控间隔(秒)")
    retry_count = Column(Integer, default=3, comment="重试次数")
    
    # 状态字段
    is_active = Column(Boolean, default=True, comment="是否启用")
    status = Column(String(20), default="unknown", comment="当前状态: healthy/unhealthy/unknown")
    last_check_time = Column(DateTime, comment="最后检查时间")
    last_success_time = Column(DateTime, comment="最后成功时间")
    
    # 告警配置
    enable_alert = Column(Boolean, default=True, comment="是否启用告警")
    alert_methods = Column(String(100), default="email", comment="告警方式: email,feishu,wechat")
    alert_contacts = Column(Text, comment="告警联系人(JSON格式)")
    
    # 描述信息
    description = Column(Text, comment="服务描述")
    tags = Column(String(200), comment="标签")
    
    # 关联告警配置
    alert_configs = relationship("AlertConfig", back_populates="service")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    def __repr__(self):
        return f"<MonitorService(id={self.id}, name='{self.name}', url='{self.url}')>"