#!/bin/bash

# 简化的构建测试脚本
# 用于验证 Docker 配置和项目结构

echo "=== OTRS Web Application Build Test ==="

# 检查必需的文件
echo "1. 检查项目文件..."
required_files=("Dockerfile" "requirements.txt" "app.py" "build-docker.sh")
missing_files=()

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在"
    else
        echo "❌ $file 缺失"
        missing_files+=("$file")
    fi
done

if [ ${#missing_files[@]} -gt 0 ]; then
    echo "错误: 以下文件缺失: ${missing_files[*]}"
    exit 1
fi

# 检查 Dockerfile 语法
echo ""
echo "2. 检查 Dockerfile 语法..."
if grep -q "FROM python" Dockerfile && grep -q "WORKDIR /app" Dockerfile; then
    echo "✅ Dockerfile 基本结构正确"
else
    echo "❌ Dockerfile 结构异常"
    exit 1
fi

# 检查 requirements.txt
echo ""
echo "3. 检查依赖文件..."
if [ -s "requirements.txt" ]; then
    echo "✅ requirements.txt 非空"
    echo "依赖包数量: $(wc -l < requirements.txt)"
else
    echo "❌ requirements.txt 为空"
    exit 1
fi

# 检查 Python 文件存在性
echo ""
echo "4. 检查 Python 文件..."
python_files=("app.py" "app_refactored.py")
for py_file in "${python_files[@]}"; do
    if [ -f "$py_file" ]; then
        echo "✅ $py_file 存在"
    else
        echo "⚠️ $py_file 缺失"
    fi
done
echo "注意: Python 语法检查将在云效构建环境中执行"

# 检查构建脚本权限
echo ""
echo "5. 检查构建脚本..."
if [ -x "build-docker.sh" ]; then
    echo "✅ build-docker.sh 可执行"
else
    echo "⚠️ build-docker.sh 不可执行，正在修复..."
    chmod +x build-docker.sh
    if [ -x "build-docker.sh" ]; then
        echo "✅ build-docker.sh 权限已修复"
    else
        echo "❌ 无法修复 build-docker.sh 权限"
        exit 1
    fi
fi

# 检查云效配置文件
echo ""
echo "6. 检查云效配置..."
if [ -d ".workflow" ] && [ -f ".workflow/build.yml" ]; then
    echo "✅ 云效流水线配置存在"
else
    echo "⚠️ 云效流水线配置缺失"
fi

if [ -f "deploy-k8s.yaml" ]; then
    echo "✅ Kubernetes 部署配置存在"
else
    echo "⚠️ Kubernetes 部署配置缺失"
fi

# 总结
echo ""
echo "=== 构建测试完成 ==="
echo "✅ 所有基本配置检查通过"
echo ""
echo "下一步:"
echo "1. 在云效平台配置环境变量"
echo "2. 创建流水线并连接代码仓库"
echo "3. 配置阿里云容器镜像服务"
echo "4. 配置 Kubernetes 集群"
echo ""
echo "详细配置请参考: 云效部署指南.md"
