"""
维护任务调度器 - 优化版本
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from app.services.data_cleanup import data_cleanup_service
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class MaintenanceScheduler:
    """维护任务调度器"""
    
    def __init__(self):
        # 优化调度器配置
        jobstores = {
            'default': MemoryJobStore()
        }
        executors = {
            'default': AsyncIOExecutor()  # 限制并发执行的维护任务数
        }
        job_defaults = {
            'coalesce': True,  # 合并积压的任务
            'max_instances': 1,  # 每个任务最多只能有1个实例运行
            'misfire_grace_time': 300  # 任务错过执行时间的宽限时间（5分钟）
        }
        
        self.scheduler = AsyncIOScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Asia/Shanghai'
        )
        
        self.is_running = False
        self.maintenance_config = {
            "cleanup_enabled": True,
            "cleanup_retention_days": 90,
            "cleanup_schedule": "0 2 * * 0",  # 每周日凌晨2点
            "partition_enabled": True,
            "partition_schedule": "0 1 1 * *",  # 每月1号凌晨1点
            "optimize_enabled": True,
            "optimize_schedule": "0 3 1 * *",  # 每月1号凌晨3点
        }
        self._task_status = {}  # 记录任务执行状态
    
    async def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("维护调度器已在运行")
            return
        
        try:
            # 添加数据清理任务
            if self.maintenance_config["cleanup_enabled"]:
                self.scheduler.add_job(
                    self._cleanup_old_logs,
                    CronTrigger.from_crontab(self.maintenance_config["cleanup_schedule"]),
                    id="cleanup_old_logs",
                    name="清理旧日志数据",
                    max_instances=1,
                    coalesce=True
                )
                logger.info(f"已添加数据清理任务，调度: {self.maintenance_config['cleanup_schedule']}")
            
            # 添加分区管理任务
            if self.maintenance_config["partition_enabled"]:
                self.scheduler.add_job(
                    self._create_monthly_partition,
                    CronTrigger.from_crontab(self.maintenance_config["partition_schedule"]),
                    id="create_monthly_partition",
                    name="创建月度分区",
                    max_instances=1,
                    coalesce=True
                )
                logger.info(f"已添加分区管理任务，调度: {self.maintenance_config['partition_schedule']}")
            
            # 添加表优化任务
            if self.maintenance_config["optimize_enabled"]:
                self.scheduler.add_job(
                    self._optimize_tables,
                    CronTrigger.from_crontab(self.maintenance_config["optimize_schedule"]),
                    id="optimize_tables",
                    name="优化数据库表",
                    max_instances=1,
                    coalesce=True
                )
                logger.info(f"已添加表优化任务，调度: {self.maintenance_config['optimize_schedule']}")
            
            # 添加健康检查任务（每小时执行一次）
            self.scheduler.add_job(
                self._health_check,
                IntervalTrigger(hours=1),
                id="health_check",
                name="系统健康检查",
                max_instances=1,
                coalesce=True
            )
            
            # 添加连接池监控任务（每10分钟执行一次）
            self.scheduler.add_job(
                self._monitor_database_pool,
                IntervalTrigger(minutes=10),
                id="monitor_database_pool",
                name="数据库连接池监控",
                max_instances=1,
                coalesce=True
            )
            
            self.scheduler.start()
            self.is_running = True
            logger.info("维护调度器启动成功")
            
        except Exception as e:
            logger.error(f"启动维护调度器失败: {str(e)}")
            raise
    
    async def stop(self):
        """停止调度器"""
        if not self.is_running:
            return
        
        try:
            self.scheduler.shutdown(wait=True)
            self.is_running = False
            logger.info("维护调度器已停止")
        except Exception as e:
            logger.error(f"停止维护调度器失败: {str(e)}")
    
    async def _cleanup_old_logs(self):
        """清理旧日志数据任务"""
        task_id = "cleanup_old_logs"
        self._task_status[task_id] = {"status": "running", "start_time": datetime.now()}
        
        try:
            logger.info("开始执行数据清理任务")
            
            # 使用异步清理方法
            result = await data_cleanup_service.cleanup_old_logs_async(
                retention_days=self.maintenance_config["cleanup_retention_days"],
                dry_run=False
            )
            
            logger.info(f"数据清理任务完成: {result['message']}")
            
            # 如果删除了大量数据，执行表优化
            if result["deleted_count"] > 10000:
                logger.info("删除了大量数据，执行表优化")
                await self._optimize_tables()
            
            self._task_status[task_id] = {
                "status": "completed", 
                "start_time": self._task_status[task_id]["start_time"],
                "end_time": datetime.now(),
                "result": result
            }
            
        except Exception as e:
            logger.error(f"数据清理任务失败: {str(e)}")
            self._task_status[task_id] = {
                "status": "failed", 
                "start_time": self._task_status[task_id]["start_time"],
                "end_time": datetime.now(),
                "error": str(e)
            }
    
    async def _create_monthly_partition(self):
        """创建月度分区任务"""
        task_id = "create_monthly_partition"
        self._task_status[task_id] = {"status": "running", "start_time": datetime.now()}
        
        try:
            logger.info("开始执行分区创建任务")
            
            # 为下个月创建分区
            next_month = datetime.now().replace(day=1) + timedelta(days=32)
            next_month = next_month.replace(day=1)
            
            result = data_cleanup_service.create_partition_if_needed(next_month)
            
            logger.info(f"分区创建任务完成: {result['message']}")
            
            self._task_status[task_id] = {
                "status": "completed", 
                "start_time": self._task_status[task_id]["start_time"],
                "end_time": datetime.now(),
                "result": result
            }
            
        except Exception as e:
            logger.error(f"分区创建任务失败: {str(e)}")
            self._task_status[task_id] = {
                "status": "failed", 
                "start_time": self._task_status[task_id]["start_time"],
                "end_time": datetime.now(),
                "error": str(e)
            }
    
    async def _optimize_tables(self):
        """优化数据库表任务"""
        task_id = "optimize_tables"
        self._task_status[task_id] = {"status": "running", "start_time": datetime.now()}
        
        try:
            logger.info("开始执行表优化任务")
            
            # 表优化是同步操作，在单独的线程中执行
            result = await asyncio.get_event_loop().run_in_executor(
                None, 
                data_cleanup_service.optimize_table
            )
            
            logger.info(f"表优化任务完成: {result['message']}")
            
            self._task_status[task_id] = {
                "status": "completed", 
                "start_time": self._task_status[task_id]["start_time"],
                "end_time": datetime.now(),
                "result": result
            }
            
        except Exception as e:
            logger.error(f"表优化任务失败: {str(e)}")
            self._task_status[task_id] = {
                "status": "failed", 
                "start_time": self._task_status[task_id]["start_time"],
                "end_time": datetime.now(),
                "error": str(e)
            }
    
    async def _health_check(self):
        """系统健康检查任务"""
        task_id = "health_check"
        
        try:
            # 检查表大小
            stats = await asyncio.get_event_loop().run_in_executor(
                None,
                data_cleanup_service.get_table_stats
            )
            
            # 如果表大小超过阈值，记录警告
            if stats.get("total_size_mb", 0) > 1000:  # 1GB
                logger.warning(f"monitor_logs表大小已达到 {stats['total_size_mb']:.2f} MB")
            
            # 检查最旧的记录
            cleanup_stats = await asyncio.get_event_loop().run_in_executor(
                None,
                data_cleanup_service.get_cleanup_stats,
                1
            )
            
            if cleanup_stats.get("oldest_record"):
                oldest_date = datetime.fromisoformat(cleanup_stats["oldest_record"].replace('Z', '+00:00'))
                days_old = (datetime.now() - oldest_date.replace(tzinfo=None)).days
                
                if days_old > self.maintenance_config["cleanup_retention_days"] + 7:  # 超过保留期7天
                    logger.warning(f"发现超过保留期的数据，最旧记录: {days_old} 天前")
            
            # 更新任务状态
            self._task_status[task_id] = {
                "status": "completed",
                "last_run": datetime.now(),
                "stats": stats
            }
            
        except Exception as e:
            logger.error(f"健康检查任务失败: {str(e)}")
            self._task_status[task_id] = {
                "status": "failed",
                "last_run": datetime.now(),
                "error": str(e)
            }
    
    async def _monitor_database_pool(self):
        """监控数据库连接池状态"""
        try:
            from app.core.database import get_pool_status
            
            pool_status = get_pool_status()
            
            # 检查连接池使用情况
            usage_percentage = (pool_status["checked_out"] / pool_status["size"]) * 100 if pool_status["size"] > 0 else 0
            
            if usage_percentage > 80:
                logger.warning(f"数据库连接池使用率过高: {usage_percentage:.1f}% ({pool_status['checked_out']}/{pool_status['size']})")
            
            if pool_status["overflow"] > 0:
                logger.warning(f"数据库连接池溢出连接数: {pool_status['overflow']}")
            
            if pool_status["invalid"] > 0:
                logger.warning(f"数据库连接池无效连接数: {pool_status['invalid']}")
            
            self._task_status["monitor_database_pool"] = {
                "status": "completed",
                "last_run": datetime.now(),
                "pool_status": pool_status
            }
            
        except Exception as e:
            logger.error(f"数据库连接池监控失败: {str(e)}")
            self._task_status["monitor_database_pool"] = {
                "status": "failed",
                "last_run": datetime.now(),
                "error": str(e)
            }
    
    def update_config(self, config: Dict[str, Any]):
        """更新维护配置"""
        try:
            self.maintenance_config.update(config)
            
            # 如果调度器正在运行，重新启动以应用新配置
            if self.is_running:
                logger.info("配置已更新，重新启动调度器")
                asyncio.create_task(self._restart_scheduler())
            
        except Exception as e:
            logger.error(f"更新维护配置失败: {str(e)}")
            raise
    
    async def _restart_scheduler(self):
        """重新启动调度器"""
        await self.stop()
        await asyncio.sleep(2)  # 等待2秒确保完全停止
        await self.start()
    
    def get_job_status(self) -> Dict[str, Any]:
        """获取任务状态"""
        if not self.is_running:
            return {"status": "stopped", "jobs": [], "task_status": self._task_status}
        
        jobs = []
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": next_run.isoformat() if next_run else None,
                "trigger": str(job.trigger),
                "max_instances": job.max_instances,
                "coalesce": job.coalesce
            })
        
        return {
            "status": "running",
            "jobs": jobs,
            "config": self.maintenance_config,
            "task_status": self._task_status
        }
    
    async def run_job_now(self, job_id: str) -> Dict[str, Any]:
        """立即执行指定任务"""
        if not self.is_running:
            raise ValueError("调度器未运行")
        
        job = self.scheduler.get_job(job_id)
        if not job:
            raise ValueError(f"任务 {job_id} 不存在")
        
        try:
            logger.info(f"手动执行任务: {job.name}")
            
            if job_id == "cleanup_old_logs":
                await self._cleanup_old_logs()
            elif job_id == "create_monthly_partition":
                await self._create_monthly_partition()
            elif job_id == "optimize_tables":
                await self._optimize_tables()
            elif job_id == "health_check":
                await self._health_check()
            elif job_id == "monitor_database_pool":
                await self._monitor_database_pool()
            else:
                raise ValueError(f"未知任务类型: {job_id}")
            
            return {"message": f"任务 {job.name} 执行成功"}
            
        except Exception as e:
            logger.error(f"手动执行任务 {job.name} 失败: {str(e)}")
            raise
    
    def get_maintenance_history(self, days: int = 7) -> Dict[str, Any]:
        """获取维护历史记录"""
        try:
            from sqlalchemy import text
            from app.core.database import get_db_sync
            
            with get_db_sync() as db:
                sql = """
                SELECT 
                    operation,
                    message,
                    details,
                    created_at
                FROM system_logs 
                WHERE operation IN ('data_cleanup', 'partition_create', 'table_optimize')
                AND created_at >= :start_date
                ORDER BY created_at DESC
                LIMIT 100
                """
                
                start_date = datetime.now() - timedelta(days=days)
                result = db.execute(text(sql), {"start_date": start_date}).fetchall()
                
                history = []
                for row in result:
                    history.append({
                        "operation": row.operation,
                        "message": row.message,
                        "details": row.details,
                        "created_at": row.created_at.isoformat()
                    })
                
                return {"history": history}
                
        except Exception as e:
            logger.error(f"获取维护历史失败: {str(e)}")
            return {"history": []}


# 创建全局维护调度器实例
maintenance_scheduler = MaintenanceScheduler()