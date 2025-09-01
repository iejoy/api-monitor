"""
系统设置数据模型
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class SystemSetting(Base):
    """系统设置模型"""
    __tablename__ = "system_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(50), nullable=False, comment="设置分类：email, feishu, wechat, system")
    name = Column(String(100), nullable=False, comment="设置名称")
    key = Column(String(100), nullable=False, comment="设置键名")
    value = Column(Text, comment="设置值")
    description = Column(Text, comment="设置描述")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否为默认配置")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 添加唯一约束，确保同一分类下的键名唯一
    __table_args__ = (
        UniqueConstraint('category', 'key', name='uq_system_setting_category_key'),
    )


class AlertChannelTemplate(Base):
    """告警渠道模板模型"""
    __tablename__ = "alert_channel_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="模板名称")
    type = Column(String(20), nullable=False, comment="告警类型：email, feishu, wechat")
    config = Column(JSON, comment="配置信息")
    description = Column(Text, comment="模板描述")
    
    # 告警内容模板
    alert_title_template = Column(String(200), comment="告警标题模板")
    alert_content_template = Column(Text, comment="告警内容模板")
    
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否为默认模板")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 添加唯一约束，确保同一类型下的默认模板只有一个
    __table_args__ = (
        UniqueConstraint('type', 'is_default', name='uq_alert_template_type_default'),
    )


class EmailTemplate(Base):
    """邮件模板模型"""
    __tablename__ = "email_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="模板名称")
    subject = Column(String(200), nullable=False, comment="邮件主题")
    content = Column(Text, nullable=False, comment="邮件内容")
    template_type = Column(String(50), default="alert", comment="模板类型：alert, test, notification")
    is_active = Column(Boolean, default=True, comment="是否启用")
    is_default = Column(Boolean, default=False, comment="是否为默认模板")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 添加唯一约束，确保同一类型下的默认模板只有一个
    __table_args__ = (
        UniqueConstraint('template_type', 'is_default', name='uq_email_template_type_default'),
    )