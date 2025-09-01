# 业务应用监控平台

一个基于Python FastAPI + Vue3的业务应用监控平台，支持定期监控业务服务状态，并通过飞书、微信、邮件等方式发送告警通知。

## 功能特性

- 🔍 **服务监控**: 定期监控业务服务的可用性和响应时间
- 📊 **数据统计**: 提供监控数据的统计分析和可视化图表
- 🚨 **多渠道告警**: 支持飞书、微信、邮件等多种告警方式
- ⚙️ **灵活配置**: 支持动态配置监控周期和告警规则
- 🐳 **容器化部署**: 提供完整的Docker部署方案
- 💾 **MySQL存储**: 使用MySQL数据库存储监控数据

## 技术栈

### 后端
- **Python 3.9+**
- **FastAPI**: 现代化的Web框架
- **SQLAlchemy**: ORM框架
- **PyMySQL**: MySQL数据库驱动
- **APScheduler**: 任务调度
- **Pydantic**: 数据验证

### 前端
- **Vue 3**: 渐进式JavaScript框架
- **Element Plus**: UI组件库
- **ECharts**: 数据可视化
- **Pinia**: 状态管理
- **Vite**: 构建工具

### 数据库
- **MySQL 8.0**: 关系型数据库

## 快速开始

### 方式一：Docker部署（推荐）

1. **克隆项目**
```bash
git clone <repository-url>
cd business-monitor
```

2. **启动服务**
```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

3. **访问应用**
- 前端界面: http://localhost
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

### 方式二：本地开发

#### 环境要求
- Python 3.9+
- Node.js 16+
- MySQL 8.0+

#### 后端启动

1. **安装依赖**
```bash
cd backend
pip install -r requirements.txt
```

2. **配置数据库**
```bash
# 创建数据库
mysql -u root -p
CREATE DATABASE business_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'monitor'@'%' IDENTIFIED BY 'monitor123';
GRANT ALL PRIVILEGES ON business_monitor.* TO 'monitor'@'%';
FLUSH PRIVILEGES;

# 导入初始化脚本
mysql -u monitor -p business_monitor < init_mysql.sql
```


`

4. **启动后端服务**
```bash
# Linux/Mac
./start.sh

# Windows
start.bat

# 或直接运行
python main.py
```

#### 前端启动

1. **安装依赖**
```bash
cd frontend
npm install
```

2. **启动开发服务器**
```bash
npm run dev
```

3. **构建生产版本**
```bash
npm run build
```

## 配置说明

### 数据库配置

项目使用MySQL作为数据存储，主要配置参数：

```env
# MySQL数据库配置
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=monitor
MYSQL_PASSWORD=monitor123
MYSQL_DATABASE=business_monitor

# 数据库连接URL
DATABASE_URL=mysql+pymysql://monitor:monitor123@localhost:3306/business_monitor

# 连接池配置
MYSQL_POOL_SIZE=10
MYSQL_MAX_OVERFLOW=20
MYSQL_POOL_TIMEOUT=30
MYSQL_POOL_RECYCLE=3600
```

### 告警配置

支持多种告警方式，需要在环境变量中配置相应的参数：

#### 邮件告警
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
```

#### 飞书告警
```env
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-token
```

#### 微信告警
```env
WECHAT_WEBHOOK_URL=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=your-webhook-key
```

## 数据库结构

### 服务表 (services)
- `id`: 主键
- `name`: 服务名称
- `url`: 监控URL
- `method`: HTTP方法（默认GET）
- `timeout`: 超时时间（秒）
- `interval`: 监控间隔（分钟）
- `is_active`: 是否启用
- `created_at`: 创建时间
- `updated_at`: 更新时间

### 监控日志表 (monitor_logs)
- `id`: 主键
- `service_id`: 服务ID（外键）
- `status`: 监控状态
- `response_time`: 响应时间（毫秒）
- `status_code`: HTTP状态码
- `error_message`: 错误信息
- `created_at`: 监控时间

### 告警配置表 (alert_configs)
- `id`: 主键
- `service_id`: 服务ID（外键）
- `alert_type`: 告警类型（email/feishu/wechat）
- `alert_target`: 告警目标（邮箱/webhook等）
- `is_active`: 是否启用
- `created_at`: 创建时间
- `updated_at`: 更新时间

## API接口

### 服务管理
- `GET /api/services` - 获取服务列表
- `POST /api/services` - 创建服务
- `PUT /api/services/{id}` - 更新服务
- `DELETE /api/services/{id}` - 删除服务

### 监控日志
- `GET /api/monitor-logs` - 获取监控日志
- `GET /api/monitor-logs/{service_id}` - 获取指定服务的监控日志

### 告警配置
- `GET /api/alert-configs` - 获取告警配置
- `POST /api/alert-configs` - 创建告警配置
- `PUT /api/alert-configs/{id}` - 更新告警配置
- `DELETE /api/alert-configs/{id}` - 删除告警配置

### 仪表板
- `GET /api/dashboard/stats` - 获取统计数据
- `GET /api/dashboard/charts` - 获取图表数据

## 部署说明

### Docker部署

项目提供了完整的Docker部署配置，包含以下服务：

- **MySQL**: 数据库服务
- **Backend**: Python FastAPI后端服务
- **Frontend**: Nginx + Vue3前端服务
- **Redis**: 缓存服务（可选）

#### 服务端口
- 前端: 80
- 后端: 8000
- MySQL: 3306
- Redis: 6379

#### 数据持久化
- MySQL数据: `mysql_data` volume
- Redis数据: `redis_data` volume

### 生产环境建议

1. **安全配置**
   - 修改默认密码
   - 配置防火墙规则
   - 使用HTTPS证书

2. **性能优化**
   - 调整MySQL配置参数
   - 配置Redis缓存
   - 使用负载均衡

3. **监控告警**
   - 配置系统监控
   - 设置日志收集
   - 建立备份策略

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查MySQL服务是否启动
   - 验证数据库配置参数
   - 确认网络连接正常

2. **前端无法访问后端**
   - 检查后端服务状态
   - 验证API接口地址
   - 查看浏览器控制台错误

3. **告警不生效**
   - 检查告警配置参数
   - 验证webhook地址
   - 查看后端日志错误

### 日志查看

```bash
# Docker环境
docker-compose logs backend
docker-compose logs frontend
docker-compose logs mysql

# 本地环境
tail -f backend/logs/app.log
```

## 开发指南

### 后端开发

1. **添加新的API接口**
   - 在 `app/api/endpoints/` 目录下创建新的路由文件
   - 在 `app/api/routes.py` 中注册路由
   - 添加相应的数据模型和验证

2. **添加新的监控类型**
   - 扩展 `app/services/monitor.py` 中的监控逻辑
   - 更新数据库模型支持新字段
   - 添加相应的配置参数

### 前端开发

1. **添加新页面**
   - 在 `src/views/` 目录下创建Vue组件
   - 在 `src/router/` 中配置路由
   - 更新导航菜单

2. **添加新组件**
   - 在 `src/components/` 目录下创建组件
   - 遵循Vue3 Composition API规范
   - 使用Element Plus组件库

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进项目。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交Issue: [项目Issues页面]
- 邮件联系: [联系邮箱]