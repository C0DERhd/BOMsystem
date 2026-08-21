#!/bin/bash

# BOM管理系统启动脚本

echo "=== BOM管理系统启动脚本 ==="

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python 3.8+"
    exit 1
fi

# 检查Node.js环境
if ! command -v node &> /dev/null; then
    echo "错误: 未找到Node.js，请先安装Node.js 16+"
    exit 1
fi

# 进入项目目录
cd "$(dirname "$0")"

echo "1. 设置后端环境..."

# 创建Python虚拟环境
if [ ! -d "backend/venv" ]; then
    echo "创建Python虚拟环境..."
    cd backend
    python3 -m venv venv
    cd ..
fi

# 激活虚拟环境并安装依赖
echo "安装后端依赖..."
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 复制环境配置文件
if [ ! -f ".env" ]; then
    echo "创建环境配置文件..."
    cp .env.example .env
    echo "请编辑 backend/.env 文件配置数据库等信息"
fi

# 初始化数据库
echo "初始化数据库..."
python init_db.py

echo "后端环境设置完成！"
cd ..

echo "2. 设置前端环境..."

# 安装前端依赖
cd frontend
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

echo "前端环境设置完成！"
cd ..

echo "3. 启动服务..."

# 启动后端服务
echo "启动后端服务 (端口 5000)..."
cd backend
source venv/bin/activate
python run.py &
BACKEND_PID=$!
cd ..

# 等待后端启动
sleep 3

# 启动前端服务
echo "启动前端服务 (端口 8000)..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo "=== 服务启动完成 ==="
echo "前端访问地址: http://localhost:8000"
echo "后端API地址: http://localhost:5000"
echo "默认管理员账号: admin / admin123"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 等待用户中断
trap 'echo "正在停止服务..."; kill $BACKEND_PID $FRONTEND_PID; exit' INT
wait