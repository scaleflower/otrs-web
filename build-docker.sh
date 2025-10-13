#!/bin/bash

# OTRS Web Application Docker Build Script
# 用于云效 CI/CD 流水线

set -e

# 配置变量
IMAGE_NAME="otrs-web-app"
REGISTRY="registry.cn-hangzhou.aliyuncs.com"
NAMESPACE="${ACR_NAMESPACE:-default}"
TAG="${BUILD_TAG:-latest}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查必需的环境变量
check_env() {
    local missing_vars=()
    
    if [[ -z "$ACR_USERNAME" ]]; then
        missing_vars+=("ACR_USERNAME")
    fi
    
    if [[ -z "$ACR_PASSWORD" ]]; then
        missing_vars+=("ACR_PASSWORD")
    fi
    
    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables: ${missing_vars[*]}"
        exit 1
    fi
}

# 登录到阿里云容器镜像服务
login_acr() {
    log_info "Logging in to Alibaba Cloud Container Registry..."
    docker login -u "$ACR_USERNAME" -p "$ACR_PASSWORD" "$REGISTRY"
}

# 构建 Docker 镜像
build_image() {
    local full_image_name="$REGISTRY/$NAMESPACE/$IMAGE_NAME:$TAG"
    
    log_info "Building Docker image: $full_image_name"
    
    # 构建镜像
    docker build -t "$full_image_name" .
    
    # 测试镜像
    log_info "Testing the built image..."
    docker run --rm -d -p 5000:5000 --name test-container "$full_image_name"
    sleep 10
    
    # 检查应用是否正常启动
    if curl -f http://localhost:5000/ > /dev/null 2>&1; then
        log_info "Application is running successfully"
        docker stop test-container
    else
        log_error "Application failed to start"
        docker logs test-container
        docker stop test-container
        exit 1
    fi
}

# 推送镜像到仓库
push_image() {
    local full_image_name="$REGISTRY/$NAMESPACE/$IMAGE_NAME:$TAG"
    
    log_info "Pushing image to registry: $full_image_name"
    docker push "$full_image_name"
    
    # 标记为 latest（如果是主分支）
    if [[ "$TAG" != "latest" && "$CI_COMMIT_REF_NAME" == "master" ]]; then
        log_info "Tagging as latest..."
        docker tag "$full_image_name" "$REGISTRY/$NAMESPACE/$IMAGE_NAME:latest"
        docker push "$REGISTRY/$NAMESPACE/$IMAGE_NAME:latest"
    fi
}

# 清理
cleanup() {
    log_info "Cleaning up..."
    docker system prune -f
}

# 主函数
main() {
    log_info "Starting Docker build process for OTRS Web Application"
    
    check_env
    login_acr
    build_image
    push_image
    cleanup
    
    log_info "Docker build and push completed successfully!"
    
    # 输出镜像信息
    local full_image_name="$REGISTRY/$NAMESPACE/$IMAGE_NAME:$TAG"
    echo "=========================================="
    echo "Image: $full_image_name"
    echo "Registry: $REGISTRY"
    echo "Namespace: $NAMESPACE"
    echo "Tag: $TAG"
    echo "=========================================="
}

# 执行主函数
main "$@"
