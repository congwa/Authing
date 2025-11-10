# Authing - 统一身份认证平台

<div align="center">

**企业级统一身份认证与权限管理系统**

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.1+-61DAFB.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

## 📖 项目简介

Authing 是一个现代化的统一身份认证与权限管理平台，提供完整的用户认证、授权和管理解决方案。基于 FastAPI + React 构建，支持多种认证方式，适用于企业级应用的身份认证需求。

### ✨ 核心特性

- 🔐 **多种认证方式**
  - 用户名/密码登录
  - 手机号 OTP 验证码登录
  - 邮箱 OTP 验证码登录
  - 二维码扫码登录
  
- 👥 **用户管理**
  - 用户注册与激活
  - 用户信息管理
  - 用户状态控制（激活/冻结/待审核）
  - 扩展用户属性支持
  
- 🎭 **RBAC 权限管理**
  - 基于角色的访问控制
  - 灵活的角色-权限绑定
  - 用户-角色关联管理
  - 权限过期时间控制
  
- 🏢 **多租户支持**
  - 用户池隔离
  - 应用管理
  - 独立配置
  
- 🔒 **安全特性**
  - JWT Token 认证
  - Refresh Token 刷新机制
  - 密码加密存储（bcrypt）
  - API 限流保护
  - 安全头部配置
  - 审计日志记录
  
- 📊 **监控与日志**
  - 结构化日志（structlog）
  - 健康检查端点
  - 审计日志追踪
  - 请求日志记录

## 🏗️ 技术架构

### 后端技术栈

- **框架**: FastAPI 0.115+
- **数据库**: SQLite / PostgreSQL / MySQL（可选）
- **ORM**: SQLModel + SQLAlchemy 2.0
- **认证**: JWT (python-jose)
- **密码加密**: Bcrypt
- **数据验证**: Pydantic 2.0
- **日志**: Structlog + Loguru
- **缓存**: Redis（可选）
- **任务队列**: Celery（可选）
- **数据库迁移**: Alembic

### 前端技术栈

- **框架**: React 19.1
- **构建工具**: Vite 7.1
- **语言**: TypeScript 5.8
- **路由**: React Router 7.8
- **状态管理**: Zustand 5.0
- **数据请求**: TanStack Query 5.87
- **UI 组件**: Radix UI
- **样式**: TailwindCSS 4.1
- **表单**: React Hook Form + Zod
- **图标**: Lucide React

## 📁 项目结构

```
Authing/
├── app/                          # 后端应用
│   ├── api/                      # API 路由
│   │   ├── deps.py              # 依赖注入
│   │   └── v1/                  # API v1 版本
│   │       ├── auth.py          # 认证相关接口
│   │       ├── users.py         # 用户管理接口
│   │       ├── rbac.py          # 权限管理接口
│   │       └── router.py        # 路由汇总
│   ├── core/                    # 核心功能
│   │   ├── middleware.py        # 中间件
│   │   ├── exceptions.py        # 异常定义
│   │   └── security.py          # 安全相关
│   ├── models/                  # 数据模型
│   │   ├── user.py             # 用户模型
│   │   ├── auth.py             # 认证模型
│   │   ├── rbac.py             # 权限模型
│   │   └── base.py             # 基础模型
│   ├── schemas/                 # Pydantic 模式
│   ├── services/                # 业务逻辑
│   ├── db/                      # 数据库配置
│   ├── config.py               # 配置管理
│   └── main.py                 # 应用入口
├── frontend/                    # 前端应用
│   ├── src/
│   │   ├── components/         # React 组件
│   │   ├── pages/              # 页面组件
│   │   │   ├── auth/           # 认证页面
│   │   │   │   ├── login.tsx   # 登录页
│   │   │   │   ├── register.tsx # 注册页
│   │   │   │   ├── otp-login.tsx # OTP登录
│   │   │   │   └── qr-login.tsx  # 扫码登录
│   │   │   └── Dashboard.tsx   # 仪表盘
│   │   ├── services/           # API 服务
│   │   ├── stores/             # 状态管理
│   │   └── types/              # TypeScript 类型
│   └── Dockerfile              # 前端容器配置
├── tests/                       # 测试用例
│   ├── test_auth.py            # 认证测试
│   ├── test_users.py           # 用户测试
│   ├── test_rbac.py            # 权限测试
│   └── conftest.py             # 测试配置
├── alembic/                     # 数据库迁移
├── nginx/                       # Nginx 配置
├── logs/                        # 日志目录
├── data/                        # 数据库文件
├── Dockerfile                   # 后端容器配置
├── docker-compose.yml          # Docker 编排
├── deploy.sh                   # 部署脚本
├── pyproject.toml              # Python 依赖
└── .env.example                # 环境变量模板
```

## 🚀 快速开始

### 环境要求

- Python 3.13+
- Node.js 18+
- pnpm 8+
- Docker 20.10+ (可选)
- Docker Compose 2.0+ (可选)

### 本地开发

#### 1. 克隆项目

```bash
git clone <your-repo-url>
cd Authing
```

#### 2. 后端设置

```bash
# 安装 Poetry
curl -sSL https://install.python-poetry.org | python3 -

# 安装依赖
poetry install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置必要的参数

# 运行数据库迁移
poetry run alembic upgrade head

# 启动后端服务
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 7000
```

