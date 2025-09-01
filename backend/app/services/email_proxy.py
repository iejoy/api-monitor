"""
邮件代理配置和SMTP连接工具
"""
import smtplib
import socks
import socket
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv


# 强制使用IPv4的socket解析
def force_ipv4_socket():
    """强制socket只使用IPv4"""
    original_getaddrinfo = socket.getaddrinfo
    
    def ipv4_only_getaddrinfo(*args, **kwargs):
        # 调用原始函数
        results = original_getaddrinfo(*args, **kwargs)
        # 过滤掉IPv6结果，只保留IPv4
        ipv4_results = [res for res in results if res[0] == socket.AF_INET]
        return ipv4_results if ipv4_results else results
    
    socket.getaddrinfo = ipv4_only_getaddrinfo


class EmailProxyConfig:
    """邮件代理配置类"""
    
    def __init__(self):
        self.proxy_host = None
        self.proxy_port = None
        self.proxy_type = None
        self.proxy_username = None
        self.proxy_password = None
        self.use_proxy = False
        self.load_from_env()
    
    def load_from_env(self):
        """从环境变量加载代理配置"""
        load_dotenv()
        # 从环境变量读取代理配置
        self.use_proxy = os.getenv('EMAIL_USE_PROXY', 'false').lower() == 'true'
        self.proxy_host = os.getenv('EMAIL_PROXY_HOST')
        self.proxy_port = int(os.getenv('EMAIL_PROXY_PORT', '0')) if os.getenv('EMAIL_PROXY_PORT') else None
        self.proxy_type = os.getenv('EMAIL_PROXY_TYPE', 'SOCKS5')
        self.proxy_username = os.getenv('EMAIL_PROXY_USERNAME')
        self.proxy_password = os.getenv('EMAIL_PROXY_PASSWORD')
    
    def is_configured(self) -> bool:
        """检查代理是否已配置"""
        if not self.use_proxy:
            return False
        return bool(self.proxy_host and self.proxy_port and self.proxy_type)
    
    def get_proxy_dict(self) -> Dict[str, Any]:
        """获取代理配置字典"""
        if not self.is_configured():
            return {}
        
        proxy_config = {
            'proxy_type': self.proxy_type,
            'addr': self.proxy_host,
            'port': self.proxy_port,
        }
        
        if self.proxy_username and self.proxy_password:
            proxy_config['username'] = self.proxy_username
            proxy_config['password'] = self.proxy_password
        
        return proxy_config


class ProxySMTP:
    """支持代理的SMTP连接类"""
    
    def __init__(self, smtp_config: Dict[str, Any], proxy_config: EmailProxyConfig):
        self.original_socket = None
        self.original_getaddrinfo = None
        self.smtp_config = smtp_config
        self.proxy_config = proxy_config
        self.server = None
    
    def connect(self) -> smtplib.SMTP:
        """建立SMTP连接（支持代理）"""
        # 如果配置了代理，设置代理
        if self.proxy_config.is_configured():
            # 保存原始socket
            self.original_socket = socket.socket
            self.original_getaddrinfo = socket.getaddrinfo

            # 强制使用IPv4
            force_ipv4_socket()

            proxy_dict = self.proxy_config.get_proxy_dict()
            
            # 根据代理类型设置socket
            if proxy_dict['proxy_type'].upper() == 'SOCKS5':
                socks.set_default_proxy(
                    socks.SOCKS5, 
                    proxy_dict['addr'], 
                    proxy_dict['port'],
                    username=proxy_dict.get('username'),
                    password=proxy_dict.get('password')
                )
            elif proxy_dict['proxy_type'].upper() == 'SOCKS4':
                socks.set_default_proxy(
                    socks.SOCKS4, 
                    proxy_dict['addr'], 
                    proxy_dict['port']
                )
            elif proxy_dict['proxy_type'].upper() == 'HTTP':
                socks.set_default_proxy(
                    socks.HTTP, 
                    proxy_dict['addr'], 
                    proxy_dict['port'],
                    username=proxy_dict.get('username'),
                    password=proxy_dict.get('password')
                )
            
            # 包装socket
            socket.socket = socks.socksocket
        
        # 创建SMTP连接
        self.server = smtplib.SMTP(
            self.smtp_config['smtp_host'], 
            self.smtp_config['smtp_port'], 
            timeout=30
        )
        
        return self.server
    
    def close(self):
        """关闭连接"""
        if self.server:
            try:
                self.server.quit()
            except:
                try:
                    self.server.close()
                except:
                    pass
            finally:
                self.server = None
        
        # 恢复原始socket
        if self.proxy_config.is_configured() and self.original_socket:
            socket.socket = self.original_socket
            if self.original_getaddrinfo:
                socket.getaddrinfo = self.original_getaddrinfo


def get_email_proxy_config() -> EmailProxyConfig:
    """获取邮件代理配置"""
    return EmailProxyConfig()


def create_proxy_smtp_connection(smtp_config: Dict[str, Any]) -> ProxySMTP:
    """创建支持代理的SMTP连接"""
    proxy_config = get_email_proxy_config()
    return ProxySMTP(smtp_config, proxy_config)
