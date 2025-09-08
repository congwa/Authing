#!/bin/bash

# Authing 项目 Docker 部署脚本
# 使用方法: ./deploy.sh [dev|prod|stop|logs|clean]

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的信息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查 Docker 和 Docker Compose
check_requirements() {
    print_info "检查系统环境..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker 未安装，请先安装 Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose 未安装，请先安装 Docker Compose"
        exit 1
    fi
    
    print_success "系统环境检查通过"
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    mkdir -p logs data nginx/logs nginx/ssl
    
    # 设置正确的权限
    chmod 755 logs data
    chmod 777 logs data  # 确保容器可以写入
    
    print_success "目录创建完成"
}

# 初始化环境变量文件
init_env() {
    if [ ! -f .env ]; then
        print_info "初始化环境变量文件..."
        cp .env.production .env
        print_warning "请编辑 .env 文件，修改密钥和其他配置"
        print_info "重要: 请修改 JWT_SECRET_KEY 和 SECRET_KEY 为随机值"
    else
        print_info "环境变量文件已存在"
    fi
}

# 构建和启动开发环境
deploy_dev() {
    print_info "部署开发环境..."
    
    check_requirements
    create_directories
    init_env
    
    print_info "构建并启动开发环境..."
    docker-compose -f docker-compose.yml up --build -d
    
    print_success "开发环境部署完成!"
    print_info "访问地址:"
    print_info "  - 前端: http://localhost:7001"
    print_info "  - 后端API: http://localhost:7000"
    print_info "  - 后端健康检查: http://localhost:7000/health"
}

# 构建和启动生产环境
deploy_prod() {
    print_info "部署生产环境..."
    
    check_requirements
    create_directories
    init_env
    
    # 使用生产环境配置
    print_info "构建并启动生产环境 (包含 Nginx 反向代理)..."
    docker-compose --profile production -f docker-compose.yml up --build -d
    
    print_success "生产环境部署完成!"
    print_info "访问地址:"
    print_info "  - 应用入口 (Nginx): http://localhost:7002"
    print_info "  - 前端直接访问: http://localhost:7001"  
    print_info "  - 后端API: http://localhost:7000"
}

# 停止服务
stop_services() {
    print_info "停止所有服务..."
    docker-compose --profile production down
    print_success "服务已停止"
}

# 查看日志
show_logs() {
    if [ -n "$2" ]; then
        print_info "查看 $2 服务日志..."
        docker-compose logs -f "$2"
    else
        print_info "查看所有服务日志..."
        docker-compose logs -f
    fi
}

# 清理资源
clean() {
    print_warning "这将删除所有容器、镜像和数据卷，确定要继续吗? (y/N)"
    read -r response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            print_info "清理Docker资源..."
            docker-compose --profile production down -v --rmi all
            docker system prune -f
            print_success "清理完成"
            ;;
        *)
            print_info "清理已取消"
            ;;
    esac
}

# 数据库迁移
migrate() {
    print_info "执行数据库迁移..."
    docker-compose exec backend alembic upgrade head
    print_success "数据库迁移完成"
}

# 创建管理员用户
create_admin() {
    print_info "创建管理员用户..."
    docker-compose exec backend python -c "
from app.core.database import get_session
from app.models.auth import User
from app.core.security import get_password_hash
import asyncio

async def create_admin():
    async with get_session() as session:
        admin = User(
            username='admin',
            email='admin@example.com',
            hashed_password=get_password_hash('admin123'),
            nickname='管理员',
            status='active',
            user_pool_id=1
        )
        session.add(admin)
        await session.commit()
        print('管理员用户创建成功: admin/admin123')

asyncio.run(create_admin())
"
}

# 显示状态
show_status() {
    print_info "服务状态:"
    docker-compose ps
}

# 显示帮助信息
show_help() {
    echo "Authing Docker 部署脚本"
    echo ""
    echo "使用方法:"
    echo "  ./deploy.sh dev              - 部署开发环境"
    echo "  ./deploy.sh prod             - 部署生产环境 (包含Nginx)"
    echo "  ./deploy.sh stop             - 停止所有服务"
    echo "  ./deploy.sh logs [service]   - 查看日志 (可指定服务名)"
    echo "  ./deploy.sh clean            - 清理所有资源"
    echo "  ./deploy.sh migrate          - 执行数据库迁移"
    echo "  ./deploy.sh admin            - 创建管理员用户"
    echo "  ./deploy.sh status           - 显示服务状态"
    echo "  ./deploy.sh help             - 显示帮助信息"
    echo ""
    echo "端口分配:"
    echo "  7000 - 后端API"
    echo "  7001 - 前端应用"
    echo "  7002 - Nginx HTTP (生产环境)"
    echo "  7003 - Nginx HTTPS (生产环境)"
}

# 主逻辑
case "${1:-help}" in
    dev)
        deploy_dev
        ;;
    prod)
        deploy_prod
        ;;
    stop)
        stop_services
        ;;
    logs)
        show_logs "$@"
        ;;
    clean)
        clean
        ;;
    migrate)
        migrate
        ;;
    admin)
        create_admin
        ;;
    status)
        show_status
        ;;
    help|*)
        show_help
        ;;
esac
