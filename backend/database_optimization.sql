-- monitor_logs表性能优化脚本 - 简化版本
-- 只包含索引优化，不使用存储过程和视图

USE business_monitor;

-- 1. 添加关键索引
-- 为service_id添加索引（如果不存在）
CREATE INDEX idx_monitor_logs_service_id ON monitor_logs(service_id);

-- 为check_time添加索引（用于时间范围查询）
CREATE INDEX idx_monitor_logs_check_time ON monitor_logs(check_time);

-- 为status添加索引（用于状态筛选）
CREATE INDEX idx_monitor_logs_status ON monitor_logs(status);

-- 2. 添加复合索引优化常见查询
-- 服务ID + 检查时间复合索引（最常用的组合查询）
CREATE INDEX idx_monitor_logs_service_time ON monitor_logs(service_id, check_time);

-- 状态 + 检查时间复合索引（用于统计查询）
CREATE INDEX idx_monitor_logs_status_time ON monitor_logs(status, check_time);

-- 检查时间 + 状态 + 服务ID复合索引（用于复杂筛选）
CREATE INDEX idx_monitor_logs_time_status_service ON monitor_logs(check_time, status, service_id);

-- 3. 为告警相关字段添加索引
CREATE INDEX idx_monitor_logs_alert_sent ON monitor_logs(alert_sent);

-- 4. 创建系统日志表（用于记录维护操作）
CREATE TABLE IF NOT EXISTS system_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    operation VARCHAR(50) NOT NULL,
    message TEXT,
    details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_operation (operation),
    INDEX idx_created_at (created_at)
);

-- 5. 分析表以更新统计信息
ANALYZE TABLE monitor_logs;
