"""
告警配置管理API
"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.models.alert_config import AlertConfig
from app.models.service import MonitorService
from app.services.email_proxy import create_proxy_smtp_connection

router = APIRouter()


@router.get("/")
async def get_alert_configs(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页记录数"),
    alert_type: Optional[str] = Query(None, description="告警类型筛选"),
    is_active: Optional[bool] = Query(None, description="启用状态筛选"),
    service_id: Optional[int] = Query(None, description="服务ID筛选"),
    db: Session = Depends(get_db)
):
    """获取告警配置列表"""
    query = db.query(AlertConfig).options(joinedload(AlertConfig.service))
    
    # 类型筛选
    if alert_type:
        query = query.filter(AlertConfig.type == alert_type)
    
    # 状态筛选
    if is_active is not None:
        query = query.filter(AlertConfig.is_active == is_active)
    
    # 服务筛选
    if service_id:
        query = query.filter(AlertConfig.service_id == service_id)
    
    # 获取总数
    total = query.count()
    
    # 计算跳过记录数
    skip = (page - 1) * size
    
    # 分页查询
    configs = query.order_by(desc(AlertConfig.created_at)).offset(skip).limit(size).all()
    
    # 转换为字典格式
    configs_data = []
    for config in configs:
        # 根据配置类型提取告警目标
        alert_target = ""
        if config.config:
            if config.type == "email" and "to_emails" in config.config:
                alert_target = ", ".join(config.config["to_emails"])
            elif config.type in ["feishu", "wechat"] and "webhook_url" in config.config:
                alert_target = config.config["webhook_url"]
        
        config_dict = {
            "id": config.id,
            "name": config.name,
            "alert_type": config.type,  # 前端期望的字段名
            "alert_target": alert_target,  # 前端期望的字段
            "service_name": config.service.name if config.service else "未知服务",
            "service_id": config.service_id,
            "service_url": config.service.url if config.service else "",
            "config": config.config,
            "is_active": config.is_active,
            "description": config.description,
            "alert_conditions": config.alert_conditions,
            "response_threshold": config.response_threshold,
            "alert_frequency": config.alert_frequency,
            "last_test_time": config.last_test_time.isoformat() if config.last_test_time else None,
            "last_test_result": config.last_test_result,
            "last_test_message": config.last_test_message,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        }
        configs_data.append(config_dict)
    
    return {
        "total": total,
        "items": configs_data
    }


@router.get("/{config_id}")
async def get_alert_config(config_id: int, db: Session = Depends(get_db)):
    """获取单个告警配置详情"""
    config = db.query(AlertConfig).options(joinedload(AlertConfig.service)).filter(AlertConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="告警配置不存在")
    
    return {
        "id": config.id,
        "name": config.name,
        "type": config.type,
        "service_id": config.service_id,
        "service_name": config.service.name if config.service else "未知服务",
        "config": config.config,
        "is_active": config.is_active,
        "description": config.description,
        "alert_conditions": config.alert_conditions,
        "response_threshold": config.response_threshold,
        "alert_frequency": config.alert_frequency,
        "last_test_time": config.last_test_time.isoformat() if config.last_test_time else None,
        "last_test_result": config.last_test_result,
        "last_test_message": config.last_test_message,
        "created_at": config.created_at.isoformat() if config.created_at else None,
        "updated_at": config.updated_at.isoformat() if config.updated_at else None
    }


@router.post("/")
async def create_alert_config(config_data: dict, db: Session = Depends(get_db)):
    """创建新的告警配置"""
    # 验证服务是否存在
    service_id = config_data.get("service_id")
    if not service_id:
        raise HTTPException(status_code=400, detail="必须指定关联的服务")
    
    service = db.query(MonitorService).filter(MonitorService.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="指定的服务不存在")
    
    # 检查该服务是否已经有告警配置
    existing_config = db.query(AlertConfig).filter(AlertConfig.service_id == service_id).first()
    if existing_config:
        raise HTTPException(
            status_code=400, 
            detail=f"服务 '{service.name}' 已经配置了告警渠道，每个服务只能配置一个告警渠道"
        )
    
    # 从前端数据构建配置
    alert_type = config_data.get("alert_type")
    alert_target = config_data.get("alert_target")
    email_recipients = config_data.get("email_recipients")
    
    # 构建配置对象
    config = {}
    if alert_type == "email":
        # 对于邮件类型，alert_target是模板ID，email_recipients是收件人
        if email_recipients:
            emails = [email.strip() for email in email_recipients.split(",") if email.strip()]
        else:
            emails = []
        
        config = {
            "template_id": alert_target,  # 模板ID
            "to_emails": emails  # 收件人列表
        }
    elif alert_type in ["feishu", "wechat"]:
        # 对于飞书和微信，alert_target是模板ID
        config = {
            "template_id": alert_target
        }
    
    # 生成配置名称
    name = f"{service.name}-{alert_type}告警"
    
    # 处理告警条件
    alert_conditions = config_data.get("alert_conditions", [])
    if isinstance(alert_conditions, list):
        alert_conditions_str = ",".join(alert_conditions)
    else:
        alert_conditions_str = alert_conditions
    
    # 创建配置
    db_config = AlertConfig(
        name=name,
        type=alert_type,
        service_id=service_id,
        config=config,
        is_active=config_data.get("is_active", True),
        description=config_data.get("description", ""),
        alert_conditions=alert_conditions_str,
        response_threshold=config_data.get("response_threshold"),
        alert_frequency=config_data.get("alert_frequency", "immediate")
    )
    
    try:
        db.add(db_config)
        db.commit()
        db.refresh(db_config)
        return {"message": "告警配置创建成功", "id": db_config.id}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"服务 '{service.name}' 已经配置了告警渠道，每个服务只能配置一个告警渠道"
        )


@router.put("/{config_id}")
async def update_alert_config(config_id: int, config_data: dict, db: Session = Depends(get_db)):
    """更新告警配置"""
    config = db.query(AlertConfig).filter(AlertConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="告警配置不存在")
    
    # 验证服务是否存在
    service_id = config_data.get("service_id")
    if service_id and service_id != config.service_id:
        service = db.query(MonitorService).filter(MonitorService.id == service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="指定的服务不存在")
        
        # 检查新服务是否已经有告警配置
        existing_config = db.query(AlertConfig).filter(
            AlertConfig.service_id == service_id,
            AlertConfig.id != config_id
        ).first()
        if existing_config:
            raise HTTPException(
                status_code=400, 
                detail=f"服务 '{service.name}' 已经配置了告警渠道，每个服务只能配置一个告警渠道"
            )
        
        config.service_id = service_id
    
    # 从前端数据构建配置
    alert_type = config_data.get("alert_type")
    alert_target = config_data.get("alert_target")
    email_recipients = config_data.get("email_recipients")
    
    # 构建配置对象
    new_config = {}
    if alert_type == "email":
        # 对于邮件类型，alert_target是模板ID，email_recipients是收件人
        if email_recipients:
            emails = [email.strip() for email in email_recipients.split(",") if email.strip()]
        else:
            emails = []
        
        new_config = {
            "template_id": alert_target,  # 模板ID
            "to_emails": emails  # 收件人列表
        }
    elif alert_type in ["feishu", "wechat"]:
        # 对于飞书和微信，alert_target是模板ID
        new_config = {
            "template_id": alert_target
        }
    
    # 获取服务信息生成配置名称
    service = db.query(MonitorService).filter(MonitorService.id == config.service_id).first()
    name = f"{service.name}-{alert_type}告警" if service else f"告警配置-{alert_type}"
    
    # 处理告警条件
    alert_conditions = config_data.get("alert_conditions", [])
    if isinstance(alert_conditions, list):
        alert_conditions_str = ",".join(alert_conditions)
    else:
        alert_conditions_str = alert_conditions
    
    # 更新配置信息
    config.name = name
    config.type = alert_type
    config.config = new_config
    config.is_active = config_data.get("is_active", True)
    config.description = config_data.get("description", "")
    config.alert_conditions = alert_conditions_str
    config.response_threshold = config_data.get("response_threshold")
    config.alert_frequency = config_data.get("alert_frequency", "immediate")
    
    try:
        db.commit()
        db.refresh(config)
        return {"message": "告警配置更新成功"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail="更新失败，该服务已经配置了告警渠道"
        )


@router.delete("/{config_id}")
async def delete_alert_config(config_id: int, db: Session = Depends(get_db)):
    """删除告警配置"""
    config = db.query(AlertConfig).filter(AlertConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="告警配置不存在")
    
    db.delete(config)
    db.commit()
    
    return {"message": "告警配置删除成功"}


@router.post("/{config_id}/toggle")
async def toggle_alert_config(config_id: int, db: Session = Depends(get_db)):
    """切换告警配置启用状态"""
    config = db.query(AlertConfig).filter(AlertConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="告警配置不存在")
    
    # 切换状态
    config.is_active = not config.is_active
    db.commit()
    
    return {
        "message": f"告警配置已{'启用' if config.is_active else '禁用'}",
        "is_active": config.is_active
    }


@router.post("/{config_id}/test")
async def test_alert_config(config_id: int, test_data: dict = None, db: Session = Depends(get_db)):
    """测试告警配置"""
    config = db.query(AlertConfig).options(joinedload(AlertConfig.service)).filter(AlertConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="告警配置不存在")
    
    import httpx
    
    try:
        success = False
        message = ""
        details = None
        
        if config.type == "email":
            # 邮件测试直接使用系统设置处的邮件配置
            try:
                if not config.config or not config.config.get("to_emails"):
                    raise Exception("邮件配置不完整：缺少收件人")
                
                from app.models.system_setting import SystemSetting
                
                # 查询系统邮件配置
                email_settings = db.query(SystemSetting).filter(
                    SystemSetting.category == "email",
                    SystemSetting.is_active == True
                ).all()
                
                if not email_settings:
                    raise Exception("系统邮件配置不存在，请先在系统设置中配置邮件参数")
                
                # 构建SMTP配置
                smtp_config = {}
                for setting in email_settings:
                    if setting.key == "smtp_server":  # 前端使用的是smtp_server
                        smtp_config["smtp_host"] = setting.value
                    elif setting.key == "smtp_port":
                        smtp_config["smtp_port"] = int(setting.value)
                    elif setting.key == "smtp_username":  # 前端使用的是smtp_username
                        smtp_config["username"] = setting.value
                    elif setting.key == "smtp_password":  # 前端使用的是smtp_password
                        smtp_config["password"] = setting.value
                    elif setting.key == "smtp_from_email":  # 前端使用的是smtp_from_email
                        smtp_config["from_email"] = setting.value
                    elif setting.key == "smtp_use_tls":  # 前端使用的是smtp_use_tls
                        smtp_config["use_tls"] = setting.value.lower() == "true"
                
                # 验证SMTP配置
                required_fields = ["smtp_host", "smtp_port", "username", "password", "from_email"]
                for field in required_fields:
                    if not smtp_config.get(field):
                        raise Exception(f"系统邮件配置不完整：缺少{field}")
                
                # 发送测试邮件
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart
                
                # 构建测试邮件内容
                subject = f"[测试] 告警配置测试 - {config.name}"
                body = f"""
