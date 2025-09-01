"""
监控日志模型
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class MonitorLog(Base):
    """监控日志表"""
    __tablename__ = "monitor_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("monitor_services.id"), nullable=False, comment="服务ID")
    
    # 检查结果
    status = Column(String(20), nullable=False, comment="检查状态: success/failed/timeout")
    response_time = Column(Float, comment="响应时间(毫秒)")
    status_code = Column(Integer, comment="HTTP状态码")
    response_size = Column(Integer, comment="响应大小(字节)")
    
    # 错误信息
    error_message = Column(Text, comment="错误信息")
    error_type = Column(String(50), comment="错误类型")
    
    # 请求详情
    request_url = Column(String(500), comment="请求URL")
    request_method = Column(String(10), comment="请求方法")
    request_headers = Column(Text, comment="请求头(JSON)")
    
    # 响应详情
    response_headers = Column(Text, comment="响应头(JSON)")
    response_body = Column(Text, comment="响应体(截取前1000字符)")
    
    # 告警状态
    alert_sent = Column(Boolean, default=False, comment="是否已发送告警")
    alert_methods = Column(String(100), comment="已发送的告警方式")
    
    # 时间戳
    check_time = Column(DateTime, default=func.now(), comment="检查时间")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    
    # 关联关系
    service = relationship("MonitorService", backref="logs")
    
    def __repr__(self):
        return f"<MonitorLog(id={self.id}, service_id={self.service_id}, status='{self.status}')>"