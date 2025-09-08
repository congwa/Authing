# Authing 项目 Docker 部署指南

本文档介绍如何使用 Docker 部署 Authing 统一身份认证平台，支持开发和生产环境。

## 📋 系统要求

- Docker 20.10+
- Docker Compose 2.0+
- 2GB+ 可用内存
- 5GB+ 可用磁盘空间

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone <your-repo-url>
cd Authing
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
vim .env
```

**重要**: 请务必修改以下安全相关配置：
- `JWT_SECRET_KEY`: JWT 密钥
- `SECRET_KEY`: 应用密钥
- 邮件和短信服务配置（如需要）

### 3. 部署服务

```bash
# 开发环境部署
./deploy.sh dev

# 生产环境部署（包含 Nginx 反向代理）
./deploy.sh prod
```

## 🔧 部署脚本使用

### 基本命令

```bash
# 部署开发环境
./deploy.sh dev

# 部署生产环境
./deploy.sh prod

# 停止所有服务
./deploy.sh stop

# 查看服务状态
./deploy.sh status

# 查看日志
./deploy.sh logs

# 查看特定服务日志
./deploy.sh logs backend
./deploy.sh logs frontend

# 执行数据库迁移
./deploy.sh migrate

# 创建管理员用户
./deploy.sh admin

# 清理所有资源（谨慎使用）
./deploy.sh clean
```

## 🌐 访问地址

### 开发环境
- **前端应用**: http://localhost:7001
- **后端 API**: http://localhost:7000
- **API 文档**: http://localhost:7000/docs
- **健康检查**: http://localhost:7000/health

### 生产环境
- **应用入口 (Nginx)**: http://localhost:7002
- **HTTPS (如配置)**: https://localhost:7003
- **前端直接访问**: http://localhost:7001
- **后端 API**: http://localhost:7000

## 📁 目录结构

```
Authing/
├── Dockerfile                 # 后端 Docker 配置
├── docker-compose.yml        # Docker Compose 配置
├── deploy.sh                 # 部署脚本
├── .env.example              # 环境变量模板
├── .env.production           # 生产环境配置
├── frontend/
│   ├── Dockerfile            # 前端 Docker 配置
│   └── nginx.conf            # 前端 Nginx 配置
├── nginx/
│   ├── nginx.conf            # 生产环境 Nginx 配置
│   ├── ssl/                  # SSL 证书目录
│   └── logs/                 # Nginx 日志
├── logs/                     # 应用日志
└── data/                     # 数据库文件
```

## ⚙️ 配置说明

### 环境变量配置

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `APP_NAME` | 应用名称 | Authing | 否 |
| `APP_ENV` | 运行环境 | production | 否 |
| `HOST` | 监听地址 | 0.0.0.0 | 否 |
| `PORT` | 监听端口 | 7000 | 否 |
| `DATABASE_URL` | 数据库连接 | sqlite:///app/data/authing.db | 否 |
| `JWT_SECRET_KEY` | JWT 密钥 | - | **是** |
| `SECRET_KEY` | 应用密钥 | - | **是** |
| `CORS_ORIGINS` | CORS 允许源 | http://localhost:7001 | 否 |

### 端口分配

| 服务 | 内部端口 | 外部端口 | 说明 |
|------|----------|----------|------|
| 后端 API | 7000 | 7000 | FastAPI 应用 |
| 前端应用 | 80 | 7001 | React + Nginx |
| 生产 Nginx | 80 | 7002 | HTTP 反向代理 |
| 生产 Nginx | 443 | 7003 | HTTPS 反向代理 |

## 🔒 SSL 证书配置

如需启用 HTTPS，请按以下步骤配置：

### 1. 准备证书文件

```bash
# 将证书文件放到 nginx/ssl 目录
cp your-cert.pem nginx/ssl/cert.pem
cp your-key.pem nginx/ssl/key.pem
```

### 2. 修改 Nginx 配置

编辑 `nginx/nginx.conf`，取消 HTTPS 服务器配置的注释，并修改域名。

### 3. 重新部署

```bash
./deploy.sh stop
./deploy.sh prod
```

## 📊 监控和日志

### 查看实时日志

```bash
# 查看所有服务日志
./deploy.sh logs

# 查看特定服务日志
./deploy.sh logs backend
./deploy.sh logs frontend
./deploy.sh logs nginx
```

### 日志文件位置

- **应用日志**: `logs/app.log`
- **Nginx 日志**: `nginx/logs/`
- **容器日志**: 使用 `docker-compose logs` 查看

### 健康检查

所有服务都配置了健康检查：

```bash
# 检查后端健康状态
curl http://localhost:7000/health

# 检查前端健康状态
curl http://localhost:7001/health

# 检查 Nginx 健康状态
curl http://localhost:7002/health
```

## 🔄 数据备份和恢复

### 备份数据

```bash
# 备份数据库
cp data/authing.db backup/authing_$(date +%Y%m%d_%H%M%S).db

# 备份日志
tar -czf backup/logs_$(date +%Y%m%d_%H%M%S).tar.gz logs/
```

### 恢复数据

```bash
# 停止服务
./deploy.sh stop

# 恢复数据库
cp backup/authing_20240308_120000.db data/authing.db

# 启动服务
./deploy.sh prod
```

## 🔧 故障排除

### 常见问题

#### 1. 容器启动失败

```bash
# 查看容器状态
docker-compose ps

# 查看详细错误
docker-compose logs [service-name]
```

#### 2. 权限问题

```bash
# 修复目录权限
sudo chown -R $(id -u):$(id -g) logs data
chmod 755 logs data
```

#### 3. 端口被占用

```bash
# 检查端口使用情况
netstat -tulpn | grep :7000
netstat -tulpn | grep :7001
netstat -tulpn | grep :7002

# 修改 docker-compose.yml 中的端口映射
```

#### 4. 内存不足

```bash
# 查看资源使用情况
docker stats

# 调整容器资源限制（编辑 docker-compose.yml）
```

### 重置环境

如果遇到严重问题，可以重置整个环境：

```bash
# ⚠️ 警告：这将删除所有数据
./deploy.sh clean

# 重新部署
./deploy.sh prod
```

## 📝 开发调试

### 开发环境配置

开发环境使用热重载和详细日志：

```bash
# 启动开发环境
./deploy.sh dev

# 进入后端容器调试
docker-compose exec backend bash

# 进入前端容器调试
docker-compose exec frontend sh
```

### 数据库管理

```bash
# 执行数据库迁移
./deploy.sh migrate

# 创建新迁移
docker-compose exec backend alembic revision --autogenerate -m "description"

# 查看迁移历史
docker-compose exec backend alembic history
```

## 🚀 生产环境优化

### 性能优化建议

1. **使用外部数据库**: 生产环境建议使用 PostgreSQL 或 MySQL
2. **Redis 缓存**: 启用 Redis 提升性能
3. **CDN**: 静态资源使用 CDN 加速
4. **负载均衡**: 多实例部署时使用负载均衡器
5. **监控告警**: 集成 Prometheus + Grafana

### 安全加固

1. **防火墙**: 只开放必要端口
2. **SSL/TLS**: 启用 HTTPS
3. **更新密钥**: 定期更新 JWT 密钥
4. **日志审计**: 启用访问日志和安全审计

## 📚 相关链接

- [项目文档](README.md)
- [API 文档](http://localhost:7000/docs)
- [前端组件文档](frontend/README.md)
- [数据库设计](docs/database.md)

## 🆘 支持

如遇到问题，请：

1. 查看本文档的故障排除部分
2. 检查日志文件
3. 提交 Issue 到项目仓库
4. 联系技术支持团队
