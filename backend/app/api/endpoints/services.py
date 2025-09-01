"""
服务监控管理API
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.core.database import get_db
from app.models.service import MonitorService

router = APIRouter()


@router.get("/")
async def get_services(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    status: Optional[str] = Query(None, description="状态筛选"),
    db: Session = Depends(get_db)
):
    """获取服务列表"""
    query = db.query(MonitorService)
    
    # 搜索过滤
    if search:
        query = query.filter(
            or_(
                MonitorService.name.contains(search),
                MonitorService.url.contains(search),
                MonitorService.description.contains(search)
            )
        )
    
    # 状态过滤
    if status:
        query = query.filter(MonitorService.status == status)
    
    # 获取总数
    total = query.count()
    
    # 计算跳过记录数
    skip = (page - 1) * size
    
    # 分页查询
    services = query.order_by(desc(MonitorService.created_at)).offset(skip).limit(size).all()
    
    # 转换为字典格式
    services_data = []
    for service in services:
        service_dict = {
            "id": service.id,
            "name": service.name,
            "url": service.url,
            "method": service.method,
            "timeout": service.timeout,
            "interval": service.interval,
            "retry_count": service.retry_count,
            "is_active": service.is_active,
            "status": service.status,
            "last_check_time": service.last_check_time.isoformat() if service.last_check_time else None,
            "last_success_time": service.last_success_time.isoformat() if service.last_success_time else None,
            "enable_alert": service.enable_alert,
            "alert_methods": service.alert_methods,
            "alert_contacts": service.alert_contacts,
            "description": service.description,
            "tags": service.tags,
            "created_at": service.created_at.isoformat() if service.created_at else None,
            "updated_at": service.updated_at.isoformat() if service.updated_at else None
        }
        services_data.append(service_dict)
    
    return {
        "total": total,
        "items": services_data
    }


@router.get("/{service_id}")
async def get_service(service_id: int, db: Session = Depends(get_db)):
    """获取单个服务详情"""
    service = db.query(MonitorService).filter(MonitorService.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")
    
    # 导入MonitorLog模型来计算统计信息
    from app.models.monitor_log import MonitorLog
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    # 计算统计信息
    logs_query = db.query(MonitorLog).filter(MonitorLog.service_id == service_id)
    
    # 获取最近的状态
    latest_log = logs_query.order_by(desc(MonitorLog.check_time)).first()
    last_status = latest_log.status if latest_log else None
    
    # 计算平均响应时间（最近30天）
    thirty_days_ago = datetime.now() - timedelta(days=30)
    avg_response_time = logs_query.filter(
        MonitorLog.check_time >= thirty_days_ago,
        MonitorLog.response_time.isnot(None)
    ).with_entities(func.avg(MonitorLog.response_time)).scalar()
    
    # 计算可用率（最近30天）
    total_checks = logs_query.filter(MonitorLog.check_time >= thirty_days_ago).count()
    success_checks = logs_query.filter(
        MonitorLog.check_time >= thirty_days_ago,
        MonitorLog.status == "success"
    ).count()
    uptime_rate = success_checks / total_checks if total_checks > 0 else None
    
    return {
        "id": service.id,
        "name": service.name,
        "url": service.url,
        "method": service.method,
        "timeout": service.timeout,
        "interval": service.interval,
        "retry_count": service.retry_count,
        "is_active": service.is_active,
        "status": service.status,
        "last_status": last_status,
        "last_check_time": service.last_check_time.isoformat() if service.last_check_time else None,
        "last_success_time": service.last_success_time.isoformat() if service.last_success_time else None,
        "avg_response_time": round(avg_response_time, 2) if avg_response_time else None,
        "uptime_rate": round(uptime_rate, 4) if uptime_rate is not None else None,
        "enable_alert": service.enable_alert,
        "alert_methods": service.alert_methods,
        "alert_contacts": service.alert_contacts,
        "description": service.description,
        "tags": service.tags,
        "created_at": service.created_at.isoformat() if service.created_at else None,
        "updated_at": service.updated_at.isoformat() if service.updated_at else None
    }


@router.post("/")
async def create_service(service_data: dict, db: Session = Depends(get_db)):
    """创建新的监控服务"""
    # 检查URL是否已存在
    existing = db.query(MonitorService).filter(MonitorService.url == service_data.get("url")).first()
    if existing:
        raise HTTPException(status_code=400, detail="该URL已存在监控服务")
    
    # 创建服务
    db_service = MonitorService(
        name=service_data.get("name"),
        url=service_data.get("url"),
        method=service_data.get("method", "GET"),
        timeout=service_data.get("timeout", 30),
        interval=service_data.get("interval", 300),
        retry_count=service_data.get("retry_count", 3),
        is_active=service_data.get("is_active", True),
        enable_alert=service_data.get("enable_alert", True),
        alert_methods=service_data.get("alert_methods", "email"),
        alert_contacts=service_data.get("alert_contacts"),
        description=service_data.get("description"),
        tags=service_data.get("tags")
    )
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    
    return {"message": "服务创建成功", "id": db_service.id}


@router.put("/{service_id}")
async def update_service(service_id: int, service_data: dict, db: Session = Depends(get_db)):
    """更新监控服务"""
    service = db.query(MonitorService).filter(MonitorService.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")
    
    # 更新服务信息
    for field, value in service_data.items():
        if hasattr(service, field):
            setattr(service, field, value)
    
    db.commit()
    db.refresh(service)
    
    return {"message": "服务更新成功"}


@router.delete("/{service_id}")
async def delete_service(service_id: int, db: Session = Depends(get_db)):
    """删除监控服务"""
    service = db.query(MonitorService).filter(MonitorService.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")
    
    # 删除服务
    db.delete(service)
    db.commit()
    
    return {"message": "服务删除成功"}


@router.post("/{service_id}/toggle")
async def toggle_service(service_id: int, db: Session = Depends(get_db)):
    """切换服务启用状态"""
    service = db.query(MonitorService).filter(MonitorService.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")
    
    # 切换状态
    service.is_active = not service.is_active
    db.commit()
    
    return {
        "message": f"服务已{'启用' if service.is_active else '禁用'}",
        "is_active": service.is_active
    }


@router.post("/{service_id}/test")
async def test_service(service_id: int, db: Session = Depends(get_db)):
    """手动测试服务"""
    service = db.query(MonitorService).filter(MonitorService.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")
    
    import httpx
    import time
    from datetime import datetime
    
    try:
        # 记录开始时间
        start_time = time.time()
        
        # 发送HTTP请求
        async with httpx.AsyncClient(timeout=service.timeout) as client:
            response = await client.request(
                method=service.method,
                url=service.url,
                follow_redirects=True
            )
        
        # 计算响应时间
        response_time = round((time.time() - start_time) * 1000, 2)  # 转换为毫秒
        
        # 判断状态
        if response.status_code >= 200 and response.status_code < 400:
            status = "success"
            error_message = None
        else:
            status = "failed"
            error_message = f"HTTP {response.status_code}"
        
        # 更新服务的最后检查时间和状态
        service.last_check_time = datetime.now()
        service.status = status
        if status == "success":
            service.last_success_time = datetime.now()
        
        db.commit()
        
        return {
            "message": f"测试完成：{status}",
            "status": status,
            "response_time": response_time,
            "status_code": response.status_code,
            "error_message": error_message
        }
        
    except httpx.TimeoutException:
        # 超时处理
        response_time = service.timeout * 1000  # 转换为毫秒
        status = "timeout"
        error_message = f"请求超时（{service.timeout}秒）"
        
        # 更新服务状态
        service.last_check_time = datetime.now()
        service.status = status
        db.commit()
        
        return {
            "message": f"测试完成：{status}",
            "status": status,
            "response_time": response_time,
            "status_code": None,
            "error_message": error_message
        }
        
    except Exception as e:
        # 其他错误处理
        status = "failed"
        error_message = str(e)
        
        # 更新服务状态
        service.last_check_time = datetime.now()
        service.status = status
        db.commit()
        
        return {
            "message": f"测试完成：{status}",
            "status": status,
            "response_time": None,
            "status_code": None,
            "error_message": error_message
        }


@router.get("/{service_id}/logs")
async def get_service_logs(
    service_id: int,
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页记录数"),
    db: Session = Depends(get_db)
):
    """获取服务的监控日志"""
    # 检查服务是否存在
    service = db.query(MonitorService).filter(MonitorService.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")
    
    # 导入MonitorLog模型
    from app.models.monitor_log import MonitorLog
    
    # 查询该服务的监控日志
    query = db.query(MonitorLog).filter(MonitorLog.service_id == service_id)
    
    # 获取总数
    total = query.count()
    
    # 计算跳过记录数
    skip = (page - 1) * size
    
    # 分页查询
    logs = query.order_by(desc(MonitorLog.check_time)).offset(skip).limit(size).all()
    
    # 转换为字典格式
    logs_data = []
    for log in logs:
        log_dict = {
            "id": log.id,
            "service_id": log.service_id,
            "status": log.status,
            "response_time": log.response_time,
            "status_code": log.status_code,
            "error_message": log.error_message,
            "created_at": log.check_time.isoformat() if log.check_time else None,
            "alert_sent": log.alert_sent,
            "alert_methods": log.alert_methods
        }
        logs_data.append(log_dict)
    
    return {
        "total": total,
        "items": logs_data
    }

@router.get("/{service_id}/stats")
async def get_service_stats(service_id: int, db: Session = Depends(get_db)):
    """获取服务统计信息"""
    service = db.query(MonitorService).filter(MonitorService.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="服务不存在")
    
    return {
        "total_checks": 0,
        "success_count": 0,
        "failed_count": 0,
        "success_rate": 0,
        "avg_response_time": None,
        "last_24h_checks": 0,
        "last_24h_success_rate": 0
    }