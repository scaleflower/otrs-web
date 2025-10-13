# macOS Docker Desktop 安装指南

## 方法一：手动下载安装（推荐）

### 1. 下载 Docker Desktop
访问 Docker 官网下载页面：
```
https://www.docker.com/products/docker-desktop/
```

选择 "Mac with Apple chip" 或 "Mac with Intel chip" 下载。

### 2. 安装步骤
1. 打开下载的 `.dmg` 文件
2. 将 Docker 图标拖到 Applications 文件夹
3. 打开 Applications 文件夹，双击 Docker 应用
4. 按照提示完成安装

### 3. 首次启动配置
- 系统会提示需要权限，点击 "OK"
- 输入 macOS 登录密码授权
- 等待 Docker 启动完成

## 方法二：使用 Homebrew（如果网络正常）

```bash
# 跳过自动更新（如果网络有问题）
export HOMEBREW_NO_AUTO_UPDATE=1

# 安装 Docker Desktop
brew install --cask docker

# 或者使用国内镜像源
brew install --cask docker --force
```

## 验证安装

安装完成后，在终端中运行：

```bash
# 检查 Docker 版本
docker --version

# 检查 Docker Compose 版本  
docker-compose --version

# 运行测试容器
docker run hello-world
```

## 配置优化

### 1. 资源分配
打开 Docker Desktop → Preferences → Resources：
- **CPU**: 建议 4-8 核
- **Memory**: 建议 4-8 GB
- **Disk**: 建议 64 GB

### 2. 镜像加速（国内用户）
在 Docker Desktop → Preferences → Docker Engine 中添加：

```json
{
  "registry-mirrors": [
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://registry.docker-cn.com"
  ]
}
```

## 本地开发配置

我已经为您创建了完整的本地开发配置：

### 1. 构建和运行应用

```bash
# 构建 Docker 镜像
docker build -t otrs-web-app .

# 使用 docker-compose 运行
docker-compose up -d

# 或者直接运行
docker run -p 5000:5000 -v $(pwd)/uploads:/app/uploads -v $(pwd)/logs:/app/logs otrs-web-app
```

### 2. 开发环境命令

```bash
# 查看运行状态
docker-compose ps

# 查看日志
docker-compose logs -f

