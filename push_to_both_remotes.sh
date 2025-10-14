#!/bin/bash

echo "🚀 Pushing to both GitHub and Yunxiao repositories..."

# 检查是否有未跟踪或修改过的文件
if [[ -n $(git status --porcelain) ]]; then
    echo "📁 Changes detected, adding and committing files..."
    
    # 添加所有更改到暂存区
    git add .
    
    # 提交更改
    git commit -m "Auto-commit: Update files before pushing to remote repositories"
    
    if [ $? -eq 0 ]; then
        echo "✅ Changes successfully committed"
    else
        echo "❌ Failed to commit changes"
        exit 1
    fi
else
    echo "✅ No changes to commit"
fi

# 获取当前分支名
BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "📍 Current branch: $BRANCH"

# 推送到云效 (SSH)
echo "☁️  Pushing to Yunxiao (SSH)..."
git push yunxiao-ssh $BRANCH

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to Yunxiao"
else
    echo "❌ Failed to push to Yunxiao"
    exit 1
fi

# 首先尝试通过SSH推送到GitHub
echo "🐙 Pushing to GitHub (SSH)..."
git push github-ssh $BRANCH

if [ $? -eq 0 ]; then
    echo "✅ Successfully pushed to GitHub via SSH"
elif command -v gh &> /dev/null && gh auth status > /dev/null 2>&1; then
    # 如果SSH失败但GitHub CLI已登录，使用临时token通过HTTPS推送
    echo "🔄 SSH push failed, using GitHub CLI to push via HTTPS..."
    TEMP_TOKEN=$(gh auth token)
    git push "https://x-access-token:$TEMP_TOKEN@github.com/scaleflower/otrs-web.git" $BRANCH
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully pushed to GitHub via HTTPS"
    else
        echo "❌ Failed to push to GitHub"
        exit 1
    fi
else
    echo "❌ Failed to push to GitHub"
    exit 1
fi

echo "🎉 Successfully pushed to both repositories!"