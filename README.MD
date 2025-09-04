

# **项目名称：统一身份认证与管理平台 (FastAPI + React 版)**


统一身份认证与管理平台 (FastAPI + React 前后端分离版) - 完整技术计划书

1.0 项目概述
本项目旨在构建一个功能完备、可复用的统一身份认证与管理平台（IAM）。项目将严格遵循前后端分离的架构模式，后端是基于FastAPI框架构建的单体API服务，前端是基于React框架构建的单页应用(SPA)。

平台将支持多租户（用户池）和多应用接入，为所有客户端应用提供集中、安全、可扩展的用户身份认证和权限管理服务。

2.0 架构与设计原则
2.1 系统架构：前后端分离
前端 (Frontend): 一个独立的React项目，负责所有UI渲染和用户交互。它通过HTTP/S调用后端API进行数据交换，运行在用户的浏览器中。

后端 (Backend): 一个独立的FastAPI项目，作为一个无头(Headless)服务运行在服务器上。它负责所有业务逻辑、数据持久化和安全校验，并对外暴露一套标准化的RESTful API。

通信 (Communication): 前后端之间通过API进行通信，使用JWT（JSON Web Tokens）进行无状态的用户认证。

2.2 设计原则
**安全第一**: 所有设计均以保障用户数据和系统安全为首要前提。

**前后端分离**: 严格遵守分离原则，确保前后端可以独立开发、测试、部署和扩展。

**模块化设计**: 后端服务内部按功能逻辑划分模块，保持高内聚、低耦合。

**标准化**: 遵循OAuth 2.0, JWT, RESTful API等业界标准。

**可观测性**: 实施全面的日志记录、监控和追踪机制。

**高可用性**: 设计容错机制，确保系统稳定运行。

### 2.3 安全设计原则

**多层防护**: 
- 网络层：HTTPS强制、CORS配置、API网关
- 应用层：输入验证、输出编码、SQL注入防护
- 数据层：数据加密、访问控制、备份策略

**最小权限原则**: 
- 用户默认拥有最小必要权限
- 权限临时授予机制
- 定期权限审查和回收

**零信任架构**: 
- 所有请求都需要验证和授权
- 内部服务间通信也需要认证
- 持续验证用户身份和设备状态

**数据保护**: 
- 敏感数据加密存储
- 传输过程加密
- 数据脱敏和匿名化
- 符合GDPR/个人信息保护法

3.0 核心概念
用户池 (User Pool): 一个独立的用户目录，是数据隔离的最高单位。

应用 (Application): 需要接入本平台的任何实体，例如 WebApp A, WebApp B 等。

用户 (User): 存储在某个用户池中的身份实体。

角色 (Role): 一组权限的集合，属于特定的用户池。

权限 (Permission): 定义了一个具体的操作权限，属于特定的用户池。

4.0 技术选型
后端框架: FastAPI

ORM: SQLAlchemy 2.0 (推荐使用 SQLModel 简化模型定义)

数据库: MySQL 8.0+

数据库迁移: Alembic

认证/JWT: python-jose (用于JWT操作), passlib[bcrypt] (用于密码哈希)

后台管理: SQLAdmin (集成到FastAPI中)

前端框架: React

前端路由: @tanstack/react-router

部署: Docker

5.0 数据库设计 (MySQL)
数据库包含以下核心表以支持多租户和多应用架构：

### 5.1 核心业务表

**user_pools** (用户池表)
```sql
CREATE TABLE user_pools (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL COMMENT '用户池名称',
    description TEXT COMMENT '用户池描述',
    settings JSON COMMENT '用户池配置信息',
    status ENUM('active', 'disabled') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_status (status)
);
```

