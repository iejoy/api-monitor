"""
任务调度服务
"""
import asyncio
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor

from app.services.monitor import monitor_service

logger = logging.getLogger(__name__)


class SchedulerService:
    """调度器服务类"""
    
    def __init__(self):
        # 配置调度器
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()
        }
        job_defaults = {
            'coalesce': False,
            'max_instances': 3
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Asia/Shanghai'
        )
        
        self._running = False
    
    def start(self):
        """启动调度器"""
        if not self._running:
            self.scheduler.start()
            self._running = True
            
            # 添加定期刷新任务的作业
            self.scheduler.add_job(
                func=self._refresh_monitor_jobs,
                trigger=IntervalTrigger(minutes=1),  # 每分钟检查一次
                id='refresh_monitor_jobs',
                name='刷新监控任务',
                replace_existing=True
            )
            
            logger.info("调度器已启动")
    
    def shutdown(self):
        """关闭调度器"""
        if self._running:
            self.scheduler.shutdown()
            self._running = False
            logger.info("调度器已关闭")
    
    async def _refresh_monitor_jobs(self):
        """刷新监控任务"""
        try:
            # 获取所有活跃的监控服务
            services = await monitor_service.get_active_services()
            
            # 获取当前所有监控任务的ID
            current_job_ids = set()
            for job in self.scheduler.get_jobs():
                if job.id.startswith('monitor_'):
                    current_job_ids.add(job.id)
            
            # 需要的任务ID
            needed_job_ids = set()
            
            for service in services:
                job_id = f"monitor_{service.id}"
                needed_job_ids.add(job_id)
                
                # 检查任务是否存在
                existing_job = self.scheduler.get_job(job_id)
                
                if existing_job:
                    # 检查间隔是否需要更新
                    current_interval = existing_job.trigger.interval.total_seconds()
                    if current_interval != service.interval:
                        # 更新任务间隔
                        self.scheduler.modify_job(
                            job_id,
                            trigger=IntervalTrigger(seconds=service.interval)
                        )
                        logger.info(f"更新监控任务间隔: {service.name} -> {service.interval}秒")
                else:
                    # 添加新的监控任务
                    self.scheduler.add_job(
                        func=self._monitor_job,
                        trigger=IntervalTrigger(seconds=service.interval),
                        args=[service.id],
                        id=job_id,
                        name=f"监控服务: {service.name}",
                        replace_existing=True
                    )
                    logger.info(f"添加监控任务: {service.name}, 间隔: {service.interval}秒")
            
            # 删除不再需要的任务
            for job_id in current_job_ids - needed_job_ids:
                self.scheduler.remove_job(job_id)
                logger.info(f"删除监控任务: {job_id}")
                
        except Exception as e:
            logger.error(f"刷新监控任务失败: {str(e)}")
    
    async def _monitor_job(self, service_id: int):
        """执行监控任务"""
        try:
            # 获取服务信息
            from app.core.database import SessionLocal
            from app.models.service import MonitorService as ServiceModel
            
            db = SessionLocal()
            try:
                service = db.query(ServiceModel).filter(ServiceModel.id == service_id).first()
                if not service or not service.is_active:
                    logger.warning(f"服务不存在或已禁用: {service_id}")
                    return
                
                # 预先访问所有可能需要的属性，避免懒加载问题
                service_data = {
                    "id": service.id,
                    "name": service.name,
                    "url": service.url,
                    "method": service.method,
                    "timeout": service.timeout,
                    "status": service.status,
                    "is_active": service.is_active,
                    "enable_alert": service.enable_alert,
                    "alert_methods": service.alert_methods,
                    "last_check_time": service.last_check_time,
                    "last_success_time": service.last_success_time,
                    "created_at": service.created_at,
                    "updated_at": service.updated_at
                }
                
                # 从会话中分离对象
                db.expunge(service)
                
            finally:
                db.close()
            
            # 重新创建服务对象，避免会话绑定问题
            detached_service = ServiceModel(**service_data)
            
            # 执行监控检查
            logger.debug(f"执行监控任务: {detached_service.name}")
            await monitor_service.check_and_alert(detached_service)
            
        except Exception as e:
            logger.error(f"监控任务执行失败 (service_id: {service_id}): {str(e)}")
    
    def add_monitor_job(self, service_id: int, service_name: str, interval: int):
        """添加监控任务"""
        job_id = f"monitor_{service_id}"
        
        self.scheduler.add_job(
            func=self._monitor_job,
            trigger=IntervalTrigger(seconds=interval),
            args=[service_id],
            id=job_id,
            name=f"监控服务: {service_name}",
            replace_existing=True
        )
        
        logger.info(f"添加监控任务: {service_name}, 间隔: {interval}秒")
    
    def remove_monitor_job(self, service_id: int):
        """删除监控任务"""
        job_id = f"monitor_{service_id}"
        
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"删除监控任务: {job_id}")
        except Exception as e:
            logger.warning(f"删除监控任务失败: {job_id}, 错误: {str(e)}")
    
    def update_monitor_job(self, service_id: int, service_name: str, interval: int):
        """更新监控任务"""
        job_id = f"monitor_{service_id}"
        
        try:
            self.scheduler.modify_job(
                job_id,
                trigger=IntervalTrigger(seconds=interval),
                name=f"监控服务: {service_name}"
            )
            logger.info(f"更新监控任务: {service_name}, 新间隔: {interval}秒")
        except Exception as e:
            logger.warning(f"更新监控任务失败: {job_id}, 错误: {str(e)}")
            # 如果更新失败，尝试重新添加
            self.add_monitor_job(service_id, service_name, interval)
    
    def get_job_status(self) -> dict:
        """获取任务状态"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return {
            "running": self._running,
            "total_jobs": len(jobs),
            "jobs": jobs
        }


# 创建全局调度器服务实例
scheduler_service = SchedulerService()