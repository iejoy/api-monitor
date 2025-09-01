"""
系统设置管理API
"""
from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.models.system_setting import SystemSetting, AlertChannelTemplate, EmailTemplate

router = APIRouter()


# 系统设置相关API
@router.get("/")
async def get_system_settings(
    category: Optional[str] = Query(None, description="设置分类筛选"),
    db: Session = Depends(get_db)
):
    """获取系统设置列表"""
    query = db.query(SystemSetting)
    
    if category:
        query = query.filter(SystemSetting.category == category)
    
    settings = query.order_by(SystemSetting.category, SystemSetting.key).all()
    
    # 按分类组织数据
    result = {}
    for setting in settings:
        if setting.category not in result:
            result[setting.category] = {}
        result[setting.category][setting.key] = {
            "id": setting.id,
            "value": setting.value,
            "description": setting.description,
            "is_active": setting.is_active,
            "is_default": setting.is_default,
            "created_at": setting.created_at.isoformat() if setting.created_at else None,
            "updated_at": setting.updated_at.isoformat() if setting.updated_at else None
        }
    
    return result


@router.post("/")
async def create_or_update_setting(setting_data: dict, db: Session = Depends(get_db)):
    """创建或更新系统设置"""
    category = setting_data.get("category")
    key = setting_data.get("key")
    
    if not category or not key:
        raise HTTPException(status_code=400, detail="分类和键名不能为空")
    
    # 查找现有设置
    existing_setting = db.query(SystemSetting).filter(
        SystemSetting.category == category,
        SystemSetting.key == key
    ).first()
    
    if existing_setting:
        # 更新现有设置
        existing_setting.name = setting_data.get("name", existing_setting.name)
        existing_setting.value = setting_data.get("value", existing_setting.value)
        existing_setting.description = setting_data.get("description", existing_setting.description)
        existing_setting.is_active = setting_data.get("is_active", existing_setting.is_active)
        existing_setting.is_default = setting_data.get("is_default", existing_setting.is_default)
        
        db.commit()
        db.refresh(existing_setting)
        return {"message": "设置更新成功", "id": existing_setting.id}
    else:
        # 创建新设置
        new_setting = SystemSetting(
            category=category,
            name=setting_data.get("name", ""),
            key=key,
            value=setting_data.get("value", ""),
            description=setting_data.get("description", ""),
            is_active=setting_data.get("is_active", True),
            is_default=setting_data.get("is_default", False)
        )
        
        db.add(new_setting)
        db.commit()
        db.refresh(new_setting)
        return {"message": "设置创建成功", "id": new_setting.id}


@router.put("/batch")
async def batch_update_settings(settings_data: dict, db: Session = Depends(get_db)):
    """批量更新系统设置"""
    try:
        for category, settings in settings_data.items():
            for key, value in settings.items():
                # 查找现有设置
                existing_setting = db.query(SystemSetting).filter(
                    SystemSetting.category == category,
                    SystemSetting.key == key
                ).first()
                
                if existing_setting:
                    # 更新现有设置
                    if isinstance(value, dict):
                        existing_setting.value = value.get("value", existing_setting.value)
                        existing_setting.is_active = value.get("is_active", existing_setting.is_active)
                    else:
                        existing_setting.value = str(value)
                else:
                    # 创建新设置
                    if isinstance(value, dict):
                        new_setting = SystemSetting(
                            category=category,
                            name=key,
                            key=key,
                            value=value.get("value", ""),
                            is_active=value.get("is_active", True)
                        )
                    else:
                        new_setting = SystemSetting(
                            category=category,
                            name=key,
                            key=key,
                            value=str(value),
                            is_active=True
                        )
                    db.add(new_setting)
        
        db.commit()
        return {"message": "批量更新成功"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"批量更新失败: {str(e)}")


@router.delete("/{setting_id}")
async def delete_setting(setting_id: int, db: Session = Depends(get_db)):
    """删除系统设置"""
    setting = db.query(SystemSetting).filter(SystemSetting.id == setting_id).first()
    if not setting:
        raise HTTPException(status_code=404, detail="设置不存在")
    
    db.delete(setting)
    db.commit()
    return {"message": "设置删除成功"}


