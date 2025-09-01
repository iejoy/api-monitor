@echo off
chcp 65001 >nul
echo 🚀 启动业务应用监控平台...

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.8或更高版本
    pause
    exit /b 1
)

REM 检查Node.js是否安装
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Node.js，请先安装Node.js 16.0或更高版本
    pause
    exit /b 1
)

REM 检查MySQL是否安装
mysql --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  警告: 未检测到MySQL，请确保MySQL已安装并运行
    echo    下载地址: https://dev.mysql.com/downloads/mysql/
    echo    或使用Docker: docker run -d --name mysql -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root mysql:8.0
) else (
    echo ✅ MySQL已检测到
)

REM 启动后端
echo 📦 启动后端服务...
cd backend

REM 检查虚拟环境
if not exist "venv" (
    echo 🔧 创建Python虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat

REM 安装依赖
echo 📥 安装Python依赖...
pip install -r requirements.txt

REM 检查环境配置文件
if not exist ".env" (
    echo ⚙️ 创建环境配置文件...
    copy .env.example .env
    echo 📝 请编辑 backend\.env 文件配置MySQL数据库连接参数
    echo    默认配置: mysql+pymysql://monitor:monitor123@localhost:3306/business_monitor
)

REM 询问是否初始化MySQL数据库
set /p init_db="🗄️  是否需要初始化MySQL数据库？(y/N): "
if /i "%init_db%"=="y" (
    echo 🔧 初始化MySQL数据库...
    set /p mysql_password="请输入MySQL root密码: "
    mysql -u root -p%mysql_password% < init_mysql.sql
    if %errorlevel% equ 0 (
        echo ✅ MySQL数据库初始化完成
    ) else (
        echo ❌ MySQL数据库初始化失败，请检查MySQL连接
        echo    手动执行: mysql -u root -p ^< init_mysql.sql
    )
)

REM 启动后端服务
echo 🌐 启动后端API服务...
start "Backend API" cmd /k "python main.py"

REM 等待后端启动
timeout /t 5 /nobreak >nul

REM 启动前端
echo 🎨 启动前端服务...
cd ..\frontend

REM 安装依赖
if not exist "node_modules" (
    echo 📥 安装前端依赖...
    npm install
)

REM 启动前端开发服务器
echo 🌐 启动前端开发服务器...
start "Frontend Dev Server" cmd /k "npm run dev"

echo.
echo ✅ 服务启动完成！
echo.
echo 📊 前端地址: http://localhost:3000
echo 🔧 后端API: http://localhost:8000
echo 📖 API文档: http://localhost:8000/docs
echo 🗄️  数据库: MySQL (business_monitor)
echo.
echo 📝 配置说明:
echo    - 编辑 backend\.env 配置数据库连接
echo    - 默认数据库: business_monitor
echo    - 默认用户: monitor/monitor123
echo.
echo 按任意键退出...
pause >nul