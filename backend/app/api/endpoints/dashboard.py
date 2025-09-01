"""
仪表板API
"""
from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, text

from app.core.database import get_db
from app.models.service import MonitorService
from app.models.monitor_log import MonitorLog
from app.models.alert_config import AlertConfig

router = APIRouter()


@router.get("/overview")
async def get_dashboard_overview(db: Session = Depends(get_db)):
    """获取仪表板概览数据"""
    # 服务统计
    total_services = db.query(MonitorService).count()
    active_services = db.query(MonitorService).filter(MonitorService.is_active == True).count()
    healthy_services = db.query(MonitorService).filter(MonitorService.status == "success").count()
    unhealthy_services = db.query(MonitorService).filter(
        MonitorService.status.in_(["failed", "timeout"])
    ).count()
    
    # 告警配置统计
    total_alert_configs = db.query(AlertConfig).count()
    active_alert_configs = db.query(AlertConfig).filter(AlertConfig.is_active == True).count()
    
    # 今天的监控统计
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_checks = db.query(MonitorLog).filter(MonitorLog.check_time >= today_start).count()
    today_success = db.query(MonitorLog).filter(
        MonitorLog.check_time >= today_start,
        MonitorLog.status == "success"
    ).count()
    today_alerts = db.query(MonitorLog).filter(
        MonitorLog.check_time >= today_start,
        MonitorLog.alert_sent == True
    ).count()
    
    # 最近24小时监控统计（保留用于其他统计）
    last_24h = datetime.now() - timedelta(hours=24)
    recent_checks = db.query(MonitorLog).filter(MonitorLog.check_time >= last_24h).count()
    recent_success = db.query(MonitorLog).filter(
        MonitorLog.check_time >= last_24h,
        MonitorLog.status == "success"
    ).count()
    
    # 计算成功率
    success_rate = round(recent_success / recent_checks * 100, 2) if recent_checks > 0 else 0
    
    return {
        "services": {
            "total": total_services,
            "active": active_services,
            "healthy": healthy_services,
            "unhealthy": unhealthy_services,
            "inactive": total_services - active_services
        },
        "alerts": {
            "total_configs": total_alert_configs,
            "active_configs": active_alert_configs,
            "recent_alerts": today_alerts
        },
        "monitoring": {
            "recent_checks": recent_checks,
            "recent_success": recent_success,
            "success_rate": success_rate
        },
        "scheduler": {
            "running": True,
            "total_jobs": active_services
        }
    }


@router.get("/services/status")
async def get_services_status(db: Session = Depends(get_db)):
    """获取所有服务的当前状态"""
    services = db.query(MonitorService).filter(MonitorService.is_active == True).all()
    
    services_status = []
    for service in services:
        # 获取最近的监控日志
        latest_log = db.query(MonitorLog).filter(
            MonitorLog.service_id == service.id
        ).order_by(MonitorLog.check_time.desc()).first()
        
        services_status.append({
            "id": service.id,
            "name": service.name,
            "url": service.url,
            "status": service.status,
            "last_check_time": service.last_check_time.isoformat() if service.last_check_time else None,
            "last_success_time": service.last_success_time.isoformat() if service.last_success_time else None,
            "response_time": latest_log.response_time if latest_log else None,
            "status_code": latest_log.status_code if latest_log else None,
            "error_message": latest_log.error_message if latest_log and latest_log.error_message else None
        })
    
    return {"services": services_status}


@router.get("/alerts/recent")
async def get_recent_alerts(
    limit: int = Query(10, ge=1, le=50, description="返回记录数"),
    today_only: bool = Query(True, description="是否只返回今天的告警"),
    db: Session = Depends(get_db)
):
    """获取最近的告警记录"""
    query = db.query(MonitorLog).filter(MonitorLog.alert_sent == True)
    
    # 如果只要今天的告警，添加日期过滤
    if today_only:
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(MonitorLog.check_time >= today_start)
    
    recent_alerts = query.order_by(MonitorLog.check_time.desc()).limit(limit).all()
    
    alerts_data = []
    for log in recent_alerts:
        service = db.query(MonitorService).filter(MonitorService.id == log.service_id).first()
        alerts_data.append({
            "id": log.id,
            "service_id": log.service_id,
            "service_name": service.name if service else "未知服务",
            "service_url": log.request_url,
            "status": log.status,
            "error_message": log.error_message,
            "alert_methods": log.alert_methods,
            "check_time": log.check_time.isoformat(),
            "response_time": log.response_time,
            "status_code": log.status_code
        })
    
    return {"alerts": alerts_data}


