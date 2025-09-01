"""
监控日志管理API - 性能优化版本
"""
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc, func, text

from app.core.database import get_db
from app.models.monitor_log import MonitorLog
from app.models.service import MonitorService

router = APIRouter()


@router.get("/")
async def get_monitor_logs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页记录数"),
    service_id: Optional[int] = Query(None, description="服务ID筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    db: Session = Depends(get_db)
):
    """获取监控日志列表 - 优化版本"""
    # 使用JOIN查询避免N+1问题，利用复合索引
    query = db.query(MonitorLog, MonitorService.name.label('service_name'))\
              .join(MonitorService, MonitorLog.service_id == MonitorService.id)
    
    # 构建筛选条件 - 优化索引使用顺序
    # 优先使用时间范围筛选（通常选择性最高）
    if start_time:
        query = query.filter(MonitorLog.check_time >= start_time)
    if end_time:
        query = query.filter(MonitorLog.check_time <= end_time)
    
    # 然后是服务筛选
    if service_id:
        query = query.filter(MonitorLog.service_id == service_id)
    
    # 最后是状态筛选
    if status:
        query = query.filter(MonitorLog.status == status)
    
    # 获取总数 - 使用优化的计数查询
    count_query = db.query(func.count(MonitorLog.id))
    if start_time:
        count_query = count_query.filter(MonitorLog.check_time >= start_time)
    if end_time:
        count_query = count_query.filter(MonitorLog.check_time <= end_time)
    if service_id:
        count_query = count_query.filter(MonitorLog.service_id == service_id)
    if status:
        count_query = count_query.filter(MonitorLog.status == status)
    
    total = count_query.scalar()
    
    # 计算跳过记录数
    skip = (page - 1) * size
    
    # 分页查询 - 利用check_time索引排序
    results = query.order_by(desc(MonitorLog.check_time))\
                   .offset(skip)\
                   .limit(size)\
                   .all()
    
    # 构建返回数据
    logs_with_service_name = []
    for log, service_name in results:
        log_dict = {
            "id": log.id,
            "service_id": log.service_id,
            "service_name": service_name,
            "status": log.status,
            "response_time": log.response_time,
            "status_code": log.status_code,
            "error_message": log.error_message,
            "check_time": log.check_time.isoformat() if log.check_time else None,
            "alert_sent": log.alert_sent,
            "alert_methods": log.alert_methods
        }
        logs_with_service_name.append(log_dict)
    
    # 优化统计查询 - 使用单个查询获取所有统计数据
    stats_sql = """
    SELECT 
        COUNT(*) as total_stats,
        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed_count,
        SUM(CASE WHEN status = 'timeout' THEN 1 ELSE 0 END) as timeout_count,
        AVG(CASE WHEN response_time IS NOT NULL THEN response_time END) as avg_response_time
    FROM monitor_logs 
    WHERE 1=1
    """
    
    params = {}
    if start_time:
        stats_sql += " AND check_time >= :start_time"
        params["start_time"] = start_time
    if end_time:
        stats_sql += " AND check_time <= :end_time"
        params["end_time"] = end_time
    if service_id:
        stats_sql += " AND service_id = :service_id"
        params["service_id"] = service_id
    if status:
        stats_sql += " AND status = :status"
        params["status"] = status
    
    stats_result = db.execute(text(stats_sql), params).fetchone()
    
    stats = {
        "success_count": int(stats_result.success_count or 0),
        "failed_count": int(stats_result.failed_count or 0),
        "timeout_count": int(stats_result.timeout_count or 0),
        "avg_response_time": round(float(stats_result.avg_response_time), 2) if stats_result.avg_response_time else 0
    }
    
    return {
        "total": total,
        "items": logs_with_service_name,
        "stats": stats
    }


@router.get("/{log_id}")
async def get_monitor_log(log_id: int, db: Session = Depends(get_db)):
    """获取单个监控日志详情 - 优化版本"""
    # 使用JOIN避免额外查询
    result = db.query(MonitorLog, MonitorService.name.label('service_name'))\
               .join(MonitorService, MonitorLog.service_id == MonitorService.id)\
               .filter(MonitorLog.id == log_id)\
               .first()
    
    if not result:
        raise HTTPException(status_code=404, detail="监控日志不存在")
    
    log, service_name = result
    
    return {
        "id": log.id,
        "service_id": log.service_id,
        "service_name": service_name,
        "status": log.status,
        "response_time": log.response_time,
        "status_code": log.status_code,
        "response_size": log.response_size,
        "error_message": log.error_message,
        "error_type": log.error_type,
        "request_url": log.request_url,
        "request_method": log.request_method,
        "request_headers": log.request_headers,
        "response_headers": log.response_headers,
        "response_body": log.response_body,
        "check_time": log.check_time.isoformat() if log.check_time else None,
        "created_at": log.created_at.isoformat() if log.created_at else None,
        "alert_sent": log.alert_sent,
        "alert_methods": log.alert_methods
    }


