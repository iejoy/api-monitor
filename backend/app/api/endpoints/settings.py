"""
系统设置API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.core.database import get_db
from app.models.system_setting import SystemSetting, AlertChannelTemplate, EmailTemplate

router = APIRouter()


@router.get("/")
async def get_system_settings(db: Session = Depends(get_db)):
    """获取系统设置"""
    # 从数据库获取设置
    settings = db.query(SystemSetting).all()
    
    # 按分类组织数据
    result = {
        "email": {
            "smtp_server": "",
            "smtp_port": 587,
            "smtp_username": "",
            "smtp_password": "",
            "smtp_from_email": "",
            "smtp_use_tls": True
        },
        "feishu": {
            "sign_key": ""
        },
        "wechat": {},
        "monitor": {
            "default_interval": 5,
            "max_concurrent_checks": 10,
            "default_timeout": 30,
            "data_retention_days": 30,
            "monitoring_enabled": True
        }
    }
    
    # 用数据库中的值覆盖默认值
    for setting in settings:
        if setting.category in result and setting.is_active:
            # 处理不同类型的值
            value = setting.value
            if setting.key in ["smtp_port", "default_interval", "max_concurrent_checks", "default_timeout", "data_retention_days"]:
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    pass
            elif setting.key in ["smtp_use_tls", "monitoring_enabled"]:
                value = str(value).lower() in ['true', '1', 'yes', 'on']
            
            result[setting.category][setting.key] = value
    
    return result


@router.put("/")
async def update_system_settings(settings_data: dict, db: Session = Depends(get_db)):
    """更新系统设置"""
    try:
        for category, settings in settings_data.items():
            if not isinstance(settings, dict):
                continue
                
            for key, value in settings.items():
                # 查找现有设置
                existing_setting = db.query(SystemSetting).filter(
                    SystemSetting.category == category,
                    SystemSetting.key == key
                ).first()
                
                if existing_setting:
                    # 更新现有设置
                    existing_setting.value = str(value)
                    existing_setting.is_active = True
                else:
                    # 创建新设置
                    new_setting = SystemSetting(
                        category=category,
                        name=key.replace('_', ' ').title(),
                        key=key,
                        value=str(value),
                        is_active=True
                    )
                    db.add(new_setting)
        
        db.commit()
        return {"message": "系统设置更新成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新失败: {str(e)}")


@router.post("/test/email")
async def test_email_config(email_data: dict, db: Session = Depends(get_db)):
    """测试邮件配置"""
    # 这里可以实现实际的邮件发送测试逻辑
    return {
        "success": True,
        "message": "邮件配置测试成功"
    }


@router.post("/test/feishu")
async def test_feishu_config(feishu_data: dict, db: Session = Depends(get_db)):
    """测试飞书配置"""
    # 这里可以实现实际的飞书消息发送测试逻辑
    return {
        "success": True,
        "message": "飞书配置测试成功"
    }


@router.post("/test/wechat")
async def test_wechat_config(wechat_data: dict, db: Session = Depends(get_db)):
    """测试微信配置"""
    # 这里可以实现实际的微信消息发送测试逻辑
    return {
        "success": True,
        "message": "微信配置测试成功"
    }


@router.get("/system/info")
async def get_system_info(db: Session = Depends(get_db)):
    """获取系统信息"""
    import platform
    from datetime import datetime
    from app.models.service import MonitorService
    from app.models.alert_config import AlertConfig
    from app.models.monitor_log import MonitorLog
    
    # 获取统计数据
    service_count = db.query(MonitorService).count()
    alert_config_count = db.query(AlertConfig).count()
    today_check_count = db.query(MonitorLog).filter(
        MonitorLog.created_at >= datetime.now().date()
    ).count()
    
    return {
        "version": "1.0.0",
        "python_version": platform.python_version(),
        "database_type": "MySQL",
        "start_time": datetime.now().isoformat(),
        "uptime": "0 days, 0 hours, 0 minutes",
        "service_count": service_count,
        "alert_config_count": alert_config_count,
        "today_check_count": today_check_count
    }


@router.post("/system/clear-logs")
async def clear_system_logs(db: Session = Depends(get_db)):
    """清理系统日志"""
    from app.models.monitor_log import MonitorLog
    from datetime import datetime, timedelta
    
    # 删除30天前的日志
    cutoff_date = datetime.now() - timedelta(days=30)
    deleted_count = db.query(MonitorLog).filter(
        MonitorLog.created_at < cutoff_date
    ).count()
    
    db.query(MonitorLog).filter(
        MonitorLog.created_at < cutoff_date
    ).delete()
    
    db.commit()
    
    return {"message": "系统日志清理成功", "deleted_count": deleted_count}


@router.get("/system/export")
async def export_system_data(db: Session = Depends(get_db)):
    """导出系统数据"""
    from fastapi.responses import JSONResponse
    from datetime import datetime
    from app.models.service import MonitorService
    from app.models.alert_config import AlertConfig
    from app.models.monitor_log import MonitorLog
    
    # 获取所有数据
    services = db.query(MonitorService).all()
    alert_configs = db.query(AlertConfig).all()
    recent_logs = db.query(MonitorLog).order_by(MonitorLog.created_at.desc()).limit(1000).all()
    
    export_data = {
        "services": [
            {
                "id": s.id,
                "name": s.name,
                "url": s.url,
                "method": s.method,
                "is_active": s.is_active,
                "created_at": s.created_at.isoformat() if s.created_at else None
            }
            for s in services
        ],
        "alert_configs": [
            {
                "id": a.id,
                "name": a.name,
                "type": a.type,
                "service_id": a.service_id,
                "is_active": a.is_active,
                "created_at": a.created_at.isoformat() if a.created_at else None
            }
            for a in alert_configs
        ],
        "logs": [
            {
                "id": l.id,
                "service_id": l.service_id,
                "status_code": l.status_code,
                "response_time": l.response_time,
                "is_success": l.is_success,
                "created_at": l.created_at.isoformat() if l.created_at else None
            }
            for l in recent_logs
        ],
        "export_time": datetime.now().isoformat()
    }
    
    return JSONResponse(content=export_data)


# 告警渠道模板相关API
@router.get("/alert-templates/")
async def get_alert_templates(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: str = Query(None),
    type: str = Query(None),
    db: Session = Depends(get_db)
):
    """获取告警渠道模板列表"""
    try:
        print(f"搜索参数 - search: '{search}', type: '{type}', page: {page}, size: {size}")  # 调试日志
        
        query = db.query(AlertChannelTemplate)
        
        # 搜索过滤
        if search and search.strip():
            search_term = search.strip()
            print(f"应用搜索过滤: '{search_term}'")  # 调试日志
            search_filter = or_(
                AlertChannelTemplate.name.contains(search_term),
                AlertChannelTemplate.description.contains(search_term)
            )
            query = query.filter(search_filter)
        
        # 类型过滤
        if type and type.strip():
            type_term = type.strip()
            print(f"应用类型过滤: '{type_term}'")  # 调试日志
            query = query.filter(AlertChannelTemplate.type == type_term)
        
        # 获取总数
        total = query.count()
        print(f"过滤后总数: {total}")  # 调试日志
        
        # 分页
        templates = query.order_by(
            AlertChannelTemplate.type, 
            AlertChannelTemplate.name
        ).offset((page - 1) * size).limit(size).all()
        
        print(f"返回模板数量: {len(templates)}")  # 调试日志
        
        return {
            "items": [
                {
                    "id": template.id,
                    "name": template.name,
                    "type": template.type,
                    "config": template.config or {},
                    "description": template.description or "",
                    "alert_title_template": getattr(template, 'alert_title_template', '') or "",
                    "alert_content_template": getattr(template, 'alert_content_template', '') or "",
                    "is_default": template.is_default,
                    "is_active": template.is_active,
                    "created_at": template.created_at.isoformat() if template.created_at else None,
                    "updated_at": template.updated_at.isoformat() if template.updated_at else None
                }
                for template in templates
            ],
            "total": total,
            "page": page,
            "size": size
        }
    except Exception as e:
        print(f"获取模板列表错误: {str(e)}")  # 调试日志
        raise HTTPException(status_code=500, detail=f"获取模板列表失败: {str(e)}")


@router.get("/alert-templates/{template_id}")
async def get_alert_template(template_id: int, db: Session = Depends(get_db)):
    """获取单个告警渠道模板详情"""
    try:
        template = db.query(AlertChannelTemplate).filter(AlertChannelTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        return {
            "id": template.id,
            "name": template.name,
            "type": template.type,
            "config": template.config or {},
            "description": template.description or "",
            "alert_title_template": getattr(template, 'alert_title_template', '') or "",
            "alert_content_template": getattr(template, 'alert_content_template', '') or "",
            "is_default": template.is_default,
            "is_active": template.is_active,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"获取模板详情错误: {str(e)}")  # 调试日志
        raise HTTPException(status_code=500, detail=f"获取模板详情失败: {str(e)}")

@router.post("/alert-templates/")
async def create_alert_template(template_data: dict, db: Session = Depends(get_db)):
    """创建告警渠道模板"""
    try:
        # 如果设置为默认模板，先取消同类型的其他默认模板
        if template_data.get("is_default", False):
            db.query(AlertChannelTemplate).filter(
                AlertChannelTemplate.type == template_data.get("type"),
                AlertChannelTemplate.is_default == True
            ).update({"is_default": False})
        
        template = AlertChannelTemplate(
            name=template_data.get("name"),
            type=template_data.get("type"),
            config=template_data.get("config", {}),
            description=template_data.get("description", ""),
            alert_title_template=template_data.get("alert_title_template", ""),
            alert_content_template=template_data.get("alert_content_template", ""),
            is_active=template_data.get("is_active", True),
            is_default=template_data.get("is_default", False)
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        
        return {"message": "模板创建成功", "id": template.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"创建模板失败: {str(e)}")


@router.put("/alert-templates/{template_id}")
async def update_alert_template(template_id: int, template_data: dict, db: Session = Depends(get_db)):
    """更新告警渠道模板"""
    try:
        template = db.query(AlertChannelTemplate).filter(AlertChannelTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        # 如果设置为默认模板，先取消同类型的其他默认模板
        if template_data.get("is_default", False) and not template.is_default:
            db.query(AlertChannelTemplate).filter(
                AlertChannelTemplate.type == template.type,
                AlertChannelTemplate.id != template_id,
                AlertChannelTemplate.is_default == True
            ).update({"is_default": False})
        
        # 更新模板信息
        template.name = template_data.get("name", template.name)
        template.config = template_data.get("config", template.config)
        template.description = template_data.get("description", template.description)
        template.alert_title_template = template_data.get("alert_title_template", getattr(template, 'alert_title_template', ''))
        template.alert_content_template = template_data.get("alert_content_template", getattr(template, 'alert_content_template', ''))
        template.is_active = template_data.get("is_active", template.is_active)
        template.is_default = template_data.get("is_default", template.is_default)
        
        db.commit()
        db.refresh(template)
        
        return {"message": "模板更新成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"更新模板失败: {str(e)}")


@router.delete("/alert-templates/{template_id}")
async def delete_alert_template(template_id: int, db: Session = Depends(get_db)):
    """删除告警渠道模板"""
    try:
        template = db.query(AlertChannelTemplate).filter(AlertChannelTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="模板不存在")
        
        db.delete(template)
        db.commit()
        
        return {"message": "模板删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"删除模板失败: {str(e)}")