@router.get("/hourly-stats")
async def get_hourly_stats(
    hours: int = Query(24, ge=1, le=720, description="统计小时数"),
    db: Session = Depends(get_db)
):
    """获取按小时统计的监控数据"""
    # 计算开始时间
    start_time = datetime.now() - timedelta(hours=hours)
    
    # 按小时分组统计
    hourly_stats = []
    for i in range(hours):
        hour_start = start_time + timedelta(hours=i)
        hour_end = hour_start + timedelta(hours=1)
        
        # 统计该小时内的监控记录
        total_checks = db.query(MonitorLog).filter(
            MonitorLog.check_time >= hour_start,
            MonitorLog.check_time < hour_end
        ).count()
        
        success_checks = db.query(MonitorLog).filter(
            MonitorLog.check_time >= hour_start,
            MonitorLog.check_time < hour_end,
            MonitorLog.status == "success"
        ).count()
        
        # 计算成功率
        success_rate = round(success_checks / total_checks * 100, 2) if total_checks > 0 else 0
        
        hourly_stats.append({
            "hour": hour_start.isoformat(),
            "total_checks": total_checks,
            "success_checks": success_checks,
            "failed_checks": total_checks - success_checks,
            "success_rate": success_rate
        })
    
    return {"hourly_stats": hourly_stats}