**applications** (应用表)
```sql
CREATE TABLE applications (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_pool_id BIGINT NOT NULL,
    app_name VARCHAR(100) NOT NULL COMMENT '应用名称',
    app_id VARCHAR(64) NOT NULL UNIQUE COMMENT '应用ID',
    app_secret VARCHAR(128) NOT NULL COMMENT '应用密钥',
    callback_urls JSON COMMENT '回调地址列表',
    logout_urls JSON COMMENT '登出地址列表',
    allowed_origins JSON COMMENT '允许的来源域名',
    token_lifetime INT DEFAULT 3600 COMMENT 'Token有效期(秒)',
    refresh_token_lifetime INT DEFAULT 2592000 COMMENT 'Refresh Token有效期(秒)',
    status ENUM('active', 'disabled') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_pool_id) REFERENCES user_pools(id) ON DELETE CASCADE,
    INDEX idx_user_pool_id (user_pool_id),
    INDEX idx_app_id (app_id),
    INDEX idx_status (status)
);
```

**users** (用户表)
```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_pool_id BIGINT NOT NULL,
    username VARCHAR(100) UNIQUE COMMENT '用户名',
    email VARCHAR(255) UNIQUE COMMENT '邮箱',
    phone VARCHAR(20) UNIQUE COMMENT '手机号',
    nickname VARCHAR(100) COMMENT '昵称',
    avatar_url VARCHAR(500) COMMENT '头像URL',
    profile_data JSON COMMENT '扩展用户信息',
    email_verified BOOLEAN DEFAULT FALSE COMMENT '邮箱是否已验证',
    phone_verified BOOLEAN DEFAULT FALSE COMMENT '手机号是否已验证',
    status ENUM('active', 'blocked', 'pending') DEFAULT 'pending',
    last_login_at TIMESTAMP NULL COMMENT '最后登录时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_pool_id) REFERENCES user_pools(id) ON DELETE CASCADE,
    INDEX idx_user_pool_id (user_pool_id),
    INDEX idx_username (username),
    INDEX idx_email (email),
    INDEX idx_phone (phone),
    INDEX idx_status (status)
);
```

**credentials** (凭证表)
```sql
CREATE TABLE credentials (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    type ENUM('password', 'social', 'mfa') NOT NULL,
    identifier VARCHAR(255) NOT NULL COMMENT '标识符(邮箱/手机/社交账号ID)',
    credential TEXT NOT NULL COMMENT '凭证(哈希密码/OAuth token等)',
    salt VARCHAR(32) COMMENT '密码盐值',
    provider VARCHAR(50) COMMENT '第三方提供商(google/wechat等)',
    expires_at TIMESTAMP NULL COMMENT '凭证过期时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY uk_user_type_identifier (user_id, type, identifier),
    INDEX idx_user_id (user_id),
    INDEX idx_type (type),
    INDEX idx_identifier (identifier)
);
```

### 5.2 权限管理表

**roles** (角色表)
```sql
CREATE TABLE roles (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_pool_id BIGINT NOT NULL,
    role_name VARCHAR(100) NOT NULL,
    role_code VARCHAR(100) NOT NULL COMMENT '角色代码',
    description TEXT COMMENT '角色描述',
    is_system BOOLEAN DEFAULT FALSE COMMENT '是否系统角色',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_pool_id) REFERENCES user_pools(id) ON DELETE CASCADE,
    UNIQUE KEY uk_pool_role_code (user_pool_id, role_code),
    INDEX idx_user_pool_id (user_pool_id),
    INDEX idx_role_code (role_code)
);
```

**permissions** (权限表)
```sql
CREATE TABLE permissions (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_pool_id BIGINT NOT NULL,
    permission_name VARCHAR(100) NOT NULL,
    permission_code VARCHAR(100) NOT NULL COMMENT '权限代码',
    resource VARCHAR(100) NOT NULL COMMENT '资源标识',
    action VARCHAR(50) NOT NULL COMMENT '操作类型(read/write/delete等)',
    description TEXT COMMENT '权限描述',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_pool_id) REFERENCES user_pools(id) ON DELETE CASCADE,
    UNIQUE KEY uk_pool_permission_code (user_pool_id, permission_code),
    INDEX idx_user_pool_id (user_pool_id),
    INDEX idx_resource_action (resource, action)
);
```