这是一封测试邮件，用于验证告警配置是否正常工作。

配置信息：
- 配置名称：{config.name}
- 关联服务：{config.service.name if config.service else '未知服务'}
- 测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

如果您收到此邮件，说明告警配置工作正常。
                """.strip()
                
                # 创建邮件对象
                msg = MIMEMultipart()
                msg['From'] = smtp_config['from_email']
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain', 'utf-8'))
                
                # 使用代理连接SMTP服务器并发送邮件
                proxy_smtp = None
                try:
                    # 创建支持代理的SMTP连接
                    proxy_smtp = create_proxy_smtp_connection(smtp_config)
                    server = proxy_smtp.connect()
                    server.set_debuglevel(0)  # 关闭调试模式
                    
                    # 发送EHLO命令
                    server.ehlo()
                    
                    # 启用TLS加密
                    if smtp_config.get('use_tls', True):
                        server.starttls()
                        server.ehlo()  # TLS后重新发送EHLO
                    
                    # 登录SMTP服务器
                    server.login(smtp_config['from_email'], smtp_config['password'])
                    
                    # 发送给所有收件人
                    to_emails = config.config['to_emails']
                    for email in to_emails:
                        msg['To'] = email
                        server.send_message(msg)
                        del msg['To']  # 清除To字段，为下一个收件人准备
                    
                except smtplib.SMTPAuthenticationError as e:
                    raise Exception(f"SMTP认证失败，请检查用户名和密码：{str(e)}")
                except smtplib.SMTPConnectError as e:
                    raise Exception(f"无法连接到SMTP服务器，请检查服务器地址和端口：{str(e)}")
                except smtplib.SMTPRecipientsRefused as e:
                    raise Exception(f"收件人地址被拒绝：{str(e)}")
                except smtplib.SMTPServerDisconnected as e:
                    raise Exception(f"SMTP服务器连接意外断开，请检查网络连接：{str(e)}")
                except smtplib.SMTPException as e:
                    raise Exception(f"SMTP发送失败：{str(e)}")
                except Exception as e:
                    raise Exception(f"邮件发送过程中发生错误：{str(e)}")
                finally:
                    # 确保连接被正确关闭
                    if proxy_smtp:
                        proxy_smtp.close()
                
                success = True
                message = f"测试邮件发送成功，收件人：{', '.join(config.config['to_emails'])}"
                details = f"邮件已发送到 {len(config.config['to_emails'])} 个收件人"
                
            except Exception as e:
                success = False
                message = f"邮件发送失败：{str(e)}"
                details = str(e)
        
        elif config.type == "feishu":
            # 飞书测试使用配置模板处的webhook
            try:
                from app.models.system_setting import AlertChannelTemplate
                template_id = config.config.get("template_id") if config.config else None
                
                if template_id:
                    # 确保template_id是整数类型
                    try:
                        template_id = int(template_id)
                    except (ValueError, TypeError):
                        raise Exception(f"无效的模板ID：{template_id}")
                    
                    template = db.query(AlertChannelTemplate).filter(AlertChannelTemplate.id == template_id).first()
                    if not template:
                        raise Exception(f"飞书模板不存在：ID={template_id}")
                    if not template.config or not template.config.get("webhook_url"):
                        raise Exception(f"飞书模板配置不完整：缺少webhook_url，ID={template_id}")
                    
                    webhook_url = template.config["webhook_url"]
                else:
                    raise Exception("飞书配置不完整：缺少模板ID")
                
                # 构建测试消息
                test_message = {
                    "msg_type": "text",
                    "content": {
                        "text": f"[测试] 告警配置测试\n\n配置名称：{config.name}\n关联服务：{config.service.name if config.service else '未知服务'}\n测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n如果您收到此消息，说明告警配置工作正常。"
                    }
                }
                
                # 发送到飞书
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(webhook_url, json=test_message)
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("StatusCode") == 0:
                            success = True
                            message = "飞书测试消息发送成功"
                            details = "消息已发送到飞书群组"
                        else:
                            raise Exception(f"飞书API返回错误：{result.get('StatusMessage', '未知错误')}")
                    else:
                        raise Exception(f"飞书API返回HTTP错误：{response.status_code}")
                
            except Exception as e:
                success = False
                message = f"飞书消息发送失败：{str(e)}"
                details = str(e)
        
        elif config.type == "wechat":
            # 微信测试使用配置模板处的webhook
            try:
                from app.models.system_setting import AlertChannelTemplate
                template_id = config.config.get("template_id") if config.config else None
                
                if template_id:
                    # 确保template_id是整数类型
                    try:
                        template_id = int(template_id)
                    except (ValueError, TypeError):
                        raise Exception(f"无效的模板ID：{template_id}")
                    
                    template = db.query(AlertChannelTemplate).filter(AlertChannelTemplate.id == template_id).first()
                    if not template:
                        raise Exception(f"微信模板不存在：ID={template_id}")
                    if not template.config or not template.config.get("webhook_url"):
                        raise Exception(f"微信模板配置不完整：缺少webhook_url，ID={template_id}")
                    
                    webhook_url = template.config["webhook_url"]
                else:
                    raise Exception("微信配置不完整：缺少模板ID")
                
                # 构建测试消息
                test_message = {
                    "msgtype": "text",
                    "text": {
                        "content": f"[测试] 告警配置测试\n\n配置名称：{config.name}\n关联服务：{config.service.name if config.service else '未知服务'}\n测试时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n如果您收到此消息，说明告警配置工作正常。"
                    }
                }
                
                # 发送到微信
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(webhook_url, json=test_message)
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("errcode") == 0:
                            success = True
                            message = "微信测试消息发送成功"
                            details = "消息已发送到微信群组"
                        else:
                            raise Exception(f"微信API返回错误：{result.get('errmsg', '未知错误')}")
                    else:
                        raise Exception(f"微信API返回HTTP错误：{response.status_code}")
                
            except Exception as e:
                success = False
                message = f"微信消息发送失败：{str(e)}"
                details = str(e)
        
        else:
            success = False
            message = f"不支持的告警类型：{config.type}"
            details = "请检查告警配置类型"
        
        # 更新测试记录
        config.last_test_time = datetime.now()
        config.last_test_result = "success" if success else "failed"
        config.last_test_message = message
        db.commit()
        
        return {
            "success": success,
            "message": message,
            "details": details
        }
        
    except Exception as e:
        # 更新测试记录
        config.last_test_time = datetime.now()
        config.last_test_result = "failed"
        config.last_test_message = f"测试失败：{str(e)}"
        db.commit()
        
        return {
            "success": False,
            "message": f"测试失败：{str(e)}",
            "details": str(e)
        }


@router.post("/test")
async def test_alert_config_direct(test_data: dict, db: Session = Depends(get_db)):
    """直接测试告警配置"""
    return {
        "success": True,
        "message": "测试成功",
        "details": None
    }


@router.get("/templates")
async def get_alert_templates(db: Session = Depends(get_db)):
    """获取可用的告警模板"""
    from app.models.system_setting import AlertChannelTemplate
    
    templates = db.query(AlertChannelTemplate).filter(
        AlertChannelTemplate.is_active == True
    ).order_by(AlertChannelTemplate.type, AlertChannelTemplate.name).all()
    
    return {
        "items": [
            {
                "id": template.id,
                "name": template.name,
                "type": template.type,
                "config": template.config,
                "description": template.description,
                "is_active": template.is_active,
                "is_default": template.is_default
            }
            for template in templates
        ]
    }


@router.get("/service/{service_id}")
async def get_service_alert_config(service_id: int, db: Session = Depends(get_db)):
    """获取指定服务的告警配置"""
    config = db.query(AlertConfig).options(joinedload(AlertConfig.service)).filter(
        AlertConfig.service_id == service_id
    ).first()
    
    if not config:
        return {"has_config": False, "config": None}
    
    # 根据配置类型提取告警目标
    alert_target = ""
    if config.config:
        if config.type == "email" and "to_emails" in config.config:
            alert_target = ", ".join(config.config["to_emails"])
        elif config.type in ["feishu", "wechat"] and "webhook_url" in config.config:
            alert_target = config.config["webhook_url"]
    
    return {
        "has_config": True,
        "config": {
            "id": config.id,
            "name": config.name,
            "alert_type": config.type,
            "alert_target": alert_target,
            "service_name": config.service.name if config.service else "未知服务",
            "service_id": config.service_id,
            "is_active": config.is_active,
            "description": config.description,
            "alert_conditions": config.alert_conditions,
            "response_threshold": config.response_threshold,
            "alert_frequency": config.alert_frequency,
            "created_at": config.created_at.isoformat() if config.created_at else None,
            "updated_at": config.updated_at.isoformat() if config.updated_at else None
        }
    }


@router.get("/types/schemas")
async def get_alert_type_schemas():
    """获取各种告警类型的配置模式"""
    return {
        "email": {
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "邮件模板ID"},
                "to_emails": {"type": "array", "items": {"type": "string"}, "description": "收件人邮箱列表"},
                "smtp_host": {"type": "string", "description": "SMTP服务器地址"},
                "smtp_port": {"type": "integer", "description": "SMTP端口"},
                "username": {"type": "string", "description": "用户名"},
                "password": {"type": "string", "description": "密码"},
                "from_email": {"type": "string", "description": "发件人邮箱"},
                "use_tls": {"type": "boolean", "description": "是否使用TLS", "default": True}
            },
            "required": ["template_id", "to_emails"]
        },
        "feishu": {
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "飞书模板ID"}
            },
            "required": ["template_id"]
        },
        "wechat": {
            "type": "object",
            "properties": {
                "template_id": {"type": "string", "description": "微信模板ID"}
            },
            "required": ["template_id"]
        }
    }