@router.delete("/{log_id}")
async def delete_monitor_log(log_id: int, db: Session = Depends(get_db)):
    """删除监控日志"""
    log = db.query(MonitorLog).filter(MonitorLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="监控日志不存在")
    
    db.delete(log)
    db.commit()
    
    return {"message": "监控日志删除成功"}


@router.delete("/")
async def batch_delete_logs(
    service_id: Optional[int] = Query(None, description="服务ID"),
    status: Optional[str] = Query(None, description="状态"),
    days: Optional[int] = Query(None, ge=1, description="删除N天前的日志"),
    batch_size: int = Query(1000, ge=100, le=10000, description="批次大小"),
    db: Session = Depends(get_db)
):
    """批量删除监控日志 - 优化版本，分批删除避免长时间锁表"""
    
    # 构建删除条件
    conditions = []
    params = {}
    
    if service_id:
        conditions.append("service_id = :service_id")
        params["service_id"] = service_id
    
    if status:
        conditions.append("status = :status")
        params["status"] = status
    
    if days:
        cutoff_date = datetime.now() - timedelta(days=days)
        conditions.append("check_time < :cutoff_date")
        params["cutoff_date"] = cutoff_date
    
    if not conditions:
        raise HTTPException(status_code=400, detail="必须提供至少一个删除条件")
    
    where_clause = " AND ".join(conditions)
    
    # 先获取要删除的总数
    count_sql = f"SELECT COUNT(*) FROM monitor_logs WHERE {where_clause}"
    total_count = db.execute(text(count_sql), params).scalar()
    
    if total_count == 0:
        return {"message": "没有找到符合条件的记录"}
    
    # 分批删除
    deleted_count = 0
    while True:
        delete_sql = f"""
        DELETE FROM monitor_logs 
        WHERE {where_clause}
        LIMIT :batch_size
        """
        params["batch_size"] = batch_size
        
        result = db.execute(text(delete_sql), params)
        batch_deleted = result.rowcount
        
        if batch_deleted == 0:
            break
            
        deleted_count += batch_deleted
        db.commit()
        
        # 如果删除的记录数小于批次大小，说明已经删除完毕
        if batch_deleted < batch_size:
            break
    
    return {"message": f"成功删除 {deleted_count} 条监控日志"}