@router.get("/response-time-stats")
async def get_response_time_stats(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取响应时间分布统计"""
    # 计算开始时间
    start_time = datetime.now() - timedelta(days=days)
    
    # 获取指定时间范围内的响应时间数据
    response_times = db.query(MonitorLog.response_time).filter(
        MonitorLog.check_time >= start_time,
        MonitorLog.response_time.isnot(None),
        MonitorLog.status == "success"
    ).all()
    
    # 统计响应时间分布
    distribution = {
        "0-100ms": 0,
        "100-300ms": 0,
        "300-500ms": 0,
        "500-1000ms": 0,
        "1000ms+": 0
    }
    
    for (response_time,) in response_times:
        if response_time < 100:
            distribution["0-100ms"] += 1
        elif response_time < 300:
            distribution["100-300ms"] += 1
        elif response_time < 500:
            distribution["300-500ms"] += 1
        elif response_time < 1000:
            distribution["500-1000ms"] += 1
        else:
            distribution["1000ms+"] += 1
    
    # 转换为前端需要的格式
    distribution_list = [
        {"range": range_name, "count": count}
        for range_name, count in distribution.items()
    ]
    
    # 计算平均响应时间
    total_response_time = sum(rt[0] for rt in response_times)
    avg_response_time = round(total_response_time / len(response_times), 2) if response_times else 0
    
    return {
        "distribution": distribution_list,
        "avg_response_time": avg_response_time,
        "total_samples": len(response_times)
    }


@router.get("/stats")
async def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取仪表板统计数据"""
    # 基本统计
    total_services = db.query(MonitorService).count()
    active_services = db.query(MonitorService).filter(MonitorService.is_active == True).count()
    total_logs = db.query(MonitorLog).count()
    total_alerts = db.query(MonitorLog).filter(MonitorLog.alert_sent == True).count()
    
    return {
        "total_services": total_services,
        "active_services": active_services,
        "total_logs": total_logs,
        "total_alerts": total_alerts
    }


@router.get("/charts")
async def get_dashboard_charts(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取图表数据"""
    # 简单返回模拟数据
    chart_data = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=days-i-1)).strftime('%Y-%m-%d')
        chart_data.append({
            "date": date,
            "success_count": 100 - i,
            "failed_count": i,
            "avg_response_time": 200 + i * 10
        })
    
    return {"chart_data": chart_data}


@router.get("/health")
async def get_system_health():
    """获取系统健康状态"""
    try:
        import psutil
        import os
        
        # CPU使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # 内存使用情况
        memory = psutil.virtual_memory()
        
        # 磁盘使用情况
        disk = psutil.disk_usage('/')
        
        # 进程信息
        process = psutil.Process(os.getpid())
        process_memory = process.memory_info()
        
        return {
            "system": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total": memory.total,
                    "available": memory.available,
                    "percent": memory.percent,
                    "used": memory.used
                },
                "disk": {
                    "total": disk.total,
                    "used": disk.used,
                    "free": disk.free,
                    "percent": round(disk.used / disk.total * 100, 2)
                }
            },
            "process": {
                "memory_rss": process_memory.rss,
                "memory_vms": process_memory.vms,
                "cpu_percent": process.cpu_percent(),
                "create_time": datetime.fromtimestamp(process.create_time()).isoformat()
            },
            "scheduler": {
                "running": True,
                "total_jobs": 0
            }
        }
    except Exception as e:
        return {
            "system": {
                "cpu_percent": 0,
                "memory": {"total": 0, "available": 0, "percent": 0, "used": 0},
                "disk": {"total": 0, "used": 0, "free": 0, "percent": 0}
            },
            "process": {
                "memory_rss": 0,
                "memory_vms": 0,
                "cpu_percent": 0,
                "create_time": datetime.now().isoformat()
            },
            "scheduler": {"running": True, "total_jobs": 0}
        }


@router.get("/availability-stats")
async def get_availability_stats(
    days: int = Query(7, ge=1, le=30, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取按应用维度的高可用统计"""
    # 计算开始时间
    start_time = datetime.now() - timedelta(days=days)
    
    # 获取所有活跃服务
    services = db.query(MonitorService).filter(MonitorService.is_active == True).all()
    
    availability_stats = []
    
    for service in services:
        # 统计该服务在指定时间范围内的监控记录
        total_checks = db.query(MonitorLog).filter(
            MonitorLog.service_id == service.id,
            MonitorLog.check_time >= start_time
        ).count()
        
        success_checks = db.query(MonitorLog).filter(
            MonitorLog.service_id == service.id,
            MonitorLog.check_time >= start_time,
            MonitorLog.status == "success"
        ).count()
        
        # 计算可用性百分比
        availability = round(success_checks / total_checks * 100, 2) if total_checks > 0 else 0
        
        # 计算平均响应时间
        avg_response_time = db.query(func.avg(MonitorLog.response_time)).filter(
            MonitorLog.service_id == service.id,
            MonitorLog.check_time >= start_time,
            MonitorLog.response_time.isnot(None),
            MonitorLog.status == "success"
        ).scalar()
        
        avg_response_time = round(avg_response_time, 2) if avg_response_time else 0
        
        # 获取最近一次检查时间
        latest_log = db.query(MonitorLog).filter(
            MonitorLog.service_id == service.id
        ).order_by(MonitorLog.check_time.desc()).first()
        
        availability_stats.append({
            "service_id": service.id,
            "service_name": service.name,
            "service_url": service.url,
            "availability": availability,
            "total_checks": total_checks,
            "success_checks": success_checks,
            "failed_checks": total_checks - success_checks,
            "avg_response_time": avg_response_time,
            "last_check_time": latest_log.check_time.isoformat() if latest_log else None,
            "current_status": service.status
        })
    
    # 按可用性排序（从高到低）
    availability_stats.sort(key=lambda x: x['availability'], reverse=True)
    
    # 计算整体统计
    total_services = len(services)
    high_availability_services = len([s for s in availability_stats if s['availability'] >= 99.0])
    medium_availability_services = len([s for s in availability_stats if 95.0 <= s['availability'] < 99.0])
    low_availability_services = len([s for s in availability_stats if s['availability'] < 95.0])
    
    return {
        "services": availability_stats,
        "summary": {
            "total_services": total_services,
            "high_availability": high_availability_services,  # >= 99%
            "medium_availability": medium_availability_services,  # 95% - 99%
            "low_availability": low_availability_services,  # < 95%
            "period_days": days
        }
    }