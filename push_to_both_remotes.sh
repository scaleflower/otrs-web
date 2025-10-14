#!/bin/bash

echo "🚀 Pushing to both GitHub and Yunxiao repositories..."

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
        echo "✅ Successfully pushed to GitHub via HTTPS using CLI token"
    else
        echo "❌ Failed to push to GitHub using CLI token"
        exit 1
    fi
else
    # 如果SSH和CLI都不可用，尝试配置好的HTTPS远程
    echo "🔄 SSH and CLI failed, trying configured HTTPS remote..."
    git push github-https $BRANCH
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully pushed to GitHub via HTTPS"
    else
        echo "❌ Failed to push to GitHub via HTTPS"
        echo "💡 Please check your GitHub credentials and access rights"
        exit 1
    fi
fi

echo "🎉 Successfully pushed to both repositories!"