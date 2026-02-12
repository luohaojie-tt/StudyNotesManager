#!/bin/bash
# Study Notes Manager - Docker 快速启动脚本
# 使用方法：bash start-docker.sh

echo "======================================"
echo "  Study Notes Manager - Docker 启动脚本"
echo "======================================"
echo ""

# 检查 Docker 是否安装
if ! command -v docker >/dev/null 2>&1; then
    echo "❌ Docker 未安装，请先安装 Docker Desktop"
    echo "   下载地址: https://www.docker.com/products/docker-desktop"
    exit 1
fi

echo "✅ Docker 已安装"
echo ""

# 检查端口占用
echo "🔍 检查端口占用..."
check_port() {
    if netstat -an | grep -q ":$1 " >/dev/null; then
        echo "  ❌ 端口 $1 已被占用"
        return 1
    else
        echo "  ✅ 端口 $1 可用"
        return 0
    fi
}

# 检查必需端口
check_port 5432  # PostgreSQL
check_port 6379  # Redis
check_port 8000  # Backend API
check_port 3000  # Frontend

echo ""
echo "======================================"
echo ""

# 询问用户启动方式
echo "请选择启动方式："
echo "1) 完整启动 - 包含数据库（首次使用推荐）"
echo "2) 后端启动 - 仅启动后端和前端"
echo "3) 数据库启动 - 仅启动数据库"
echo ""
read -p "输入选择 (1-3): " choice

case $choice in
    1)
        echo "🚀 启动完整服务..."
        docker-compose up -d postgres redis backend frontend
        ;;
    2)
        echo "🔧 启动后端服务..."
        docker-compose up -d backend frontend
        ;;
    3)
        echo "🗄️ 启动数据库服务..."
        docker-compose up -d postgres redis
        ;;
    *)
        echo "❌ 无效选择，启动完整服务..."
        docker-compose up -d postgres redis backend frontend
        ;;
esac

echo ""
echo "======================================"
echo "✅ 服务启动完成！"
echo ""
echo "📋 访问地址："
echo "   后端 API: http://localhost:8000"
echo "   前端页面: http://localhost:3000"
echo "   数据库:   localhost:5432"
echo "   Redis:    localhost:6379"
echo ""
echo "💡 常用命令："
echo "   查看日志: docker-compose logs -f backend"
echo "   停止服务: docker-compose down"
echo "   重启服务: docker-compose restart backend"
echo ""
echo "⚠️  首次启动前请确保："
echo "   1. 已配置 backend/.env 文件（或使用默认值）"
echo "   2. Docker Desktop 正在运行"
echo ""
echo "======================================"