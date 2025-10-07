#!/usr/bin/env python3
"""
检查GitHub配置状态
"""

import os
from dotenv import load_dotenv

def check_github_config():
    """检查GitHub配置状态"""
    print("=" * 60)
    print("GitHub配置状态检查")
    print("=" * 60)
    
    # 加载环境变量
    load_dotenv()
    
    # 检查关键配置
    repo = os.environ.get('APP_UPDATE_REPO')
    token = os.environ.get('APP_UPDATE_GITHUB_TOKEN')
    enabled = os.environ.get('APP_UPDATE_ENABLED', 'true').lower() == 'true'
    
    print(f"📦 仓库配置: {repo}")
    print(f"🔑 GitHub Token: {'已配置' if token else '未配置'}")
    if token:
        print(f"   Token预览: {token[:10]}...{token[-4:] if len(token) > 14 else ''}")
    print(f"🔄 更新启用: {enabled}")
    
    # 提供解决方案
    print("\n" + "=" * 60)
    print("解决方案")
    print("=" * 60)
    
    if not token:
        print("❌ 问题: GitHub Token未配置")
        print("\n💡 解决方案:")
        print("1. 访问 https://github.com/settings/tokens")
        print("2. 点击 'Generate new token' → 'Generate new token (classic)'")
        print("3. 设置Token名称: 'OTRS Web Update'")
        print("4. 权限设置: 只需要 'public_repo' 权限")
        print("5. 点击 'Generate token'")
        print("6. 复制生成的Token")
        print("7. 在 .env 文件中添加:")
        print("   APP_UPDATE_GITHUB_TOKEN=ghp_your_token_here")
        print("\n⚠️  注意: Token只会显示一次，请立即复制保存")
    else:
        print("✅ GitHub Token已配置")
        print("💡 如果仍有速率限制问题，请检查Token是否有效")
        
    print("\n" + "=" * 60)
    print("配置验证完成")
    print("=" * 60)

if __name__ == "__main__":
    check_github_config()
