"""
数据库配置和初始化 - 优化版本
"""
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging

from .config import settings

logger = logging.getLogger(__name__)

# 优化数据库连接池配置
if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite配置
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=settings.DEBUG
    )
elif settings.DATABASE_URL.startswith("mysql"):
    # MySQL配置 - 优化连接池设置
    engine = create_engine(
        settings.DATABASE_URL,
        poolclass=QueuePool,
        pool_size=max(20, settings.DB_POOL_SIZE),  # 增加基础连接池大小
        max_overflow=max(50, settings.DB_MAX_OVERFLOW),  # 增加最大溢出连接数
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=1800,  # 减少连接回收时间到30分钟
        pool_pre_ping=True,  # 连接前检查连接是否有效
        echo=settings.DEBUG,
        connect_args={
            "charset": "utf8mb4",
            "autocommit": False,
            # 添加连接超时设置
            "connect_timeout": 10,
            "read_timeout": 30,
            "write_timeout": 30,
        }
    )
else:
    # 其他数据库配置（PostgreSQL等）
    engine = create_engine(
        settings.DATABASE_URL, 
        echo=settings.DEBUG,
        pool_size=max(20, settings.DB_POOL_SIZE),
        max_overflow=max(50, settings.DB_MAX_OVERFLOW),
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_recycle=1800,
        pool_pre_ping=True
    )

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基础模型类
Base = declarative_base()


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager  # 改为同步上下文管理器
def get_db_session():
    """同步上下文管理器获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"数据库事务失败: {str(e)}")
        raise
    finally:
        db.close()


def get_db_sync():
    """同步获取数据库会话的上下文管理器"""
    class DatabaseSession:
        def __init__(self):
            self.db = None
            
        def __enter__(self):
            self.db = SessionLocal()
            return self.db
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                self.db.rollback()
                logger.error(f"数据库事务失败: {exc_val}")
            else:
                self.db.commit()
            self.db.close()
    
    return DatabaseSession()


async def init_db():
    """初始化数据库"""
    from app.models import service, monitor_log, alert_config
    
    print("初始化数据库...")
    
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("数据库表创建完成")
        
        # 测试数据库连接
        with get_db_sync() as db:
            db.execute(text('SELECT 1'))
            print("数据库连接测试成功")
            
        # 输出连接池状态
        pool = engine.pool
        print(f"数据库连接池状态: size={pool.size()}, checked_in={pool.checkedin()}, checked_out={pool.checkedout()}")
            
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        raise
    
    print("数据库初始化完成")


def get_db_info():
    """获取数据库信息"""
    db_url = settings.DATABASE_URL
    if "mysql" in db_url:
        return "MySQL"
    elif "postgresql" in db_url:
        return "PostgreSQL"
    elif "sqlite" in db_url:
        return "SQLite"
    else:
        return "Unknown"


def get_pool_status():
    """获取连接池状态"""
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "invalid": pool.invalidated()
    }