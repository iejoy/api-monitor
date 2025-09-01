"""
数据库维护管理API
"""
from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.data_cleanup import data_cleanup_service
from app.services.maintenance_scheduler import maintenance_scheduler

router = APIRouter()


@router.get("/status")
async def get_maintenance_status():
    """获取维护系统状态"""
    try:
        job_status = maintenance_scheduler.get_job_status()
        table_stats = data_cleanup_service.get_table_stats()
        cleanup_stats = data_cleanup_service.get_cleanup_stats(days=7)
        
        return {
            "scheduler": job_status,
            "table_stats": table_stats,
            "cleanup_stats": cleanup_stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取维护状态失败: {str(e)}")


@router.post("/cleanup")
async def manual_cleanup(
    retention_days: int = Body(90, ge=7, le=365, description="保留天数"),
    dry_run: bool = Body(True, description="是否为试运行"),
    service_id: Optional[int] = Body(None, description="特定服务ID")
):
    """手动执行数据清理"""
    try:
        result = data_cleanup_service.cleanup_old_logs(
            retention_days=retention_days,
            dry_run=dry_run,
            service_id=service_id
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据清理失败: {str(e)}")


@router.post("/optimize")
async def optimize_table():
    """手动优化数据库表"""
    try:
        result = data_cleanup_service.optimize_table()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"表优化失败: {str(e)}")


@router.post("/partition")
async def create_partition(
    target_year: int = Body(..., ge=2024, le=2030, description="目标年份"),
    target_month: int = Body(..., ge=1, le=12, description="目标月份")
):
    """手动创建分区"""
    try:
        target_date = datetime(target_year, target_month, 1)
        result = data_cleanup_service.create_partition_if_needed(target_date)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建分区失败: {str(e)}")


@router.get("/partitions")
async def list_partitions(db: Session = Depends(get_db)):
    """列出所有分区信息"""
    try:
        from sqlalchemy import text
        
        sql = """
        SELECT 
            partition_name,
            partition_description,
            table_rows,
            ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb,
            partition_comment
        FROM information_schema.partitions 
        WHERE table_schema = DATABASE() 
        AND table_name = 'monitor_logs'
        AND partition_name IS NOT NULL
        ORDER BY partition_name
        """
        
        result = db.execute(text(sql)).fetchall()
        
        partitions = []
        for row in result:
            partitions.append({
                "name": row.partition_name,
                "description": row.partition_description,
                "rows": row.table_rows or 0,
                "size_mb": float(row.size_mb) if row.size_mb else 0,
                "comment": row.partition_comment
            })
        
        return {"partitions": partitions}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取分区信息失败: {str(e)}")


@router.get("/indexes")
async def list_indexes(db: Session = Depends(get_db)):
    """列出所有索引信息"""
    try:
        from sqlalchemy import text
        
        sql = """
        SELECT 
            index_name,
            column_name,
            seq_in_index,
            non_unique,
            index_type,
            cardinality
        FROM information_schema.statistics 
        WHERE table_schema = DATABASE() 
        AND table_name = 'monitor_logs'
        ORDER BY index_name, seq_in_index
        """
        
        result = db.execute(text(sql)).fetchall()
        
        indexes = {}
        for row in result:
            index_name = row.index_name
            if index_name not in indexes:
                indexes[index_name] = {
                    "name": index_name,
                    "columns": [],
                    "unique": row.non_unique == 0,
                    "type": row.index_type,
                    "cardinality": row.cardinality
                }
            
            indexes[index_name]["columns"].append({
                "name": row.column_name,
                "position": row.seq_in_index
            })
        
        return {"indexes": list(indexes.values())}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取索引信息失败: {str(e)}")


@router.post("/scheduler/start")
async def start_scheduler():
    """启动维护调度器"""
    try:
        await maintenance_scheduler.start()
        return {"message": "维护调度器启动成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动调度器失败: {str(e)}")


@router.post("/scheduler/stop")
async def stop_scheduler():
    """停止维护调度器"""
    try:
        await maintenance_scheduler.stop()
        return {"message": "维护调度器停止成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止调度器失败: {str(e)}")


@router.put("/scheduler/config")
async def update_scheduler_config(config: Dict[str, Any] = Body(...)):
    """更新调度器配置"""
    try:
        maintenance_scheduler.update_config(config)
        return {"message": "调度器配置更新成功", "config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")


@router.post("/scheduler/jobs/{job_id}/run")
async def run_job_now(job_id: str):
    """立即执行指定任务"""
    try:
        result = await maintenance_scheduler.run_job_now(job_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行任务失败: {str(e)}")


@router.get("/history")
async def get_maintenance_history(
    days: int = Query(7, ge=1, le=30, description="查询天数")
):
    """获取维护历史记录"""
    try:
        result = maintenance_scheduler.get_maintenance_history(days)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取维护历史失败: {str(e)}")


@router.get("/performance/analysis")
async def analyze_performance(
    days: int = Query(7, ge=1, le=30, description="分析天数"),
    db: Session = Depends(get_db)
):
    """性能分析报告"""
    try:
        from sqlalchemy import text
        
        # 查询性能统计
        sql = """
        SELECT 
            -- 查询性能统计
            COUNT(*) as total_queries,
            AVG(response_time) as avg_response_time,
            MIN(response_time) as min_response_time,
            MAX(response_time) as max_response_time,
            STDDEV(response_time) as stddev_response_time,
            
            -- 状态分布
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
            SUM(CASE WHEN status = 'timeout' THEN 1 ELSE 0 END) as timeout_count,
            
            -- 时间分布
            COUNT(CASE WHEN HOUR(check_time) BETWEEN 0 AND 5 THEN 1 END) as night_queries,
            COUNT(CASE WHEN HOUR(check_time) BETWEEN 6 AND 11 THEN 1 END) as morning_queries,
            COUNT(CASE WHEN HOUR(check_time) BETWEEN 12 AND 17 THEN 1 END) as afternoon_queries,
            COUNT(CASE WHEN HOUR(check_time) BETWEEN 18 AND 23 THEN 1 END) as evening_queries
            
        FROM monitor_logs 
        WHERE check_time >= DATE_SUB(NOW(), INTERVAL :days DAY)
        AND response_time IS NOT NULL
        """
        
        result = db.execute(text(sql), {"days": days}).fetchone()
        
        # 获取慢查询统计
        slow_queries_sql = """
        SELECT 
            service_id,
            s.name as service_name,
            COUNT(*) as slow_query_count,
            AVG(response_time) as avg_slow_response_time,
            MAX(response_time) as max_response_time
        FROM monitor_logs ml
        JOIN monitor_services s ON ml.service_id = s.id
        WHERE ml.check_time >= DATE_SUB(NOW(), INTERVAL :days DAY)
        AND ml.response_time > 5000  -- 超过5秒的查询
        GROUP BY service_id, s.name
        ORDER BY slow_query_count DESC
        LIMIT 10
        """
        
        slow_queries = db.execute(text(slow_queries_sql), {"days": days}).fetchall()
        
        # 获取表大小趋势
        table_stats = data_cleanup_service.get_table_stats()
        
        analysis = {
            "period_days": days,
            "query_performance": {
                "total_queries": result.total_queries or 0,
                "avg_response_time": round(float(result.avg_response_time), 2) if result.avg_response_time else 0,
                "min_response_time": round(float(result.min_response_time), 2) if result.min_response_time else 0,
                "max_response_time": round(float(result.max_response_time), 2) if result.max_response_time else 0,
                "stddev_response_time": round(float(result.stddev_response_time), 2) if result.stddev_response_time else 0
            },
            "status_distribution": {
                "success_count": result.success_count or 0,
                "failed_count": result.failed_count or 0,
                "timeout_count": result.timeout_count or 0,
                "success_rate": round((result.success_count or 0) / (result.total_queries or 1) * 100, 2)
            },
            "time_distribution": {
                "night_queries": result.night_queries or 0,
                "morning_queries": result.morning_queries or 0,
                "afternoon_queries": result.afternoon_queries or 0,
                "evening_queries": result.evening_queries or 0
            },
            "slow_queries": [
                {
                    "service_id": row.service_id,
                    "service_name": row.service_name,
                    "slow_query_count": row.slow_query_count,
                    "avg_slow_response_time": round(float(row.avg_slow_response_time), 2),
                    "max_response_time": round(float(row.max_response_time), 2)
                }
                for row in slow_queries
            ],
            "table_stats": table_stats,
            "recommendations": []
        }
        
        # 生成优化建议
        if analysis["query_performance"]["avg_response_time"] > 1000:
            analysis["recommendations"].append("平均响应时间较高，建议检查索引优化")
        
        if analysis["status_distribution"]["success_rate"] < 95:
            analysis["recommendations"].append("成功率较低，建议检查服务健康状况")
        
        if table_stats.get("total_size_mb", 0) > 1000:
            analysis["recommendations"].append("表大小超过1GB，建议执行数据清理")
        
        if len(analysis["slow_queries"]) > 0:
            analysis["recommendations"].append("存在慢查询，建议优化相关服务")
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"性能分析失败: {str(e)}")


@router.post("/backup/export")
async def export_data(
    start_date: datetime = Body(..., description="开始日期"),
    end_date: datetime = Body(..., description="结束日期"),
    service_ids: Optional[list[int]] = Body(None, description="服务ID列表"),
    format: str = Body("json", regex="^(json|csv)$", description="导出格式"),
    db: Session = Depends(get_db)
):
    """导出监控数据"""
    try:
        from sqlalchemy import text
        import json
        import csv
        import io
        from fastapi.responses import StreamingResponse
        
        # 构建查询条件
        conditions = ["ml.check_time >= :start_date", "ml.check_time <= :end_date"]
        params = {"start_date": start_date, "end_date": end_date}
        
        if service_ids:
            conditions.append("ml.service_id IN :service_ids")
            params["service_ids"] = tuple(service_ids)
        
        where_clause = " AND ".join(conditions)
        
        sql = f"""
        SELECT 
            ml.id,
            ml.service_id,
            s.name as service_name,
            ml.status,
            ml.response_time,
            ml.status_code,
            ml.error_message,
            ml.check_time,
            ml.alert_sent
        FROM monitor_logs ml
        JOIN monitor_services s ON ml.service_id = s.id
        WHERE {where_clause}
        ORDER BY ml.check_time DESC
        LIMIT 10000
        """
        
        result = db.execute(text(sql), params).fetchall()
        
        if format == "json":
            data = []
            for row in result:
                data.append({
                    "id": row.id,
                    "service_id": row.service_id,
                    "service_name": row.service_name,
                    "status": row.status,
                    "response_time": row.response_time,
                    "status_code": row.status_code,
                    "error_message": row.error_message,
                    "check_time": row.check_time.isoformat() if row.check_time else None,
                    "alert_sent": row.alert_sent
                })
            
            json_str = json.dumps(data, ensure_ascii=False, indent=2)
            
            return StreamingResponse(
                io.StringIO(json_str),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=monitor_logs_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.json"}
            )
        
        elif format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            
            # 写入表头
            writer.writerow([
                "ID", "服务ID", "服务名称", "状态", "响应时间", "状态码", 
                "错误信息", "检查时间", "已发送告警"
            ])
            
            # 写入数据
            for row in result:
                writer.writerow([
                    row.id,
                    row.service_id,
                    row.service_name,
                    row.status,
                    row.response_time,
                    row.status_code,
                    row.error_message,
                    row.check_time.isoformat() if row.check_time else "",
                    "是" if row.alert_sent else "否"
                ])
            
            output.seek(0)
            
            return StreamingResponse(
                io.StringIO(output.getvalue()),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=monitor_logs_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"}
            )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据导出失败: {str(e)}")