**user_roles** (用户角色关联表)
```sql
CREATE TABLE user_roles (
    user_id BIGINT NOT NULL,
    role_id BIGINT NOT NULL,
    granted_by BIGINT COMMENT '授权人ID',
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NULL COMMENT '权限过期时间',
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (granted_by) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_role_id (role_id),
    INDEX idx_expires_at (expires_at)
);
```

**role_permissions** (角色权限关联表)
```sql
CREATE TABLE role_permissions (
    role_id BIGINT NOT NULL,
    permission_id BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);
```

### 5.3 认证相关表

**otp_codes** (一次性验证码表)
```sql
CREATE TABLE otp_codes (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    identifier VARCHAR(255) NOT NULL COMMENT '手机号或邮箱',
    code_hash VARCHAR(128) NOT NULL COMMENT '验证码哈希值',
    type ENUM('login', 'register', 'reset_password', 'verify') NOT NULL,
    attempts INT DEFAULT 0 COMMENT '尝试次数',
    max_attempts INT DEFAULT 5 COMMENT '最大尝试次数',
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    ip_address VARCHAR(45) COMMENT '请求IP',
    user_agent TEXT COMMENT '用户代理',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_identifier_type (identifier, type),
    INDEX idx_expires_at (expires_at),
    INDEX idx_used (used)
);
```

**qr_login_sessions** (扫码登录会话表)
```sql
CREATE TABLE qr_login_sessions (
    scene_id VARCHAR(36) PRIMARY KEY COMMENT 'UUID',
    user_pool_id BIGINT NOT NULL,
    app_id VARCHAR(64) NOT NULL COMMENT '发起登录的应用ID',
    status ENUM('pending', 'scanned', 'confirmed', 'expired', 'cancelled') DEFAULT 'pending',
    user_id BIGINT NULL COMMENT '确认登录的用户ID',
    expires_at TIMESTAMP NOT NULL,
    scanned_at TIMESTAMP NULL COMMENT '扫码时间',
    confirmed_at TIMESTAMP NULL COMMENT '确认时间',
    ip_address VARCHAR(45) COMMENT 'Web端IP',
    user_agent TEXT COMMENT 'Web端用户代理',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_pool_id) REFERENCES user_pools(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_status (status),
    INDEX idx_expires_at (expires_at),
    INDEX idx_user_id (user_id)
);
```

### 5.4 审计和日志表

**audit_logs** (审计日志表)
```sql
CREATE TABLE audit_logs (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_pool_id BIGINT,
    user_id BIGINT,
    action VARCHAR(100) NOT NULL COMMENT '操作类型',
    resource VARCHAR(100) COMMENT '操作资源',
    resource_id VARCHAR(100) COMMENT '资源ID',
    details JSON COMMENT '操作详情',
    ip_address VARCHAR(45),
    user_agent TEXT,
    success BOOLEAN NOT NULL,
    error_message TEXT COMMENT '错误信息',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_pool_id) REFERENCES user_pools(id) ON DELETE SET NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_user_pool_id (user_pool_id),
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at),
    INDEX idx_success (success)
);
```



### 5.5 技术选型详细说明

#### 5.5.1 后端技术栈
* **核心框架**: FastAPI 0.104+
  - 原生异步支持，高性能
  - 自动API文档生成 (OpenAPI/Swagger)
  - 基于Pydantic的数据验证
  - 优秀的类型提示支持

* **数据库相关**: 
  - **ORM**: SQLAlchemy 2.0 + SQLModel
  - **数据库**: MySQL 8.0+
  - **连接池**: aiomysql + asyncio
  - **迁移工具**: Alembic

* **认证安全**:
  - **JWT处理**: python-jose[cryptography]
  - **密码哈希**: passlib[bcrypt]
  - **加密**: cryptography库
  - **限流**: slowapi (基于redis)

* **其他组件**:
  - **配置管理**: pydantic-settings
  - **日志**: structlog + loguru
  - **监控**: prometheus-client
  - **任务队列**: celery + redis
  - **缓存**: redis-py[hiredis]
  - **HTTP客户端**: httpx