@router.get("/stats/overview")
async def get_monitor_stats(
    service_id: Optional[int] = Query(None, description="服务ID筛选"),
    days: int = Query(7, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取监控统计信息 - 优化版本"""
    # 使用单个优化的SQL查询获取所有统计数据
    sql = """
    SELECT 
        -- 总体统计
        COUNT(*) as total_checks,
        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
        AVG(CASE WHEN response_time IS NOT NULL THEN response_time END) as avg_response_time,
        
        -- 24小时统计
        SUM(CASE WHEN check_time >= :last_24h_start THEN 1 ELSE 0 END) as last_24h_checks,
        SUM(CASE WHEN check_time >= :last_24h_start AND status = 'success' THEN 1 ELSE 0 END) as last_24h_success
    FROM monitor_logs 
    WHERE check_time >= :start_time
    """
    
    start_time = datetime.now() - timedelta(days=days)
    last_24h_start = datetime.now() - timedelta(hours=24)
    
    params = {
        "start_time": start_time,
        "last_24h_start": last_24h_start
    }
    
    if service_id:
        sql += " AND service_id = :service_id"
        params["service_id"] = service_id
    
    result = db.execute(text(sql), params).fetchone()
    
    total_checks = result.total_checks or 0
    success_count = result.success_count or 0
    failed_count = total_checks - success_count
    success_rate = round(success_count / total_checks * 100, 2) if total_checks > 0 else 0
    
    last_24h_checks = result.last_24h_checks or 0
    last_24h_success = result.last_24h_success or 0
    last_24h_success_rate = round(last_24h_success / last_24h_checks * 100, 2) if last_24h_checks > 0 else 0
    
    return {
        "total_checks": total_checks,
        "success_count": success_count,
        "failed_count": failed_count,
        "success_rate": success_rate,
        "avg_response_time": round(float(result.avg_response_time), 2) if result.avg_response_time else None,
        "last_24h_checks": last_24h_checks,
        "last_24h_success_rate": last_24h_success_rate
    }


@router.get("/stats/timeline")
async def get_timeline_stats(
    service_id: Optional[int] = Query(None, description="服务ID筛选"),
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取时间线统计数据 - 优化版本"""
    
    # 优化的SQL查询，利用索引
    sql = """
    SELECT 
        DATE(check_time) as date,
        COUNT(*) as total_checks,
        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
        AVG(CASE WHEN response_time IS NOT NULL THEN response_time END) as avg_response_time,
        MIN(response_time) as min_response_time,
        MAX(response_time) as max_response_time
    FROM monitor_logs 
    WHERE check_time >= :start_time
    """
    
    params = {"start_time": datetime.now() - timedelta(days=days)}
    
    if service_id:
        sql += " AND service_id = :service_id"
        params["service_id"] = service_id
    
    sql += " GROUP BY DATE(check_time) ORDER BY date"
    
    result = db.execute(text(sql), params).fetchall()
    
    timeline_data = []
    for row in result:
        success_rate = round(row.success_count / row.total_checks * 100, 2) if row.total_checks > 0 else 0
        timeline_data.append({
            "date": row.date.isoformat(),
            "total_checks": row.total_checks,
            "success_count": row.success_count,
            "failed_count": row.total_checks - row.success_count,
            "success_rate": success_rate,
            "avg_response_time": round(row.avg_response_time, 2) if row.avg_response_time else None,
            "min_response_time": round(row.min_response_time, 2) if row.min_response_time else None,
            "max_response_time": round(row.max_response_time, 2) if row.max_response_time else None
        })
    
    return {"timeline": timeline_data}


@router.get("/stats/performance")
async def get_performance_stats(
    service_id: Optional[int] = Query(None, description="服务ID筛选"),
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取性能统计数据 - 新增接口"""
    
    sql = """
    SELECT 
        service_id,
        s.name as service_name,
        COUNT(*) as total_checks,
        SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
        AVG(CASE WHEN response_time IS NOT NULL THEN response_time END) as avg_response_time,
        MIN(CASE WHEN response_time IS NOT NULL THEN response_time END) as min_response_time,
        MAX(CASE WHEN response_time IS NOT NULL THEN response_time END) as max_response_time,
        STDDEV(CASE WHEN response_time IS NOT NULL THEN response_time END) as stddev_response_time
    FROM monitor_logs ml
    JOIN monitor_services s ON ml.service_id = s.id
    WHERE ml.check_time >= :start_time
    """
    
    params = {"start_time": datetime.now() - timedelta(days=days)}
    
    if service_id:
        sql += " AND ml.service_id = :service_id"
        params["service_id"] = service_id
    
    sql += " GROUP BY service_id, s.name ORDER BY avg_response_time DESC"
    
    result = db.execute(text(sql), params).fetchall()
    
    performance_data = []
    for row in result:
        success_rate = round(row.success_count / row.total_checks * 100, 2) if row.total_checks > 0 else 0
        performance_data.append({
            "service_id": row.service_id,
            "service_name": row.service_name,
            "total_checks": row.total_checks,
            "success_count": row.success_count,
            "success_rate": success_rate,
            "avg_response_time": round(row.avg_response_time, 2) if row.avg_response_time else None,
            "min_response_time": round(row.min_response_time, 2) if row.min_response_time else None,
            "max_response_time": round(row.max_response_time, 2) if row.max_response_time else None,
            "stddev_response_time": round(row.stddev_response_time, 2) if row.stddev_response_time else None
        })
    
    return {"performance": performance_data}


@router.post("/cleanup")
async def cleanup_old_logs(
    days_to_keep: int = Query(90, ge=7, le=365, description="保留天数"),
    dry_run: bool = Query(True, description="是否为试运行"),
    db: Session = Depends(get_db)
):
    """清理旧日志数据"""
    cutoff_date = datetime.now() - timedelta(days=days_to_keep)
    
    # 获取要删除的记录数
    count_sql = "SELECT COUNT(*) FROM monitor_logs WHERE check_time < :cutoff_date"
    count_to_delete = db.execute(text(count_sql), {"cutoff_date": cutoff_date}).scalar()
    
    if dry_run:
        return {
            "message": f"试运行模式：将删除 {count_to_delete} 条记录（{cutoff_date.strftime('%Y-%m-%d')} 之前的数据）",
            "count_to_delete": count_to_delete,
            "cutoff_date": cutoff_date.isoformat()
        }
    
    if count_to_delete == 0:
        return {"message": "没有需要清理的数据"}
    
    # 分批删除
    batch_size = 1000
    deleted_count = 0
    
    while True:
        delete_sql = """
        DELETE FROM monitor_logs 
        WHERE check_time < :cutoff_date
        LIMIT :batch_size
        """
        
        result = db.execute(text(delete_sql), {
            "cutoff_date": cutoff_date,
            "batch_size": batch_size
        })
        
        batch_deleted = result.rowcount
        if batch_deleted == 0:
            break
            
        deleted_count += batch_deleted
        db.commit()
        
        if batch_deleted < batch_size:
            break
    
    return {
        "message": f"成功清理 {deleted_count} 条旧日志记录",
        "deleted_count": deleted_count,
        "cutoff_date": cutoff_date.isoformat()
    }