#### 3. 前端设置

```bash
cd frontend

# 安装依赖
pnpm install

# 启动开发服务器
pnpm dev
```

#### 4. 访问应用

- 前端应用: http://localhost:5173
- 后端 API: http://localhost:7000
- API 文档: http://localhost:7000/docs

### Docker 部署

详细的 Docker 部署指南请参考 [DEPLOYMENT.md](DEPLOYMENT.md)

#### 快速部署

```bash
# 配置环境变量
cp .env.example .env

# 开发环境部署
./deploy.sh dev

# 生产环境部署
./deploy.sh prod
```

#### 访问地址

- **开发环境**
  - 前端: http://localhost:7001
  - 后端: http://localhost:7000
  - API 文档: http://localhost:7000/docs

- **生产环境**
  - 应用入口: http://localhost:7002
  - HTTPS: https://localhost:7003

## 📚 核心功能说明

### 1. 用户认证

#### 密码登录
```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "user@example.com",
  "password": "password123"
}
```

#### OTP 验证码登录
```bash
# 发送验证码
POST /api/v1/auth/otp/send
{
  "identifier": "13800138000",
  "type": "login"
}

# 验证登录
POST /api/v1/auth/otp/verify
{
  "identifier": "13800138000",
  "code": "123456"
}
```

#### 二维码登录
```bash
# 生成二维码
POST /api/v1/auth/qr/generate

# 扫码确认
POST /api/v1/auth/qr/confirm
{
  "scene_id": "uuid-string"
}

# 轮询状态
GET /api/v1/auth/qr/poll/{scene_id}
```

### 2. 用户管理

- 用户注册
- 用户信息查询与更新
- 用户状态管理
- 用户列表查询（支持分页、筛选）

### 3. RBAC 权限管理

- 角色创建与管理
- 权限定义与分配
- 用户角色绑定
- 权限验证与检查

### 4. 审计日志

所有关键操作都会记录审计日志，包括：
- 用户登录/登出
- 用户信息修改
- 角色权限变更
- 敏感操作记录

## 🔧 配置说明

### 环境变量

关键配置项说明：

| 变量名 | 说明 | 默认值 | 必填 |
|--------|------|--------|------|
| `JWT_SECRET_KEY` | JWT 签名密钥 | - | ✅ |
| `SECRET_KEY` | 应用密钥 | - | ✅ |
| `DATABASE_URL` | 数据库连接 | sqlite:///app/data/authing.db | ❌ |
| `REDIS_URL` | Redis 连接 | - | ❌ |
| `SMTP_HOST` | 邮件服务器 | - | ❌ |
| `CORS_ORIGINS` | CORS 允许源 | http://localhost:3000 | ❌ |

完整配置请参考 `.env.example` 文件。

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
poetry run pytest

# 运行特定测试
poetry run pytest tests/test_auth.py

# 生成覆盖率报告
poetry run pytest --cov=app --cov-report=html
```

### 测试覆盖

项目包含完整的测试用例：
- 认证流程测试
- 用户管理测试
- RBAC 权限测试
- 集成测试

## 📊 API 文档

启动后端服务后，访问以下地址查看 API 文档：

- **Swagger UI**: http://localhost:7000/docs
- **ReDoc**: http://localhost:7000/redoc

## 🔐 安全建议

1. **生产环境必须修改**:
   - `JWT_SECRET_KEY`
   - `SECRET_KEY`
   - 数据库密码

2. **启用 HTTPS**:
   - 配置 SSL 证书
   - 使用反向代理（Nginx）

3. **数据库安全**:
   - 使用强密码
   - 限制访问权限
   - 定期备份

4. **限流配置**:
   - 调整 API 限流参数
   - 防止暴力破解

## 📈 性能优化

1. **使用外部数据库**: 生产环境推荐 PostgreSQL
2. **启用 Redis 缓存**: 提升性能
3. **CDN 加速**: 静态资源使用 CDN
4. **负载均衡**: 多实例部署

## 🛠️ 开发工具

### 代码格式化

```bash
# Python 代码格式化
poetry run black app/
poetry run isort app/

# 代码检查
poetry run flake8 app/
poetry run mypy app/
```

### 数据库迁移

```bash
# 创建迁移
poetry run alembic revision --autogenerate -m "description"

# 执行迁移
poetry run alembic upgrade head

# 回滚迁移
poetry run alembic downgrade -1
```

## 📝 更新日志

### v0.1.0 (当前版本)

- ✅ 基础认证功能（密码、OTP、二维码）
- ✅ 用户管理系统
- ✅ RBAC 权限管理
- ✅ 多租户支持
- ✅ 审计日志
- ✅ Docker 部署支持
- ✅ 完整的测试覆盖

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🆘 支持与帮助

- 📖 [部署文档](DEPLOYMENT.md)
- 🐛 [提交 Issue](https://github.com/your-repo/issues)
- 💬 [讨论区](https://github.com/your-repo/discussions)

## 🙏 致谢

感谢以下开源项目：

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://reactjs.org/)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [TailwindCSS](https://tailwindcss.com/)
- [Radix UI](https://www.radix-ui.com/)

---

<div align="center">
Made with ❤️ by Authing Team
</div>
