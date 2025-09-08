# 后端 Dockerfile
# 使用 Python 3.13-slim 作为基础镜像，它体积小，适合生产环境。
FROM python:3.13-slim

# 定义构建参数，用于在构建时传入代理地址。
ARG http_proxy
ARG https_proxy

# 设置环境变量，确保 Python 输出不会被缓冲，且不生成 pyc 文件。
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 如果提供了代理参数，则设置代理环境变量。
ENV HTTP_PROXY=${http_proxy}
ENV HTTPS_PROXY=${https_proxy}

# --- 配置国内镜像源 ---
# 这部分非常关键，它将所有包管理工具的源都切换到国内，可以显著提高构建速度。

# 配置 apt 包管理器使用阿里云镜像源。
RUN rm -f /etc/apt/sources.list.d/* && \
    echo "deb https://mirrors.aliyun.com/debian/ bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian/ bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian/ bookworm-backports main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.aliyun.com/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list

# 安装系统依赖，这里只安装了 curl，并清理了 apt 缓存。
RUN apt-get clean && \
    apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 第一步：复制依赖相关文件（这些文件变化时才重新安装依赖）
COPY pyproject.toml poetry.lock ./

# 配置 pip 使用阿里云镜像源。
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com

RUN pip install --upgrade pip && \
    pip install poetry

# 安装完成提示
RUN echo "安装完成poetry"

RUN poetry config virtualenvs.create false 

RUN echo "开始安装依赖"
RUN poetry install --only=main --no-root --no-interaction --verbose

# 第二步：复制应用程序代码（只有这部分会因代码修改而重新构建）
# 注意：将代码复制放在依赖安装之后，这样代码修改不会影响依赖缓存
COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini ./
COPY tests/ ./tests/
COPY pytest.ini ./

# 添加一个非 root 用户，可以降低安全风险。
# 注意，此步骤放在代码复制之后，以确保正确设置所有文件的权限。
# 使用构建参数对齐宿主机 UID/GID，避免挂载目录权限问题
ARG APP_UID=1000
ARG APP_GID=1000
RUN groupadd -g ${APP_GID} app || true && \
    useradd --create-home --shell /bin/bash -u ${APP_UID} -g ${APP_GID} app && \
    mkdir -p /app/data /app/logs && \
    chown -R ${APP_UID}:${APP_GID} /app && \
    chmod -R 755 /app && \
    chmod -R 777 /app/logs && \
    chmod -R 777 /app/data && \
    touch /app/logs/app.log && \
    chown ${APP_UID}:${APP_GID} /app/logs/app.log && \
    chmod 666 /app/logs/app.log

# 切换到非 root 用户。
USER app

# 暴露端口。
EXPOSE 7000

# 健康检查，用于判断容器是否正常运行。
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7000/health || exit 1

# 启动命令。
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7000"]
