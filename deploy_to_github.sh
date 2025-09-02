#!/bin/bash

# ================================================================================
# OTRS Web Application - GitHub部署脚本
# 功能：自动提交所有更改并推送到指定GitHub分支
# 用法：./deploy_to_github.sh <branch_name> [commit_message]
# 示例：./deploy_to_github.sh master "新功能：增量导入和统计修复"
# ================================================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
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

# 检查参数 - branch_name参数现在是可选的，默认为master
BRANCH_NAME=${1:-"master"}
COMMIT_MESSAGE=${2:-"Auto commit: $(date '+%Y-%m-%d %H:%M:%S')"}

# 显示使用帮助（如果用户明确请求）
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    echo "使用方法: $0 [branch_name] [commit_message]"
    print_info "参数说明："
    print_info "  branch_name    : 目标分支名（可选，默认为master）"
    print_info "  commit_message : 提交信息（可选，默认为当前时间戳）"
    print_info ""
    print_info "示例："
    print_info "  $0                           # 提交到master分支，使用默认提交信息"
    print_info "  $0 master                    # 提交到master分支，使用默认提交信息"
    print_info "  $0 develop                   # 提交到develop分支"
    print_info "  $0 master \"新功能实现\"       # 提交到master分支，自定义提交信息"
    print_info "  $0 develop \"修复bug\"        # 提交到develop分支，自定义提交信息"
    exit 0
fi

print_info "开始部署到GitHub..."
print_info "目标分支: $BRANCH_NAME"
print_info "提交信息: $COMMIT_MESSAGE"

# 检查是否在git仓库中
if [ ! -d ".git" ]; then
    print_error "当前目录不是git仓库！"
    exit 1
fi

# 检查git配置
if ! git config user.name > /dev/null || ! git config user.email > /dev/null; then
    print_error "Git用户配置未设置！请先配置："
    echo "git config user.name \"Your Name\""
    echo "git config user.email \"your.email@example.com\""
    exit 1
fi

# 检查远程仓库
if ! git remote get-url origin > /dev/null 2>&1; then
    print_error "未找到远程仓库origin！"
    exit 1
fi

print_info "Git配置检查通过..."

# 检查当前分支
current_branch=$(git branch --show-current)
print_info "当前分支: $current_branch"

# 如果目标分支不是当前分支，询问是否切换
if [ "$current_branch" != "$BRANCH_NAME" ]; then
    print_warning "当前分支 ($current_branch) 与目标分支 ($BRANCH_NAME) 不同"
    
    # 检查目标分支是否存在
    if git show-ref --verify --quiet refs/heads/$BRANCH_NAME; then
        print_info "切换到现有分支: $BRANCH_NAME"
        git checkout $BRANCH_NAME
    else
        print_info "创建并切换到新分支: $BRANCH_NAME"
        git checkout -b $BRANCH_NAME
    fi
    
    if [ $? -ne 0 ]; then
        print_error "分支切换失败！"
        exit 1
    fi
fi

# 拉取最新更改（如果分支存在于远程）
if git ls-remote --heads origin $BRANCH_NAME | grep -q $BRANCH_NAME; then
    print_info "拉取远程分支最新更改..."
    git pull origin $BRANCH_NAME
    if [ $? -ne 0 ]; then
        print_warning "拉取远程更改失败，继续执行..."
    fi
fi

# 显示当前状态
print_info "检查Git状态..."
git status --porcelain

# 添加所有更改，但排除特定文件
print_info "添加文件到暂存区..."

# 添加所有文件，但排除数据库文件和临时文件
git add .
git reset HEAD -- "*.db" "db/*.db" "instance/*.db" "logs/*.log" "__pycache__/" "*.pyc" ".DS_Store" "Thumbs.db"

# 显示即将提交的文件
print_info "即将提交的文件："
git diff --cached --name-status

# 检查是否有文件要提交
if git diff --cached --quiet; then
    print_warning "没有更改需要提交！"
    exit 0
fi

# 提交更改
print_info "提交更改..."
git commit -m "$COMMIT_MESSAGE"

if [ $? -ne 0 ]; then
    print_error "提交失败！"
    exit 1
fi

print_success "提交成功！"

# 推送到远程仓库
print_info "推送到远程仓库 origin/$BRANCH_NAME..."
git push origin $BRANCH_NAME

if [ $? -ne 0 ]; then
    print_error "推送失败！请检查网络连接和权限。"
    exit 1
fi

print_success "推送成功！"

# 显示最新提交信息
print_info "最新提交信息："
git log --oneline -1

# 显示远程仓库URL
remote_url=$(git remote get-url origin)
print_success "部署完成！"
print_info "远程仓库: $remote_url"
print_info "分支: $BRANCH_NAME"
print_info "提交哈希: $(git rev-parse HEAD)"

# 生成部署报告
echo ""
echo "=========================================="
echo "           部署报告"
echo "=========================================="
echo "时间: $(date '+%Y-%m-%d %H:%M:%S')"
echo "分支: $BRANCH_NAME"
echo "提交: $(git log --oneline -1)"
echo "仓库: $remote_url"
echo "操作员: $(git config user.name) <$(git config user.email)>"
echo "=========================================="
