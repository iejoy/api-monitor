"""
配置管理
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 基础配置
    APP_NAME: str = "业务应用监控平台"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置
    DATABASE_URL: str = "mysql://monitor:monitor123@localhost:3306/business_monitor"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 邮件配置
    SMTP_HOST: str = "smtp.qq.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    
    # 飞书配置
    FEISHU_WEBHOOK_URL: str = ""
    
    # 微信配置
    WECHAT_WEBHOOK_URL: str = ""
    
    # 监控配置
    DEFAULT_TIMEOUT: int = 30  # 默认超时时间（秒）
    DEFAULT_INTERVAL: int = 300  # 默认监控间隔（秒）
    MAX_RETRY_COUNT: int = 3  # 最大重试次数

    # 邮件代理配置
    # 是否启用邮件代理
    EMAIL_USE_PROXY: bool = False

    # 代理服务器地址
    EMAIL_PROXY_HOST: str = "127.0.0.1"

    # 代理服务器端口
    EMAIL_PROXY_PORT: int = 1080

    # 代理类型 (SOCKS5, SOCKS4, HTTP)
    EMAIL_PROXY_TYPE: str = "HTTP"

    # 代理用户名（可选）
    EMAIL_PROXY_USERNAME: str = ""

    # 代理密码（可选）
    EMAIL_PROXY_PASSWORD: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
settings = Settings()