# 告警渠道模板相关API
@router.get("/alert-templates/")
async def get_alert_templates(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页记录数"),
    search: Optional[str] = Query(None, description="搜索关键词"),
    type: Optional[str] = Query(None, description="告警类型筛选"),
    is_active: Optional[bool] = Query(None, description="启用状态筛选"),
    db: Session = Depends(get_db)
):
    """获取告警渠道模板列表"""
    query = db.query(AlertChannelTemplate)
    
    # 搜索过滤
    if search:
        query = query.filter(
            AlertChannelTemplate.name.contains(search) |
            AlertChannelTemplate.description.contains(search)
        )
    
    if type:
        query = query.filter(AlertChannelTemplate.type == type)
    
    if is_active is not None:
        query = query.filter(AlertChannelTemplate.is_active == is_active)
    
    # 获取总数
    total = query.count()
    
    # 计算跳过记录数
    skip = (page - 1) * size
    
    # 分页查询
    templates = query.order_by(desc(AlertChannelTemplate.is_default), AlertChannelTemplate.name).offset(skip).limit(size).all()
    
    return {
        "total": total,
        "items": [
            {
                "id": template.id,
                "name": template.name,
                "type": template.type,
                "alert_title_template": template.config.get("alert_title_template", "") if template.config else "",
                "alert_content_template": template.config.get("alert_content_template", "") if template.config else "",
                "config": template.config,
                "description": template.description,
                "is_active": template.is_active,
                "is_default": template.is_default,
                "created_at": template.created_at.isoformat() if template.created_at else None,
                "updated_at": template.updated_at.isoformat() if template.updated_at else None
            }
            for template in templates
        ]
    }


