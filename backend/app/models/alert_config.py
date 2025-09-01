"""
告警配置模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class AlertConfig(Base):
    """告警配置表"""
    __tablename__ = "alert_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="配置名称")
    type = Column(String(20), nullable=False, comment="告警类型: email/feishu/wechat")
    
    # 关联服务
    service_id = Column(Integer, ForeignKey("monitor_services.id"), nullable=False, comment="关联的服务ID")
    service = relationship("MonitorService", back_populates="alert_configs")
    
    # 告警条件和频率
    alert_conditions = Column(Text, comment="告警条件，逗号分隔")
    response_threshold = Column(Integer, comment="响应时间阈值(毫秒)")
    alert_frequency = Column(String(20), default="immediate", comment="告警频率: immediate/once_per_hour/once_per_day")
    
    # 配置参数(JSON格式存储)
    config = Column(JSON, comment="告警配置参数")
    
    # 邮件配置示例:
    # {
    #   "smtp_host": "smtp.qq.com",
    #   "smtp_port": 587,
    #   "username": "user@qq.com",
    #   "password": "password",
    #   "from_email": "user@qq.com",
    #   "to_emails": ["admin@company.com"]
    # }
    
    # 飞书配置示例:
    # {
    #   "webhook_url": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
    # }
    
    # 微信配置示例:
    # {
    #   "webhook_url": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
    # }
    
    # 状态和描述
    is_active = Column(Boolean, default=True, comment="是否启用")
    description = Column(Text, comment="配置描述")
    
    # 测试状态
    last_test_time = Column(DateTime, comment="最后测试时间")
    last_test_result = Column(String(20), comment="最后测试结果: success/failed")
    last_test_message = Column(Text, comment="最后测试消息")
    
    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 添加唯一约束：每个服务只能有一个告警配置
    __table_args__ = (
        UniqueConstraint('service_id', name='uq_alert_config_service'),
    )
    
    def __repr__(self):
        return f"<AlertConfig(id={self.id}, name='{self.name}', type='{self.type}', service_id={self.service_id})>"