#### 5.5.2 前端技术栈
* **核心框架**: React 18+ (TypeScript)
* **路由**: @tanstack/react-router v1
* **状态管理**: @tanstack/react-query + zustand
* **UI组件**: Ant Design 5.x 或 Shadcn/ui
* **构建工具**: Vite
* **代码规范**: ESLint + Prettier + Husky

#### 5.5.3 DevOps技术栈
* **容器化**: Docker + Docker Compose
* **CI/CD**: GitHub Actions 或 GitLab CI
* **监控**: Prometheus + Grafana
* **日志**: ELK Stack (Elasticsearch + Logstash + Kibana)
* **部署**: Kubernetes (可选) 或 直接容器部署

### 6.0 项目结构设计

#### 6.1 后端项目结构
```
server/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI应用入口
│   ├── config.py              # 配置管理
│   ├── core/                  # 核心模块
│   │   ├── __init__.py
│   │   ├── dependencies.py    # 依赖注入
│   │   ├── security.py        # 安全相关
│   │   ├── exceptions.py      # 自定义异常
│   │   └── middleware.py      # 中间件
│   ├── models/                # 数据模型
│   │   ├── __init__.py
│   │   ├── base.py           # 基础模型类
│   │   ├── user.py           # 用户相关模型
│   │   ├── auth.py           # 认证相关模型
│   │   └── rbac.py           # 权限相关模型
│   ├── schemas/               # Pydantic模式
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── auth.py
│   │   └── common.py
│   ├── api/                   # API路由
│   │   ├── __init__.py
│   │   ├── deps.py           # API依赖
│   │   ├── v1/               # API版本1
│   │   │   ├── __init__.py
│   │   │   ├── auth.py       # 认证相关API
│   │   │   ├── users.py      # 用户管理API
│   │   │   ├── pools.py      # 用户池API
│   │   │   └── admin.py      # 管理员API
│   ├── services/              # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   └── rbac_service.py
│   ├── utils/                 # 工具函数
│   │   ├── __init__.py
│   │   ├── crypto.py         # 加密工具
│   │   ├── validators.py     # 验证器
│   │   └── helpers.py        # 助手函数
│   └── db/                    # 数据库相关
│       ├── __init__.py
│       ├── database.py       # 数据库连接
│       ├── base.py          # 基础类
│       └── session.py       # 会话管理
├── alembic/                   # 数据库迁移
├── tests/                     # 测试文件
│   ├── __init__.py
│   ├── conftest.py           # pytest配置
│   ├── test_auth.py
│   ├── test_users.py
│   └── fixtures/             # 测试固件
├── scripts/                   # 脚本文件
├── docker/                    # Docker配置
├── requirements.txt          # 依赖声明
├── pyproject.toml           # 项目配置
├── Dockerfile
└── docker-compose.yml
```

#### 6.2 前端项目结构
```
frontend/
├── public/
├── src/
│   ├── main.tsx              # 应用入口
│   ├── App.tsx               # 根组件
│   ├── components/           # 可复用组件
│   │   ├── ui/              # 基础UI组件
│   │   ├── forms/           # 表单组件
│   │   └── layout/          # 布局组件
│   ├── pages/                # 页面组件
│   │   ├── auth/            # 认证相关页面
│   │   ├── dashboard/       # 仪表板
│   │   └── admin/           # 管理页面
│   ├── hooks/                # 自定义Hook
│   ├── services/             # API服务
│   │   ├── api.ts           # API客户端
│   │   ├── auth.ts          # 认证服务
│   │   └── users.ts         # 用户服务
│   ├── stores/               # 状态管理
│   │   ├── auth.ts
│   │   └── user.ts
│   ├── utils/                # 工具函数
│   │   ├── constants.ts
│   │   ├── helpers.ts
│   │   └── validators.ts
│   ├── types/                # TypeScript类型定义
│   └── styles/               # 样式文件
├── tests/                    # 测试文件
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js        # 如果使用Tailwind
└── Dockerfile
```

