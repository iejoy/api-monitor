#!/bin/bash

# 业务应用监控平台启动脚本

echo "🚀 启动业务应用监控平台..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
if [[ $(echo "$python_version >= 3.8" | bc -l) -eq 0 ]]; then
    echo "❌ 错误: 需要Python 3.8或更高版本，当前版本: $python_version"
    exit 1
fi

# 检查Node.js版本
node_version=$(node --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
if [[ $(echo "$node_version >= 16.0" | bc -l) -eq 0 ]]; then
    echo "❌ 错误: 需要Node.js 16.0或更高版本，当前版本: $node_version"
    exit 1
fi

# 检查MySQL是否运行
if ! command -v mysql &> /dev/null; then
    echo "⚠️  警告: 未检测到MySQL，请确保MySQL已安装并运行"
    echo "   如果使用Docker: docker run -d --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root mysql:8.0"
else
    echo "✅ MySQL已检测到"
fi

# 启动后端
echo "📦 启动后端服务..."
cd backend

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "🔧 创建Python虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "📥 安装Python依赖..."
pip install -r requirements.txt

# 检查环境配置文件
if [ ! -f ".env" ]; then
    echo "⚙️ 创建环境配置文件..."
    cp .env.example .env
    echo "📝 请编辑 backend/.env 文件配置MySQL数据库连接参数"
    echo "   默认配置: mysql+pymysql://monitor:monitor123@localhost:3306/business_monitor"
fi

# 询问是否初始化MySQL数据库
read -p "🗄️  是否需要初始化MySQL数据库？(y/N): " init_db
if [[ $init_db =~ ^[Yy]$ ]]; then
    echo "🔧 初始化MySQL数据库..."
    read -p "请输入MySQL root密码: " -s mysql_password
    echo
    mysql -u root -p$mysql_password < init_mysql.sql
    if [ $? -eq 0 ]; then
        echo "✅ MySQL数据库初始化完成"
    else
        echo "❌ MySQL数据库初始化失败，请检查MySQL连接"
        echo "   手动执行: mysql -u root -p < init_mysql.sql"
    fi
fi

# 启动后端服务
echo "🌐 启动后端API服务..."
python main.py &
BACKEND_PID=$!

# 等待后端启动
sleep 5

# 检查后端是否启动成功
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ 后端服务启动成功"
else
    echo "❌ 后端服务启动失败，请检查日志"
fi

# 启动前端
echo "🎨 启动前端服务..."
cd ../frontend

# 安装依赖
if [ ! -d "node_modules" ]; then
    echo "📥 安装前端依赖..."
    npm install
fi

# 启动前端开发服务器
echo "🌐 启动前端开发服务器..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ 服务启动完成！"
echo ""
echo "📊 前端地址: http://localhost:3000"
echo "🔧 后端API: http://localhost:8000"
echo "📖 API文档: http://localhost:8000/docs"
echo "🗄️  数据库: MySQL (business_monitor)"
echo ""
echo "📝 配置说明:"
echo "   - 编辑 backend/.env 配置数据库连接"
echo "   - 默认数据库: business_monitor"
echo "   - 默认用户: monitor/monitor123"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap 'echo "🛑 正在停止服务..."; kill $BACKEND_PID $FRONTEND_PID; exit' INT
wait