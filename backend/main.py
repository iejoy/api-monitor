"""
业务应用监控平台 - 主入口文件（优化版本）
"""
import asyncio
import signal
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.api.routes import api_router
from app.services.scheduler import scheduler_service
from app.services.maintenance_scheduler import maintenance_scheduler
from app.services.monitor import monitor_service
from app.services.alert import alert_service

# 配置日志 - 移除emoji字符避免Windows编码问题
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('business_monitor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 全局变量用于优雅关闭
shutdown_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("启动业务监控平台...")
    
    try:
        # 初始化数据库
        await init_db()
        
        # 启动调度器
        scheduler_service.start()
        logger.info("监控调度器已启动")
        
        # 启动维护调度器
        await maintenance_scheduler.start()
        logger.info("维护调度器已启动")
        
        # 设置信号处理器
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，准备优雅关闭...")
            shutdown_event.set()
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        logger.info("业务监控平台启动完成")
        
        yield
        
    except Exception as e:
        logger.error(f"启动失败: {str(e)}")
        raise
    finally:
        # 关闭时执行
        logger.info("开始关闭业务监控平台...")
        
        try:
            # 停止调度器
            scheduler_service.shutdown()
            logger.info("监控调度器已停止")
            
            # 停止维护调度器
            await maintenance_scheduler.stop()
            logger.info("维护调度器已停止")
            
            # 关闭监控服务HTTP客户端
            await monitor_service.close()
            logger.info("监控服务HTTP客户端已关闭")
            
            # 关闭告警服务HTTP客户端
            await alert_service.close()
            logger.info("告警服务HTTP客户端已关闭")
            
            # 等待所有异步任务完成
            await asyncio.sleep(1)
            
            logger.info("业务监控平台关闭完成")
            
        except Exception as e:
            logger.error(f"关闭过程中出错: {str(e)}")


# 创建FastAPI应用
app = FastAPI(
    title="业务应用监控平台",
    description="定期监控业务服务状态，支持多种告警方式",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "业务应用监控平台 API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        from app.core.database import get_pool_status
        
        # 获取数据库连接池状态
        pool_status = get_pool_status()
        
        # 获取监控服务状态
        monitor_info = monitor_service.get_client_info()
        
        # 获取调度器状态
        scheduler_status = scheduler_service.get_job_status()
        maintenance_status = maintenance_scheduler.get_job_status()
        
        return {
            "status": "healthy", 
            "service": "business-monitor",
            "database_pool": pool_status,
            "monitor_service": monitor_info,
            "scheduler": {
                "monitor_scheduler_running": scheduler_status["running"],
                "monitor_jobs": scheduler_status["total_jobs"],
                "maintenance_scheduler_running": maintenance_status["status"] == "running",
                "maintenance_jobs": len(maintenance_status.get("jobs", []))
            }
        }
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return {
            "status": "unhealthy", 
            "service": "business-monitor",
            "error": str(e)
        }


@app.get("/status")
async def system_status():
    """系统状态详细信息"""
    try:
        from app.core.database import get_pool_status
        
        # 数据库连接池状态
        pool_status = get_pool_status()
        
        # 监控服务状态
        monitor_info = monitor_service.get_client_info()
        
        # 调度器状态
        scheduler_status = scheduler_service.get_job_status()
        maintenance_status = maintenance_scheduler.get_job_status()
        
        # 表统计信息
        from app.services.data_cleanup import data_cleanup_service
        table_stats = data_cleanup_service.get_table_stats()
        
        return {
            "timestamp": asyncio.get_event_loop().time(),
            "database": {
                "connection_pool": pool_status,
                "table_stats": table_stats
            },
            "services": {
                "monitor_service": monitor_info,
                "scheduler_service": scheduler_status,
                "maintenance_service": maintenance_status
            }
        }
    except Exception as e:
        logger.error(f"获取系统状态失败: {str(e)}")
        return {"error": str(e)}


async def graceful_shutdown():
    """优雅关闭处理"""
    logger.info("开始执行优雅关闭流程...")
    
    # 等待关闭信号
    await shutdown_event.wait()
    
    # 执行清理工作
    try:
        scheduler_service.shutdown()
        await maintenance_scheduler.stop()
        await monitor_service.close()
        await alert_service.close()
    except Exception as e:
        logger.error(f"优雅关闭过程中出错: {str(e)}")


if __name__ == "__main__":
    try:
        # 使用8001端口避免冲突
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=8001,  # 改为8001端口
            reload=False,  # 生产环境关闭热重载
            log_level="info",
            access_log=True,
            # 添加工作进程和连接限制
            workers=1,  # 单进程模式，避免多进程间的资源竞争
            limit_concurrency=1000,  # 限制并发连接数
            limit_max_requests=10000,  # 限制每个worker处理的最大请求数
            timeout_keep_alive=30,  # Keep-alive超时时间
        )
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务...")
    except Exception as e:
        logger.error(f"服务运行异常: {str(e)}")