### 7.0 API设计规范

#### 7.1 RESTful API设计原则
```
# 基本URL结构
/api/v1/{resource}/{id?}/{action?}

# 示例
GET    /api/v1/users              # 获取用户列表
GET    /api/v1/users/{id}         # 获取特定用户
POST   /api/v1/users              # 创建用户
PUT    /api/v1/users/{id}         # 更新用户(完整)
PATCH  /api/v1/users/{id}         # 更新用户(部分)
DELETE /api/v1/users/{id}         # 删除用户

# 认证相关
POST   /api/v1/auth/login         # 登录
POST   /api/v1/auth/refresh       # 刷新Token
POST   /api/v1/auth/logout        # 登出
POST   /api/v1/auth/otp/send      # 发送验证码
POST   /api/v1/auth/otp/verify    # 验证码登录
```

#### 7.2 统一响应格式
```json
{
  "code": 200,
  "message": "success",
  "data": {
    // 具体数据
  },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### 7.3 错误处理规范
```python
# 自定义异常类
class AuthError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=401, detail=detail)

class ValidationError(HTTPException):
    def __init__(self, detail: str):
        super().__init__(status_code=422, detail=detail)

# 错误响应格式
{
  "code": 400,
  "message": "Validation Error",
  "errors": [
    {
      "field": "email",
      "message": "邮箱格式不正确"
    }
  ],
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 8.0 测试策略

#### 8.1 测试分层架构
```
├── 单元测试 (Unit Tests)
│   ├── models/          # 数据模型测试
│   ├── services/        # 业务逻辑测试
│   └── utils/           # 工具函数测试
├── 集成测试 (Integration Tests)
│   ├── api/             # API接口测试
│   ├── database/        # 数据库集成测试
│   └── external/        # 外部服务集成测试
└── 端到端测试 (E2E Tests)
    ├── authentication/   # 认证流程测试
    ├── user_management/  # 用户管理流程测试
    └── permissions/      # 权限管理流程测试
```

#### 8.2 测试工具选择
**后端测试**:
- **单元测试**: pytest + pytest-asyncio
- **API测试**: httpx + FastAPI TestClient
- **数据库测试**: pytest-postgresql (测试数据库)
- **Mock**: pytest-mock
- **覆盖率**: pytest-cov

**前端测试**:
- **单元测试**: Vitest + Testing Library
- **组件测试**: React Testing Library
- **E2E测试**: Playwright
- **可视化测试**: Chromatic (可选)

#### 8.3 持续集成/持续部署 (CI/CD)

**GitHub Actions 工作流示例**:
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: test
        options: >-
          --health-cmd="mysqladmin ping"
          --health-interval=10s
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: |
          pytest --cov=app tests/
      - name: Upload coverage
        uses: codecov/codecov-action@v3

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm ci
      - name: Run tests
        run: npm test
      - name: E2E tests
        run: npm run test:e2e

  deploy:
    needs: [backend-test, frontend-test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Deploy to production
        run: |
          # 部署脚本
```

### 9.0 功能模块技术实现

#### 9.1 认证中间件实现
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from jose import JWTError, jwt

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    return user
```

#### 9.2 验证码登录实现
```python
import secrets
import hashlib
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def send_otp_code(identifier: str, type: str):
    # 生成6位验证码
    code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
    
    # 哈希验证码
    code_hash = pwd_context.hash(code)
    
    # 存储到数据库
    otp_record = OTPCode(
        identifier=identifier,
        code_hash=code_hash,
        type=type,
        expires_at=datetime.utcnow() + timedelta(minutes=5)
    )
    await save_otp_code(otp_record)
    
    # 发送验证码 (短信/邮件)
    await send_notification(identifier, code)

async def verify_otp_code(identifier: str, code: str):
    # 查找未使用的验证码
    otp = await get_valid_otp(identifier)
    if not otp:
        raise HTTPException(400, "验证码不存在或已过期")
    
    # 验证码验证
    if not pwd_context.verify(code, otp.code_hash):
        # 增加尝试次数
        await increment_otp_attempts(otp.id)
        raise HTTPException(400, "验证码错误")
    
    # 标记为已使用
    await mark_otp_used(otp.id)
    return True
```

#### 9.3 扫码登录实现
```python
import uuid
from enum import Enum

class QRStatus(str, Enum):
    PENDING = "pending"
    SCANNED = "scanned"
    CONFIRMED = "confirmed"
    EXPIRED = "expired"

async def create_qr_session(user_pool_id: int, app_id: str):
    scene_id = str(uuid.uuid4())
    session = QRLoginSession(
        scene_id=scene_id,
        user_pool_id=user_pool_id,
        app_id=app_id,
        status=QRStatus.PENDING,
        expires_at=datetime.utcnow() + timedelta(minutes=2)
    )
    await save_qr_session(session)
    return scene_id

async def confirm_qr_login(scene_id: str, user_id: int):
    session = await get_qr_session(scene_id)
    if not session or session.status != QRStatus.PENDING:
        raise HTTPException(400, "二维码会话无效")
    
    await update_qr_session_status(
        scene_id, 
        QRStatus.CONFIRMED, 
        user_id,
        datetime.utcnow()
    )
```

### 10.0 性能优化与监控

#### 10.1 数据库性能优化
**索引优化**:
```sql
-- 复合索引优化常见查询
CREATE INDEX idx_users_pool_status ON users(user_pool_id, status);
CREATE INDEX idx_credentials_user_type ON credentials(user_id, type);
CREATE INDEX idx_audit_logs_time_action ON audit_logs(created_at, action);

-- 分区表(可选，用于大量数据)
CREATE TABLE audit_logs_2024 PARTITION OF audit_logs 
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

**查询优化**:
- 使用连接池 (连接数：10-20)
- 启用查询缓存
- 读写分离 (主从复制)
- 慢查询日志监控

#### 10.2 应用层性能优化
**缓存策略**:
```python
# Redis缓存配置
CACHE_CONFIG = {
    "user_profile": 3600,      # 用户信息1小时
    "user_permissions": 1800,   # 权限信息30分钟
    "app_config": 7200,        # 应用配置2小时
    "jwt_blacklist": 86400,    # JWT黑名单24小时
}

# 缓存装饰器示例
@cache(key="user:{user_id}", ttl=3600)
async def get_user_with_permissions(user_id: int):
    # 复杂的用户权限查询
    pass
```

**异步处理**:
```python
# 使用Celery处理耗时任务
@celery_app.task
def send_email_verification(user_id: int, email: str):
    # 发送邮件验证
    pass

@celery_app.task
def batch_import_users(file_path: str, user_pool_id: int):
    # 批量导入用户
    pass
```

#### 10.3 监控与可观测性
**应用指标监控**:
```python
from prometheus_client import Counter, Histogram, Gauge

# 业务指标
login_attempts = Counter('auth_login_attempts_total', 'Login attempts', ['status', 'method'])
api_request_duration = Histogram('api_request_duration_seconds', 'API request duration')
active_users = Gauge('active_users_total', 'Number of active users')

# 中间件记录指标
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    api_request_duration.observe(duration)
    return response
```

**日志规范**:
```python
import structlog

logger = structlog.get_logger()

# 结构化日志
logger.info(
    "用户登录",
    user_id=user.id,
    user_pool_id=user.user_pool_id,
    login_method="password",
    ip_address=request.client.host,
    user_agent=request.headers.get("user-agent"),
    duration_ms=duration * 1000
)
```

**告警配置**:
```yaml
# Prometheus 告警规则
groups:
  - name: auth_service
    rules:
      - alert: HighErrorRate
        expr: rate(api_request_total{status!~"2.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "API错误率过高"
      
      - alert: SlowQueries
        expr: mysql_slow_queries > 10
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "数据库慢查询过多"
```

### 11.0 安全加固

#### 11.1 API安全
```python
# 请求限流
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")  # 登录限流
async def login(request: Request, ...):
    pass

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

#### 11.2 数据加密
```python
# 敏感字段加密
from cryptography.fernet import Fernet

class EncryptedField:
    def __init__(self, key: str):
        self.cipher_suite = Fernet(key.encode())
    
    def encrypt(self, data: str) -> str:
        return self.cipher_suite.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
```

### 12.0 项目规划与里程碑

#### 第一阶段：基础架构建设 (4-5周)
**目标**: 搭建完整的开发和部署环境
- **第1-2周**: 
  - 初始化FastAPI项目结构
  - 配置数据库、ORM、迁移工具
  - 设置Docker开发环境
  - 建立CI/CD流水线
- **第3-4周**:
  - 实现核心数据模型和数据库迁移
  - 开发基础认证模块(用户名密码登录)
  - 集成SQLAdmin后台管理
  - 编写核心API和单元测试
- **第5周**:
  - 前端React项目初始化
  - 实现基础UI组件和路由配置
  - 完成登录页面和受保护路由

#### 第二阶段：核心功能开发 (4-5周)
**目标**: 实现完整的认证和权限管理
- **第6-7周**:
  - 多租户用户池管理API
  - RBAC权限系统实现
  - JWT认证中间件优化
  - API接口完善和测试
- **第8-9周**:
  - 验证码登录功能(SMS/Email)
  - 扫码登录功能实现
  - 前端认证流程集成
  - 用户管理界面开发
- **第10周**:
  - 权限管理前端界面
  - 管理员控制台开发
  - 集成测试和安全测试

#### 第三阶段：高级特性和优化 (3-4周)
**目标**: 系统优化和生产就绪
- **第11-12周**:
  - 性能优化(缓存、数据库优化)
  - 监控和日志系统集成
  - 安全加固和漏洞修复
  - 压力测试和性能调优
- **第13-14周**:
  - 生产环境部署配置
  - 文档完善和API文档
  - 用户手册和部署指南
  - 最终测试和验收

#### 第四阶段：生产部署和维护 (2周)
**目标**: 上线运行和持续维护
- **第15周**:
  - 生产环境部署
  - 数据迁移和系统切换
  - 监控告警配置
  - 运维手册编写
- **第16周**:
  - 系统稳定性观察
  - 性能监控和优化
  - 用户反馈收集
  - 后续版本规划

### 13.0 技术风险与对策

#### 13.1 主要技术风险
1. **数据库性能瓶颈**: 大量并发认证请求可能导致数据库压力
   - 对策: 读写分离、连接池优化、缓存机制

2. **JWT安全风险**: Token泄露或伪造风险
   - 对策: 短期Token + Refresh Token机制、Token黑名单

3. **扫码登录实时性**: 数据库轮询可能影响用户体验
   - 对策: 优化轮询间隔、后续考虑WebSocket升级

4. **多租户数据隔离**: 数据泄露风险
   - 对策: 严格的数据访问控制、行级安全策略

#### 13.2 部署和运维风险
1. **单点故障**: 应用或数据库故障导致服务不可用
   - 对策: 高可用部署、主从备份、容器编排

2. **数据备份**: 用户数据丢失风险
   - 对策: 自动备份策略、异地备份、定期恢复测试

### 14.0 交付清单

#### 14.1 代码交付
- [ ] 后端源代码 (FastAPI项目)
- [ ] 前端源代码 (React项目)  
- [ ] 数据库迁移脚本
- [ ] Docker配置文件
- [ ] CI/CD配置文件

#### 14.2 文档交付
- [ ] API接口文档 (自动生成)
- [ ] 数据库设计文档
- [ ] 系统架构文档
- [ ] 部署运维手册
- [ ] 用户使用手册

#### 14.3 测试交付
- [ ] 单元测试报告 (90%+覆盖率)
- [ ] 集成测试报告
- [ ] 安全测试报告
- [ ] 性能测试报告
- [ ] 用户验收测试报告

这份经过全面修正的技术计划书提供了完整的实施路径，涵盖了从技术选型到部署上线的全流程，特别注重了安全性、可维护性和可扩展性。