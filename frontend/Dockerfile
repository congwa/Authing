# 前端 Dockerfile
# 使用多阶段构建优化镜像大小

# 构建阶段
FROM node:20-alpine AS builder

# 定义构建参数
ARG http_proxy
ARG https_proxy

# 设置代理环境变量（如果提供了构建参数）
ENV HTTP_PROXY=${http_proxy}
ENV HTTPS_PROXY=${https_proxy}

# 设置工作目录
WORKDIR /app

# 配置 npm 使用国内镜像源
RUN npm config set registry https://registry.npmmirror.com/

# 第一步：复制依赖相关文件（这些文件变化时才重新安装依赖）
COPY package*.json ./
COPY pnpm-lock.yaml ./

# 安装 pnpm 并配置使用国内镜像源
RUN npm install -g pnpm && \
    pnpm config set registry https://registry.npmmirror.com/

# 安装依赖
RUN pnpm install --frozen-lockfile

# 第二步：复制源代码（只有这部分会因代码修改而重新构建）
COPY src/ ./src/
COPY public/ ./public/
COPY index.html ./
COPY vite.config.ts ./
COPY tsconfig.json ./
COPY tsconfig.app.json ./
COPY eslint.config.js ./
COPY components.json ./
COPY tailwind.config.js ./
COPY postcss.config.js ./

# 设置环境变量用于生产构建
ENV NODE_ENV=production
ENV VITE_API_BASE_URL=http://localhost:7000

# 构建应用
RUN pnpm run build

# 生产阶段
FROM nginx:alpine AS production

# 安装 curl 用于健康检查
RUN apk --no-cache add curl

# 复制构建产物到 nginx 目录
COPY --from=builder /app/dist /usr/share/nginx/html

# 复制 nginx 配置
COPY nginx.conf /etc/nginx/nginx.conf

# 创建健康检查页面
RUN echo '<!DOCTYPE html><html><body><h1>OK</h1></body></html>' > /usr/share/nginx/html/health

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# 启动 nginx
CMD ["nginx", "-g", "daemon off;"]
