"""
数据清理服务 - 优化版本
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text, func

from app.core.database import get_db_sync, get_db_session
from app.models.monitor_log import MonitorLog

logger = logging.getLogger(__name__)


class DataCleanupService:
    """数据清理服务类"""
    
    def __init__(self):
        self.default_retention_days = 90  # 默认保留90天
        self.batch_size = 1000  # 批次大小
        self.max_batch_time = 5  # 每批最大执行时间（秒）
    
    async def cleanup_old_logs_async(
        self, 
        retention_days: int = None, 
        dry_run: bool = True,
        service_id: int = None
    ) -> Dict[str, Any]:
        """
        异步清理旧的监控日志
        
        Args:
            retention_days: 保留天数，默认90天
            dry_run: 是否为试运行模式
            service_id: 特定服务ID，None表示清理所有服务
        
        Returns:
            清理结果统计
        """
        if retention_days is None:
            retention_days = self.default_retention_days
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        try:
            async with get_db_session() as db:
                # 构建查询条件
                conditions = ["check_time < :cutoff_date"]
                params = {"cutoff_date": cutoff_date}
                
                if service_id:
                    conditions.append("service_id = :service_id")
                    params["service_id"] = service_id
                
                where_clause = " AND ".join(conditions)
                
                # 获取要删除的记录数和统计信息
                stats_sql = f"""
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(DISTINCT service_id) as affected_services,
                    MIN(check_time) as oldest_record,
                    MAX(check_time) as newest_record,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                    SUM(CASE WHEN status = 'timeout' THEN 1 ELSE 0 END) as timeout_count
                FROM monitor_logs 
                WHERE {where_clause}
                """
                
                stats_result = db.execute(text(stats_sql), params).fetchone()
                
                result = {
                    "retention_days": retention_days,
                    "cutoff_date": cutoff_date.isoformat(),
                    "total_count": stats_result.total_count or 0,
                    "affected_services": stats_result.affected_services or 0,
                    "oldest_record": stats_result.oldest_record.isoformat() if stats_result.oldest_record else None,
                    "newest_record": stats_result.newest_record.isoformat() if stats_result.newest_record else None,
                    "success_count": stats_result.success_count or 0,
                    "failed_count": stats_result.failed_count or 0,
                    "timeout_count": stats_result.timeout_count or 0,
                    "dry_run": dry_run,
                    "deleted_count": 0
                }
                
                if result["total_count"] == 0:
                    result["message"] = "没有需要清理的数据"
                    return result
                
                if dry_run:
                    result["message"] = f"试运行模式：将删除 {result['total_count']} 条记录"
                    return result
                
                # 执行实际删除
                deleted_count = await self._batch_delete_async(db, where_clause, params)
                result["deleted_count"] = deleted_count
                result["message"] = f"成功清理 {deleted_count} 条监控日志记录"
                
                # 记录清理日志
                await self._log_cleanup_operation_async(db, result)
                
                return result
                
        except Exception as e:
            logger.error(f"异步数据清理失败: {str(e)}")
            raise
    
    def cleanup_old_logs(
        self, 
        retention_days: int = None, 
        dry_run: bool = True,
        service_id: int = None
    ) -> Dict[str, Any]:
        """
        同步清理旧的监控日志（保持向后兼容）
        """
        if retention_days is None:
            retention_days = self.default_retention_days
        
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        with get_db_sync() as db:
            try:
                # 构建查询条件
                conditions = ["check_time < :cutoff_date"]
                params = {"cutoff_date": cutoff_date}
                
                if service_id:
                    conditions.append("service_id = :service_id")
                    params["service_id"] = service_id
                
                where_clause = " AND ".join(conditions)
                
                # 获取要删除的记录数和统计信息
                stats_sql = f"""
                SELECT 
                    COUNT(*) as total_count,
                    COUNT(DISTINCT service_id) as affected_services,
                    MIN(check_time) as oldest_record,
                    MAX(check_time) as newest_record,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                    SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                    SUM(CASE WHEN status = 'timeout' THEN 1 ELSE 0 END) as timeout_count
                FROM monitor_logs 
                WHERE {where_clause}
                """
                
                stats_result = db.execute(text(stats_sql), params).fetchone()
                
                result = {
                    "retention_days": retention_days,
                    "cutoff_date": cutoff_date.isoformat(),
                    "total_count": stats_result.total_count or 0,
                    "affected_services": stats_result.affected_services or 0,
                    "oldest_record": stats_result.oldest_record.isoformat() if stats_result.oldest_record else None,
                    "newest_record": stats_result.newest_record.isoformat() if stats_result.newest_record else None,
                    "success_count": stats_result.success_count or 0,
                    "failed_count": stats_result.failed_count or 0,
                    "timeout_count": stats_result.timeout_count or 0,
                    "dry_run": dry_run,
                    "deleted_count": 0
                }
                
                if result["total_count"] == 0:
                    result["message"] = "没有需要清理的数据"
                    return result
                
                if dry_run:
                    result["message"] = f"试运行模式：将删除 {result['total_count']} 条记录"
                    return result
                
                # 执行实际删除
                deleted_count = self._batch_delete(db, where_clause, params)
                result["deleted_count"] = deleted_count
                result["message"] = f"成功清理 {deleted_count} 条监控日志记录"
                
                # 记录清理日志
                self._log_cleanup_operation(db, result)
                
                return result
                
            except Exception as e:
                logger.error(f"数据清理失败: {str(e)}")
                raise
    
    async def _batch_delete_async(self, db: Session, where_clause: str, params: Dict) -> int:
        """异步分批删除数据，避免长时间锁表"""
        deleted_count = 0
        batch_count = 0
        
        while True:
            batch_start_time = datetime.now()
            
            delete_sql = f"""
            DELETE FROM monitor_logs 
            WHERE {where_clause}
            LIMIT :batch_size
            """
            params["batch_size"] = self.batch_size
            
            result = db.execute(text(delete_sql), params)
            batch_deleted = result.rowcount
            
            if batch_deleted == 0:
                break
                
            deleted_count += batch_deleted
            batch_count += 1
            
            logger.info(f"批次 {batch_count}: 删除 {batch_deleted} 条记录，累计删除 {deleted_count} 条")
            
            # 让出控制权，避免阻塞事件循环
            await asyncio.sleep(0.1)
            
            # 检查批次执行时间，避免长时间占用数据库
            batch_time = (datetime.now() - batch_start_time).total_seconds()
            if batch_time > self.max_batch_time:
                logger.warning(f"批次执行时间过长 ({batch_time:.2f}s)，暂停片刻")
                await asyncio.sleep(1)
            
            # 如果删除的记录数小于批次大小，说明已经删除完毕
            if batch_deleted < self.batch_size:
                break
        
        return deleted_count
    
    def _batch_delete(self, db: Session, where_clause: str, params: Dict) -> int:
        """同步分批删除数据，避免长时间锁表"""
        deleted_count = 0
        
        while True:
            delete_sql = f"""
            DELETE FROM monitor_logs 
            WHERE {where_clause}
            LIMIT :batch_size
            """
            params["batch_size"] = self.batch_size
            
            result = db.execute(text(delete_sql), params)
            batch_deleted = result.rowcount
            
            if batch_deleted == 0:
                break
                
            deleted_count += batch_deleted
            
            logger.info(f"已删除 {batch_deleted} 条记录，累计删除 {deleted_count} 条")
            
            # 如果删除的记录数小于批次大小，说明已经删除完毕
            if batch_deleted < self.batch_size:
                break
        
        return deleted_count
    
    async def _log_cleanup_operation_async(self, db: Session, result: Dict[str, Any]):
        """异步记录清理操作日志"""
        try:
            log_sql = """
            INSERT INTO system_logs (operation, message, details, created_at) 
            VALUES ('data_cleanup', :message, :details, NOW())
            """
            
            details = {
                "retention_days": result["retention_days"],
                "deleted_count": result["deleted_count"],
                "affected_services": result["affected_services"],
                "cutoff_date": result["cutoff_date"]
            }
            
            db.execute(text(log_sql), {
                "message": result["message"],
                "details": str(details)
            })
            await asyncio.sleep(0)  # 让出控制权
        except Exception as e:
            logger.warning(f"记录清理日志失败: {str(e)}")
    
    def _log_cleanup_operation(self, db: Session, result: Dict[str, Any]):
        """记录清理操作日志"""
        try:
            log_sql = """
            INSERT INTO system_logs (operation, message, details, created_at) 
            VALUES ('data_cleanup', :message, :details, NOW())
            """
            
            details = {
                "retention_days": result["retention_days"],
                "deleted_count": result["deleted_count"],
                "affected_services": result["affected_services"],
                "cutoff_date": result["cutoff_date"]
            }
            
            db.execute(text(log_sql), {
                "message": result["message"],
                "details": str(details)
            })
        except Exception as e:
            logger.warning(f"记录清理日志失败: {str(e)}")
    
    def get_cleanup_stats(self, days: int = 30) -> Dict[str, Any]:
        """获取清理统计信息"""
        with get_db_sync() as db:
            # 获取数据分布统计
            stats_sql = """
            SELECT 
                DATE(check_time) as date,
                COUNT(*) as record_count,
                COUNT(DISTINCT service_id) as service_count,
                SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
                SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
                AVG(CASE WHEN response_time IS NOT NULL THEN response_time END) as avg_response_time
            FROM monitor_logs 
            WHERE check_time >= :start_date
            GROUP BY DATE(check_time)
            ORDER BY date DESC
            LIMIT :days
            """
            
            start_date = datetime.now() - timedelta(days=days)
            result = db.execute(text(stats_sql), {
                "start_date": start_date,
                "days": days
            }).fetchall()
            
            daily_stats = []
            for row in result:
                daily_stats.append({
                    "date": row.date.isoformat(),
                    "record_count": row.record_count,
                    "service_count": row.service_count,
                    "success_count": row.success_count,
                    "failed_count": row.failed_count,
                    "avg_response_time": round(row.avg_response_time, 2) if row.avg_response_time else None
                })
            
            # 获取总体统计
            total_sql = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT service_id) as total_services,
                MIN(check_time) as oldest_record,
                MAX(check_time) as newest_record,
                AVG(CASE WHEN response_time IS NOT NULL THEN response_time END) as overall_avg_response_time
            FROM monitor_logs
            """
            
            total_result = db.execute(text(total_sql)).fetchone()
            
            # 获取存储空间统计
            size_sql = """
            SELECT 
                ROUND(
                    (data_length + index_length) / 1024 / 1024, 2
                ) AS size_mb
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'monitor_logs'
            """
            
            size_result = db.execute(text(size_sql)).fetchone()
            
            return {
                "daily_stats": daily_stats,
                "total_records": total_result.total_records,
                "total_services": total_result.total_services,
                "oldest_record": total_result.oldest_record.isoformat() if total_result.oldest_record else None,
                "newest_record": total_result.newest_record.isoformat() if total_result.newest_record else None,
                "overall_avg_response_time": round(total_result.overall_avg_response_time, 2) if total_result.overall_avg_response_time else None,
                "table_size_mb": float(size_result.size_mb) if size_result.size_mb else 0
            }
    
    def optimize_table(self) -> Dict[str, Any]:
        """优化表结构"""
        with get_db_sync() as db:
            # 分析表
            db.execute(text("ANALYZE TABLE monitor_logs"))
            
            # 优化表
            result = db.execute(text("OPTIMIZE TABLE monitor_logs")).fetchone()
            
            # 获取优化后的统计信息
            stats = self.get_table_stats()
            
            return {
                "message": "表优化完成",
                "optimize_result": result._asdict() if result else None,
                "table_stats": stats
            }
    
    def get_table_stats(self) -> Dict[str, Any]:
        """获取表统计信息"""
        with get_db_sync() as db:
            stats_sql = """
            SELECT 
                table_rows,
                ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb,
                ROUND(data_length / 1024 / 1024, 2) AS data_mb,
                ROUND(index_length / 1024 / 1024, 2) AS index_mb,
                ROUND(data_free / 1024 / 1024, 2) AS free_mb
            FROM information_schema.tables 
            WHERE table_schema = DATABASE() 
            AND table_name = 'monitor_logs'
            """
            
            result = db.execute(text(stats_sql)).fetchone()
            
            if result:
                return {
                    "table_rows": result.table_rows,
                    "total_size_mb": float(result.size_mb),
                    "data_size_mb": float(result.data_mb),
                    "index_size_mb": float(result.index_mb),
                    "free_space_mb": float(result.free_mb)
                }
            else:
                return {}
    
    def create_partition_if_needed(self, target_date: datetime = None) -> Dict[str, Any]:
        """根据需要创建新分区"""
        if target_date is None:
            target_date = datetime.now() + timedelta(days=30)  # 提前创建下个月的分区
        
        partition_name = f"p{target_date.year}{target_date.month:02d}"
        
        with get_db_sync() as db:
            # 检查分区是否已存在
            check_sql = """
            SELECT COUNT(*) as partition_exists
            FROM information_schema.partitions 
            WHERE table_schema = DATABASE() 
            AND table_name = 'monitor_logs' 
            AND partition_name = :partition_name
            """
            
            exists = db.execute(text(check_sql), {"partition_name": partition_name}).scalar()
            
            if exists > 0:
                return {
                    "message": f"分区 {partition_name} 已存在",
                    "partition_name": partition_name,
                    "created": False
                }
            
            # 计算分区值
            if target_date.month == 12:
                next_year = target_date.year + 1
                next_month = 1
            else:
                next_year = target_date.year
                next_month = target_date.month + 1
            
            partition_value = next_year * 100 + next_month
            
            # 创建分区
            create_sql = f"""
            ALTER TABLE monitor_logs ADD PARTITION (
                PARTITION {partition_name} VALUES LESS THAN ({partition_value})
            )
            """
            
            db.execute(text(create_sql))
            
            return {
                "message": f"成功创建分区 {partition_name}",
                "partition_name": partition_name,
                "partition_value": partition_value,
                "created": True
            }


# 创建全局数据清理服务实例
data_cleanup_service = DataCleanupService()