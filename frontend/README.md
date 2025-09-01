# 业务监控平台前端

## 快速开始

### 1. 安装依赖
```bash
npm install
```

### 2. 配置后端API地址

#### 方法一：使用环境变量文件（推荐）
复制环境变量示例文件：
```bash
cp .env.local.example .env.local
```

编辑 `.env.local` 文件，设置你的后端API地址：
```bash
# 如果后端运行在本机
VITE_API_URL=http://localhost:8000

# 如果需要使用本机IP访问（局域网访问）
VITE_API_URL=http://192.168.1.100:8000

# 替换为你的实际IP地址
```

#### 方法二：直接修改配置文件
编辑 `vite.config.js` 文件中的 proxy 配置：
```javascript
proxy: {
  '/api': {
    target: 'http://你的后端地址:8000',
    changeOrigin: true,
  }
}
```

### 3. 启动开发服务器
```bash
npm run dev
```

## 网络访问配置

### 本机访问
- 前端地址：http://localhost:3000
- 后端地址：http://localhost:8000

### 局域网访问
如果需要在局域网内其他设备访问：

1. **获取本机IP地址**
   ```bash
   # Windows
   ipconfig
   
   # macOS/Linux
   ifconfig
   ```

2. **配置前端**
   - 修改 `.env.local` 中的 `VITE_API_URL` 为你的本机IP
   - 前端会自动绑定到 `0.0.0.0:3000`，支持外部访问

3. **配置后端**
   - 确保后端配置中 `HOST=0.0.0.0`（默认已配置）
   - 后端会监听所有网络接口

4. **访问地址**
   - 前端：http://你的IP:3000
   - 后端：http://你的IP:8000

### 常见问题解决

#### 问题1：前端无法访问后端API
**症状**：前端页面加载正常，但API请求失败

**解决方案**：
1. 检查 `.env.local` 中的 `VITE_API_URL` 是否正确
2. 确保后端服务正在运行
3. 检查防火墙是否阻止了端口访问
4. 尝试直接访问后端健康检查接口：http://你的IP:8000/health

#### 问题2：使用本机IP访问报错
**症状**：使用 `http://192.168.x.x:3000` 访问前端报错

**解决方案**：
1. 确保 `vite.config.js` 中配置了 `host: '0.0.0.0'`
2. 检查 `.env.local` 中的后端地址是否使用了正确的IP
3. 重启前端开发服务器：
   ```bash
   npm run dev
   ```

#### 问题3：CORS跨域错误
**症状**：浏览器控制台显示CORS错误

**解决方案**：
1. 后端已配置允许所有来源访问，通常不会有此问题
2. 如果仍有问题，检查后端是否正常启动
3. 确保使用代理访问API（通过前端的 `/api` 路径）

### 生产环境部署

#### 构建前端
```bash
npm run build
```

#### 使用Docker部署
```bash
# 构建镜像
docker build -t business-monitor-frontend .

# 运行容器
docker run -p 80:80 business-monitor-frontend
```

## 开发工具

### 代码格式化
```bash
npm run format
```

### 代码检查
```bash
npm run lint
```

### 预览构建结果
```bash
npm run preview
```

## 技术栈
- Vue 3
- Vite
- Element Plus
- Vue Router
- Pinia
- ECharts
- Axios

## 目录结构
```
src/
├── components/     # 公共组件
├── views/         # 页面组件
├── router/        # 路由配置
├── stores/        # 状态管理
├── utils/         # 工具函数
├── api/           # API接口
└── assets/        # 静态资源