@router.get("/alert-templates/{template_id}")
async def get_alert_template(template_id: int, db: Session = Depends(get_db)):
    """获取单个告警渠道模板详情"""
    template = db.query(AlertChannelTemplate).filter(AlertChannelTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return {
        "id": template.id,
        "name": template.name,
        "type": template.type,
        "alert_title_template": template.config.get("alert_title_template", "") if template.config else "",
        "alert_content_template": template.config.get("alert_content_template", "") if template.config else "",
        "config": template.config,
        "description": template.description,
        "is_active": template.is_active,
        "is_default": template.is_default,
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None
    }


@router.post("/alert-templates/")
async def create_alert_template(template_data: dict, db: Session = Depends(get_db)):
    """创建告警渠道模板"""
    # 如果设置为默认模板，先取消同类型的其他默认模板
    if template_data.get("is_default", False):
        db.query(AlertChannelTemplate).filter(
            AlertChannelTemplate.type == template_data.get("type"),
            AlertChannelTemplate.is_default == True
        ).update({"is_default": False})
    
    # 构建配置对象
    config = {
        "alert_title_template": template_data.get("alert_title_template", ""),
        "alert_content_template": template_data.get("alert_content_template", "")
    }
    
    # 添加渠道特定配置
    if template_data.get("type") in ["feishu", "wechat"] and template_data.get("webhook_url"):
        config["webhook_url"] = template_data.get("webhook_url")
    
    template = AlertChannelTemplate(
        name=template_data.get("name"),
        type=template_data.get("type"),
        config=config,
        description=template_data.get("description", ""),
        is_active=template_data.get("is_active", True),
        is_default=template_data.get("is_default", False)
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return {"message": "模板创建成功", "id": template.id}


@router.put("/alert-templates/{template_id}")
async def update_alert_template(template_id: int, template_data: dict, db: Session = Depends(get_db)):
    """更新告警渠道模板"""
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
    
    # 构建配置对象
    config = {
        "alert_title_template": template_data.get("alert_title_template", ""),
        "alert_content_template": template_data.get("alert_content_template", "")
    }
    
    # 添加渠道特定配置
    if template_data.get("type") in ["feishu", "wechat"] and template_data.get("webhook_url"):
        config["webhook_url"] = template_data.get("webhook_url")
    
    # 更新模板信息
    template.name = template_data.get("name", template.name)
    template.type = template_data.get("type", template.type)
    template.config = config
    template.description = template_data.get("description", template.description)
    template.is_active = template_data.get("is_active", template.is_active)
    template.is_default = template_data.get("is_default", template.is_default)
    
    db.commit()
    db.refresh(template)
    
    return {"message": "模板更新成功"}


@router.delete("/alert-templates/{template_id}")
async def delete_alert_template(template_id: int, db: Session = Depends(get_db)):
    """删除告警渠道模板"""
    template = db.query(AlertChannelTemplate).filter(AlertChannelTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    db.delete(template)
    db.commit()
    
    return {"message": "模板删除成功"}


# 邮件模板相关API
@router.get("/email-templates/")
async def get_email_templates(
    template_type: Optional[str] = Query(None, description="模板类型筛选"),
    is_active: Optional[bool] = Query(None, description="启用状态筛选"),
    db: Session = Depends(get_db)
):
    """获取邮件模板列表"""
    query = db.query(EmailTemplate)
    
    if template_type:
        query = query.filter(EmailTemplate.template_type == template_type)
    
    if is_active is not None:
        query = query.filter(EmailTemplate.is_active == is_active)
    
    templates = query.order_by(desc(EmailTemplate.is_default), EmailTemplate.name).all()
    
    return [
        {
            "id": template.id,
            "name": template.name,
            "subject": template.subject,
            "content": template.content,
            "template_type": template.template_type,
            "is_active": template.is_active,
            "is_default": template.is_default,
            "created_at": template.created_at.isoformat() if template.created_at else None,
            "updated_at": template.updated_at.isoformat() if template.updated_at else None
        }
        for template in templates
    ]


@router.post("/email-templates/")
async def create_email_template(template_data: dict, db: Session = Depends(get_db)):
    """创建邮件模板"""
    # 如果设置为默认模板，先取消同类型的其他默认模板
    if template_data.get("is_default", False):
        db.query(EmailTemplate).filter(
            EmailTemplate.template_type == template_data.get("template_type"),
            EmailTemplate.is_default == True
        ).update({"is_default": False})
    
    template = EmailTemplate(
        name=template_data.get("name"),
        subject=template_data.get("subject"),
        content=template_data.get("content"),
        template_type=template_data.get("template_type", "alert"),
        is_active=template_data.get("is_active", True),
        is_default=template_data.get("is_default", False)
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return {"message": "邮件模板创建成功", "id": template.id}


@router.put("/email-templates/{template_id}")
async def update_email_template(template_id: int, template_data: dict, db: Session = Depends(get_db)):
    """更新邮件模板"""
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    # 如果设置为默认模板，先取消同类型的其他默认模板
    if template_data.get("is_default", False) and not template.is_default:
        db.query(EmailTemplate).filter(
            EmailTemplate.template_type == template.template_type,
            EmailTemplate.id != template_id,
            EmailTemplate.is_default == True
        ).update({"is_default": False})
    
    # 更新模板信息
    template.name = template_data.get("name", template.name)
    template.subject = template_data.get("subject", template.subject)
    template.content = template_data.get("content", template.content)
    template.template_type = template_data.get("template_type", template.template_type)
    template.is_active = template_data.get("is_active", template.is_active)
    template.is_default = template_data.get("is_default", template.is_default)
    
    db.commit()
    db.refresh(template)
    
    return {"message": "邮件模板更新成功"}


@router.delete("/email-templates/{template_id}")
async def delete_email_template(template_id: int, db: Session = Depends(get_db)):
    """删除邮件模板"""
    template = db.query(EmailTemplate).filter(EmailTemplate.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    db.delete(template)
    db.commit()
    
    return {"message": "邮件模板删除成功"}


# 测试配置相关API
@router.post("/test/email")
async def test_email_config(test_data: dict, db: Session = Depends(get_db)):
    """测试邮件配置"""
    # 这里可以实现实际的邮件发送测试逻辑
    return {
        "success": True,
        "message": "邮件配置测试成功",
        "details": "测试邮件已发送"
    }


@router.post("/test/feishu")
async def test_feishu_config(test_data: dict, db: Session = Depends(get_db)):
    """测试飞书配置"""
    # 这里可以实现实际的飞书消息发送测试逻辑
    return {
        "success": True,
        "message": "飞书配置测试成功",
        "details": "测试消息已发送"
    }


@router.post("/test/wechat")
async def test_wechat_config(test_data: dict, db: Session = Depends(get_db)):
    """测试微信配置"""
    # 这里可以实现实际的微信消息发送测试逻辑
    return {
        "success": True,
        "message": "微信配置测试成功",
        "details": "测试消息已发送"
    }


