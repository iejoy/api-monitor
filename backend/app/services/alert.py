"""
修复后的告警通知服务
"""
import json
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List
import httpx
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.service import MonitorService
from app.models.alert_config import AlertConfig
from app.models.system_setting import SystemSetting, AlertChannelTemplate
from app.services.email_proxy import create_proxy_smtp_connection

logger = logging.getLogger(__name__)


class AlertService:
    """告警服务类"""
    
    def __init__(self):
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def send_alert(self, service: MonitorService, check_result: Dict[str, Any]) -> Dict[str, Any]:
        """发送告警通知"""
        if not service.enable_alert:
            logger.info(f"服务 {service.name} 未启用告警")
            return
        
        # 解析告警方式
        alert_methods = [method.strip() for method in service.alert_methods.split(',')]
        logger.info(f"服务 {service.name} 配置的告警方式: {alert_methods}")
        
        # 构建告警消息
        alert_data = self._build_alert_message(service, check_result)
        
        # 发送各种类型的告警
        for method in alert_methods:
            try:
                if method == "email":
                    await self._send_email_alert(service, alert_data)
                elif method == "feishu":
                    await self._send_feishu_alert(service, alert_data)
                elif method == "wechat":
                    await self._send_wechat_alert(service, alert_data)
                else:
                    logger.warning(f"不支持的告警方式: {method}")
            except Exception as e:
                logger.error(f"发送{method}告警失败: {str(e)}")
    
    async def send_recovery_alert(self, service: MonitorService, check_result: Dict[str, Any]) -> Dict[str, Any]:
        """发送恢复通知"""
        if not service.enable_alert:
            logger.info(f"服务 {service.name} 未启用告警")
            return
        
        # 解析告警方式
        alert_methods = [method.strip() for method in service.alert_methods.split(',')]
        logger.info(f"服务 {service.name} 发送恢复通知，配置的告警方式: {alert_methods}")
        
        # 构建恢复通知消息
        alert_data = self._build_recovery_message(service, check_result)
        
        # 发送各种类型的恢复通知
        for method in alert_methods:
            try:
                if method == "email":
                    await self._send_email_alert(service, alert_data)
                elif method == "feishu":
                    await self._send_feishu_alert(service, alert_data)
                elif method == "wechat":
                    await self._send_wechat_alert(service, alert_data)
                else:
                    logger.warning(f"不支持的告警方式: {method}")
            except Exception as e:
                logger.error(f"发送{method}恢复通知失败: {str(e)}")
    
    def _build_alert_message(self, service: MonitorService, check_result: Dict[str, Any]) -> Dict[str, Any]:
        """构建告警消息"""
        status_map = {
            "failed": "❌ 服务异常",
            "timeout": "⏰ 服务超时",
            "success": "✅ 服务正常"
        }
        
        status_text = status_map.get(check_result["status"], "❓ 状态未知")
        
        return {
            "title": f"【业务监控告警】{service.name} - {status_text}",
            "service_name": service.name,
            "service_url": service.url,
            "status": check_result["status"],
            "status_text": status_text,
            "error_message": check_result.get("error_message", ""),
            "response_time": check_result.get("response_time"),
            "status_code": check_result.get("status_code"),
            "check_time": check_result["check_time"].strftime("%Y-%m-%d %H:%M:%S"),
            "description": service.description or ""
        }
    
    def _build_recovery_message(self, service: MonitorService, check_result: Dict[str, Any]) -> Dict[str, Any]:
        """构建恢复通知消息"""
        return {
            "title": f"【业务监控恢复】{service.name} - 🎉 服务已恢复正常",
            "service_name": service.name,
            "service_url": service.url,
            "status": check_result["status"],
            "status_text": "✅ 服务已恢复正常",
            "error_message": "",  # 恢复时没有错误信息
            "response_time": check_result.get("response_time"),
            "status_code": check_result.get("status_code"),
            "check_time": check_result["check_time"].strftime("%Y-%m-%d %H:%M:%S"),
            "description": service.description or "",
            "recovery_time": check_result["check_time"].strftime("%Y-%m-%d %H:%M:%S")
        }
    
    async def _send_email_alert(self, service: MonitorService, alert_data: Dict[str, Any]):
        """发送邮件告警"""
        # 获取服务的告警配置
        alert_configs = await self._get_alert_configs(service.id, "email")
        if not alert_configs:
            logger.warning(f"服务 {service.name} 未找到邮件告警配置")
            return
        
        # 获取系统邮件配置
        smtp_config = await self._get_system_email_config()
        if not smtp_config:
            logger.error("系统邮件配置不存在，无法发送邮件告警")
            return
        
        for config in alert_configs:
            try:
                # 合并系统配置和告警配置
                email_config = {**smtp_config}
                if config.config and "to_emails" in config.config:
                    email_config["to_emails"] = config.config["to_emails"]
                else:
                    logger.warning(f"告警配置 {config.id} 缺少收件人信息")
                    continue
                
                await self._send_single_email(email_config, alert_data)
                logger.info(f"邮件告警发送成功: {service.name}")
            except Exception as e:
                logger.error(f"邮件告警发送失败: {str(e)}")
    
    async def _get_system_email_config(self) -> Dict[str, Any]:
        """获取系统邮件配置"""
        db = SessionLocal()
        try:
            email_settings = db.query(SystemSetting).filter(
                SystemSetting.category == "email",
                SystemSetting.is_active == True
            ).all()
            
            if not email_settings:
                return None
            
            config = {}
            for setting in email_settings:
                if setting.key == "smtp_server":
                    config["smtp_host"] = setting.value
                elif setting.key == "smtp_port":
                    config["smtp_port"] = int(setting.value)
                elif setting.key == "smtp_username":
                    config["username"] = setting.value
                elif setting.key == "smtp_password":
                    config["password"] = setting.value
                elif setting.key == "smtp_from_email":
                    config["from_email"] = setting.value
                elif setting.key == "smtp_use_tls":
                    config["use_tls"] = setting.value.lower() == "true"
            
            # 验证必需字段
            required_fields = ["smtp_host", "smtp_port", "username", "password", "from_email"]
            for field in required_fields:
                if not config.get(field):
                    logger.error(f"系统邮件配置不完整：缺少{field}")
                    return None
            
            return config
        finally:
            db.close()
    
    async def _send_single_email(self, config: Dict[str, Any], alert_data: Dict[str, Any]):
        """发送单个邮件"""
        # 构建邮件内容 - 根据消息类型调整内容
        subject = alert_data["title"]
        
        if "恢复" in alert_data["title"]:
            # 恢复通知邮件内容
            body = f"""
业务监控恢复通知

服务名称: {alert_data['service_name']}
服务地址: {alert_data['service_url']}
当前状态: {alert_data['status_text']}
恢复时间: {alert_data['recovery_time']}
响应时间: {alert_data.get('response_time', 'N/A')}ms
状态码: {alert_data.get('status_code', 'N/A')}

服务描述: {alert_data.get('description', '无')}

服务已恢复正常运行，感谢您的关注！

---
业务应用监控平台
            """.strip()
        else:
            # 告警通知邮件内容
            body = f"""
业务监控告警通知

服务名称: {alert_data['service_name']}
服务地址: {alert_data['service_url']}
当前状态: {alert_data['status_text']}
检查时间: {alert_data['check_time']}
响应时间: {alert_data.get('response_time', 'N/A')}ms
状态码: {alert_data.get('status_code', 'N/A')}

错误信息: {alert_data.get('error_message', '无')}

服务描述: {alert_data.get('description', '无')}

请及时处理相关问题。

---
业务应用监控平台
            """.strip()
        
        # 创建邮件
        msg = MIMEMultipart()
        msg['From'] = config['from_email']
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 使用代理发送邮件
        proxy_smtp = create_proxy_smtp_connection(config)
        try:
            server = proxy_smtp.connect()
            server.set_debuglevel(0)  # 关闭调试模式
            
            # 发送EHLO命令
            server.ehlo()
            
            # 启用TLS加密
            if config.get('use_tls', True):
                server.starttls()
                server.ehlo()  # TLS后重新发送EHLO
            
            # 登录SMTP服务器
            server.login(config['from_email'], config['password'])
            
            # 发送给所有收件人
            for to_email in config['to_emails']:
                msg['To'] = to_email
                server.send_message(msg)
                del msg['To']  # 清除To字段，为下一个收件人准备
                
        finally:
            proxy_smtp.close()
    
    async def _send_feishu_alert(self, service: MonitorService, alert_data: Dict[str, Any]):
        """发送飞书告警"""
        # 获取服务的告警配置
        alert_configs = await self._get_alert_configs(service.id, "feishu")
        if not alert_configs:
            logger.warning(f"服务 {service.name} 未找到飞书告警配置")
            return
        
        # 构建飞书消息
        message = {
            "msg_type": "interactive",
            "card": {
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "content": f"**{alert_data['title']}**",
                            "tag": "lark_md"
                        }
                    },
                    {
                        "tag": "div",
                        "fields": [
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**服务名称:**\n{alert_data['service_name']}",
                                    "tag": "lark_md"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**当前状态:**\n{alert_data['status_text']}",
                                    "tag": "lark_md"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**检查时间:**\n{alert_data['check_time']}",
                                    "tag": "lark_md"
                                }
                            },
                            {
                                "is_short": True,
                                "text": {
                                    "content": f"**响应时间:**\n{alert_data.get('response_time', 'N/A')}ms",
                                    "tag": "lark_md"
                                }
                            }
                        ]
                    }
                ]
            }
        }
        
        if alert_data.get('error_message'):
            message["card"]["elements"].append({
                "tag": "div",
                "text": {
                    "content": f"**错误信息:**\n{alert_data['error_message']}",
                    "tag": "lark_md"
                }
            })
        
        # 发送飞书消息
        for config in alert_configs:
            try:
                webhook_url = await self._get_webhook_url_from_template(config, "feishu")
                if not webhook_url:
                    logger.error(f"飞书告警配置 {config.id} 无法获取webhook_url")
                    continue
                
                response = await self.http_client.post(webhook_url, json=message)
                if response.status_code == 200:
                    logger.info(f"飞书告警发送成功: {service.name}")
                else:
                    logger.error(f"飞书告警发送失败: {response.text}")
            except Exception as e:
                logger.error(f"飞书告警发送异常: {str(e)}")
    
    async def _send_wechat_alert(self, service: MonitorService, alert_data: Dict[str, Any]):
        """发送微信告警"""
        # 获取服务的告警配置
        alert_configs = await self._get_alert_configs(service.id, "wechat")
        if not alert_configs:
            logger.warning(f"服务 {service.name} 未找到微信告警配置")
            return
        
        # 构建微信消息内容 - 根据消息类型调整
        if "恢复" in alert_data["title"]:
            # 恢复通知内容
            content = f"""
{alert_data['title']}

服务名称: {alert_data['service_name']}
服务地址: {alert_data['service_url']}
当前状态: {alert_data['status_text']}
恢复时间: {alert_data['recovery_time']}
响应时间: {alert_data.get('response_time', 'N/A')}ms
状态码: {alert_data.get('status_code', 'N/A')}

服务已恢复正常运行！
            """.strip()
        else:
            # 告警通知内容
            content = f"""
{alert_data['title']}

服务名称: {alert_data['service_name']}
服务地址: {alert_data['service_url']}
当前状态: {alert_data['status_text']}
检查时间: {alert_data['check_time']}
响应时间: {alert_data.get('response_time', 'N/A')}ms
状态码: {alert_data.get('status_code', 'N/A')}

错误信息: {alert_data.get('error_message', '无')}
            """.strip()
        
        message = {
            "msgtype": "text",
            "text": {
                "content": content
            }
        }
        
        # 发送微信消息
        for config in alert_configs:
            try:
                webhook_url = await self._get_webhook_url_from_template(config, "wechat")
                if not webhook_url:
                    logger.error(f"微信告警配置 {config.id} 无法获取webhook_url")
                    continue
                
                response = await self.http_client.post(webhook_url, json=message)
                if response.status_code == 200:
                    logger.info(f"微信告警发送成功: {service.name}")
                else:
                    logger.error(f"微信告警发送失败: {response.text}")
            except Exception as e:
                logger.error(f"微信告警发送异常: {str(e)}")
    
    async def _get_webhook_url_from_template(self, config: AlertConfig, alert_type: str) -> str:
        """从模板配置中获取webhook_url"""
        if not config.config or "template_id" not in config.config:
            logger.error(f"告警配置 {config.id} 缺少template_id")
            return None
        
        template_id = config.config["template_id"]
        try:
            template_id = int(template_id)
        except (ValueError, TypeError):
            logger.error(f"无效的模板ID：{template_id}")
            return None
        
        db = SessionLocal()
        try:
            template = db.query(AlertChannelTemplate).filter(
                AlertChannelTemplate.id == template_id,
                AlertChannelTemplate.type == alert_type,
                AlertChannelTemplate.is_active == True
            ).first()
            
            if not template:
                logger.error(f"{alert_type}模板不存在：ID={template_id}")
                return None
            
            if not template.config or "webhook_url" not in template.config:
                logger.error(f"{alert_type}模板配置不完整：缺少webhook_url，ID={template_id}")
                return None
            
            return template.config["webhook_url"]
        finally:
            db.close()
    
    async def _get_alert_configs(self, service_id: int, alert_type: str) -> List[AlertConfig]:
        """获取指定服务和类型的告警配置"""
        db = SessionLocal()
        try:
            return db.query(AlertConfig).filter(
                AlertConfig.service_id == service_id,
                AlertConfig.type == alert_type,
                AlertConfig.is_active == True
            ).all()
        finally:
            db.close()
    
    async def test_alert_config(self, config: AlertConfig, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """测试告警配置"""
        try:
            if config.type == "email":
                await self._test_email_config(config.config, test_data)
            elif config.type == "feishu":
                await self._test_feishu_config(config.config, test_data)
            elif config.type == "wechat":
                await self._test_wechat_config(config.config, test_data)
            else:
                raise ValueError(f"不支持的告警类型: {config.type}")
            
            return {"success": True, "message": "测试成功"}
        except Exception as e:
            return {"success": False, "message": f"测试失败: {str(e)}"}
    
    async def _test_email_config(self, config: Dict[str, Any], test_data: Dict[str, Any]):
        """测试邮件配置"""
        # 获取系统邮件配置
        smtp_config = await self._get_system_email_config()
        if not smtp_config:
            raise Exception("系统邮件配置不存在")
        
        if not config or "to_emails" not in config:
            raise Exception("邮件配置不完整：缺少收件人")
        
        # 合并配置
        email_config = {**smtp_config, "to_emails": config["to_emails"]}
        
        msg = MIMEText(test_data["message"], 'plain', 'utf-8')
        msg['From'] = email_config['from_email']
        msg['Subject'] = test_data["title"]
        
        # 使用代理发送测试邮件
        proxy_smtp = create_proxy_smtp_connection(email_config)
        try:
            server = proxy_smtp.connect()
            server.set_debuglevel(0)  # 关闭调试模式
            
            # 发送EHLO命令
            server.ehlo()
            
            # 启用TLS加密
            if email_config.get('use_tls', True):
                server.starttls()
                server.ehlo()  # TLS后重新发送EHLO
            
            # 登录SMTP服务器
            server.login(email_config['from_email'], email_config['password'])
            
            # 发送给所有收件人
            for to_email in email_config['to_emails']:
                msg['To'] = to_email
                server.send_message(msg)
                del msg['To']  # 清除To字段，为下一个收件人准备
                
        finally:
            proxy_smtp.close()
    
    async def _test_feishu_config(self, config: Dict[str, Any], test_data: Dict[str, Any]):
        """测试飞书配置"""
        webhook_url = await self._get_webhook_url_from_template_config(config, "feishu")
        if not webhook_url:
            raise Exception("无法获取飞书webhook_url")
        
        message = {
            "msg_type": "text",
            "content": {
                "text": f"{test_data['title']}\n\n{test_data['message']}"
            }
        }
        
        response = await self.http_client.post(webhook_url, json=message)
        
        if response.status_code != 200:
            raise Exception(f"飞书API返回错误: {response.text}")
    
    async def _test_wechat_config(self, config: Dict[str, Any], test_data: Dict[str, Any]):
        """测试微信配置"""
        webhook_url = await self._get_webhook_url_from_template_config(config, "wechat")
        if not webhook_url:
            raise Exception("无法获取微信webhook_url")
        
        message = {
            "msgtype": "text",
            "text": {
                "content": f"{test_data['title']}\n\n{test_data['message']}"
            }
        }
        
        response = await self.http_client.post(webhook_url, json=message)
        
        if response.status_code != 200:
            raise Exception(f"微信API返回错误: {response.text}")
    
    async def _get_webhook_url_from_template_config(self, config: Dict[str, Any], alert_type: str) -> str:
        """从配置中获取模板的webhook_url"""
        if not config or "template_id" not in config:
            return None
        
        template_id = config["template_id"]
        try:
            template_id = int(template_id)
        except (ValueError, TypeError):
            return None
        
        db = SessionLocal()
        try:
            template = db.query(AlertChannelTemplate).filter(
                AlertChannelTemplate.id == template_id,
                AlertChannelTemplate.type == alert_type,
                AlertChannelTemplate.is_active == True
            ).first()
            
            if not template or not template.config or "webhook_url" not in template.config:
                return None
            
            return template.config["webhook_url"]
        finally:
            db.close()
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()


# 创建全局告警服务实例
alert_service = AlertService()