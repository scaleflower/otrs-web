# 使用官方Python运行时作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV PORT=15001

# 更新包索引并安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# 配置pip国内镜像源
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip config set global.trusted-host pypi.tuna.tsinghua.edu.cn

# 复制requirements文件并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 创建应用所需的所有目录
RUN mkdir -p db logs uploads database_backups

# 复制项目文件（使用.dockerignore排除不需要的文件）
COPY . .

# 暴露端口
EXPOSE 15001

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:15001/ || exit 1

# 设置启动命令（使用gunicorn生产环境）
CMD ["gunicorn", "--bind", "0.0.0.0:15001", "--workers", "4", "app:app"]