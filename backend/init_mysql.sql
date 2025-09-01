-- 业务应用监控平台 MySQL数据库初始化脚本

-- 创建数据库
CREATE DATABASE IF NOT EXISTS business_monitor 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 创建用户（如果不存在）
CREATE USER IF NOT EXISTS 'monitor'@'localhost' IDENTIFIED BY 'monitor123';
CREATE USER IF NOT EXISTS 'monitor'@'%' IDENTIFIED BY 'monitor123';

-- 授权
GRANT ALL PRIVILEGES ON business_monitor.* TO 'monitor'@'localhost';
GRANT ALL PRIVILEGES ON business_monitor.* TO 'monitor'@'%';

-- 刷新权限
FLUSH PRIVILEGES;
