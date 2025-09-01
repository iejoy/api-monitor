"""
服务监控核心逻辑 - 优化版本
"""
import asyncio
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import httpx
from sqlalchemy.orm import Session

from app.core.database import get_db_sync, get_db_session
from app.models.service import MonitorService as ServiceModel
from app.models.monitor_log import MonitorLog
from app.services.alert import alert_service

logger = logging.getLogger(__name__)


class MonitorService:
    """监控服务类"""
    
    def __init__(self):
        # 优化HTTP客户端配置，添加连接限制
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
            limits=httpx.Limits(
                max_keepalive_connections=20,  # 最大保持连接数
                max_connections=100,           # 最大连接数
                keepalive_expiry=30.0         # 连接保持时间
            ),
            # 添加重试配置
            transport=httpx.AsyncHTTPTransport(
                retries=2,
                verify=False  # 在生产环境中根据需要调整
            )
        )
        self._closed = False
    
    async def check_service(self, service: ServiceModel) -> Dict[str, Any]:
        """检查单个服务状态"""
        if self._closed:
            raise RuntimeError("MonitorService has been closed")
            
        start_time = time.time()
        result = {
            "service_id": getattr(service, 'id', 0),
            "status": "unknown",
            "response_time": None,
            "status_code": None,
            "response_size": None,
            "error_message": None,
            "error_type": None,
            "request_url": getattr(service, 'url', ''),
            "request_method": getattr(service, 'method', 'GET'),
            "check_time": datetime.now()
        }
        
        try:
            service_name = getattr(service, 'name', f'service_{result["service_id"]}')
            service_url = result["request_url"]
            logger.info(f"开始检查服务: {service_name} ({service_url})")
            
            # 发送HTTP请求
            response = await self.client.request(
                method=result["request_method"],
                url=service_url,
                timeout=min(getattr(service, 'timeout', 30), 30)  # 限制最大超时时间
            )
            
            # 计算响应时间
            response_time = (time.time() - start_time) * 1000  # 转换为毫秒
            
            # 更新结果
            result.update({
                "status": "success" if response.status_code < 400 else "failed",
                "response_time": round(response_time, 2),
                "status_code": response.status_code,
                "response_size": len(response.content) if response.content else 0
            })
            
            logger.info(f"服务检查完成: {service_name}, 状态码: {response.status_code}, 响应时间: {response_time:.2f}ms")
            
        except httpx.TimeoutException:
            service_timeout = getattr(service, 'timeout', 30)
            service_name = getattr(service, 'name', f'service_{result["service_id"]}')
            result.update({
                "status": "timeout",
                "error_message": f"请求超时 (>{service_timeout}s)",
                "error_type": "timeout"
            })
            logger.warning(f"服务检查超时: {service_name}")
            
        except httpx.ConnectError as e:
            service_name = getattr(service, 'name', f'service_{result["service_id"]}')
            result.update({
                "status": "failed",
                "error_message": f"连接错误: {str(e)}",
                "error_type": "connection_error"
            })
            logger.error(f"服务连接错误: {service_name}, 错误: {str(e)}")
            
        except Exception as e:
            service_name = getattr(service, 'name', f'service_{result["service_id"]}')
            result.update({
                "status": "failed",
                "error_message": f"未知错误: {str(e)}",
                "error_type": "unknown_error"
            })
            logger.error(f"服务检查异常: {service_name}, 错误: {str(e)}")
        
        return result
    
    async def save_monitor_log(self, result: Dict[str, Any]) -> Optional[MonitorLog]:
        """保存监控日志"""
        try:
            with get_db_session() as db:  # 使用同步上下文管理器
                log = MonitorLog(**result)
                db.add(log)
                db.flush()  # 刷新以获取ID
                await asyncio.sleep(0)  # 让出控制权
                return log
        except Exception as e:
            logger.error(f"保存监控日志失败: {str(e)}")
            return None
    
    async def update_service_status(self, service_id: int, status: str, check_time: datetime):
        """更新服务状态"""
        try:
            with get_db_session() as db:
                service = db.query(ServiceModel).filter(ServiceModel.id == service_id).first()
                if service:
                    service.status = status
                    service.last_check_time = check_time
                    if status == "success":
                        service.last_success_time = check_time
                    await asyncio.sleep(0)  # 让出控制权
        except Exception as e:
            logger.error(f"更新服务状态失败: service_id={service_id}, 错误: {str(e)}")
    
    async def check_and_alert(self, service: ServiceModel) -> Optional[MonitorLog]:
        """检查服务并处理告警"""
        # 获取服务的前一个状态（安全访问属性）
        previous_status = getattr(service, 'status', 'unknown')
        service_name = getattr(service, 'name', f'service_{getattr(service, "id", "unknown")}')
        
        # 执行服务检查
        result = await self.check_service(service)
        current_status = result["status"]
        
        # 保存监控日志
        log = await self.save_monitor_log(result)
        if not log:
            logger.error(f"保存监控日志失败，跳过后续处理: {service_name}")
            return None
        
        # 更新服务状态
        await self.update_service_status(
            getattr(service, 'id', 0), 
            current_status, 
            result["check_time"]
        )
        
        # 处理告警和恢复通知
        enable_alert = getattr(service, 'enable_alert', False)
        if enable_alert:
            try:
                alert_sent = False
                alert_methods = getattr(service, 'alert_methods', [])
                
                # 检查是否需要发送恢复通知
                if (previous_status in ["failed", "timeout"] and current_status == "success"):
                    # 服务从异常状态恢复到正常状态，发送恢复通知
                    await alert_service.send_recovery_alert(service, result)
                    alert_sent = True
                    logger.info(f"服务恢复通知已发送: {service_name}")
                
                # 检查是否需要发送告警
                elif current_status in ["failed", "timeout"]:
                    # 服务异常，发送告警
                    await alert_service.send_alert(service, result)
                    alert_sent = True
                    logger.info(f"服务告警已发送: {service_name}")
                
                # 更新告警状态
                if alert_sent and log:
                    try:
                        with get_db_session() as db:
                            # 重新获取log对象以避免会话问题
                            log_to_update = db.query(MonitorLog).filter(MonitorLog.id == log.id).first()
                            if log_to_update:
                                log_to_update.alert_sent = True
                                log_to_update.alert_methods = alert_methods
                    except Exception as e:
                        logger.error(f"更新告警状态失败: {str(e)}")
                         
            except Exception as e:
                logger.error(f"发送告警/恢复通知失败: {service_name}, 错误: {str(e)}")
        
        return log
    
    async def get_active_services(self) -> list[ServiceModel]:
        """获取所有活跃的监控服务"""
        try:
            with get_db_session() as db:
                services = db.query(ServiceModel).filter(ServiceModel.is_active == True).all()
                # 将服务对象从会话中分离，避免会话绑定问题
                detached_services = []
                for service in services:
                    # 预先访问所有需要的属性
                    service_data = {
                        "id": service.id,
                        "name": service.name,
                        "url": service.url,
                        "method": service.method,
                        "timeout": service.timeout,
                        "interval": service.interval,
                        "retry_count": service.retry_count,
                        "is_active": service.is_active,
                        "status": service.status,
                        "last_check_time": service.last_check_time,
                        "last_success_time": service.last_success_time,
                        "enable_alert": service.enable_alert,
                        "alert_methods": service.alert_methods,
                        "alert_contacts": service.alert_contacts,
                        "description": service.description,
                        "tags": service.tags,
                        "created_at": service.created_at,
                        "updated_at": service.updated_at
                    }
                    
                    # 从会话中分离原对象
                    db.expunge(service)
                    
                    # 创建新的分离对象
                    detached_service = ServiceModel(**service_data)
                    detached_services.append(detached_service)
                
                return detached_services
        except Exception as e:
            logger.error(f"获取活跃服务列表失败: {str(e)}")
            return []
    
    async def close(self):
        """关闭HTTP客户端"""
        if not self._closed:
            self._closed = True
            await self.client.aclose()
            logger.info("MonitorService HTTP客户端已关闭")
    
    def get_client_info(self):
        """获取HTTP客户端信息"""
        return {
            "is_closed": self._closed,
            "limits": {
                "max_keepalive_connections": self.client._limits.max_keepalive_connections,
                "max_connections": self.client._limits.max_connections,
                "keepalive_expiry": self.client._limits.keepalive_expiry
            }
        }


# 创建全局监控服务实例
monitor_service = MonitorService()