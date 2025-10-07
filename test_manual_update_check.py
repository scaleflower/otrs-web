#!/usr/bin/env python3
"""
Test script for manual update check functionality
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_manual_update_check():
    """Test the manual update check functionality"""
    print("=" * 60)
    print("OTRS Web 手动更新检查功能测试")
    print("=" * 60)
    
    try:
        # Import Flask app and services
        from flask import Flask
        from config import Config
        from models import init_db
        from services import init_services, update_service
        
        # Create Flask application
        app = Flask(__name__)
        app.config.from_object(Config)
        
        # Initialize database and services
        init_db(app)
        init_services(app)
        
        print("🧪 初始化测试环境...")
        
        # Test 1: Check current status
        print("\n📊 测试1: 检查当前更新状态")
        status = update_service.get_status()
        print(f"✅ 当前状态: {status}")
        
        # Test 2: Manual update check
        print("\n🔄 测试2: 手动检查更新")
        result = update_service.check_for_updates()
        print(f"✅ 检查结果: {result}")
        
        if result.get('success'):
            if result.get('status') == 'update_available':
                print(f"🎉 发现新版本: {result.get('latest_version')}")
                print(f"📝 发布说明: {result.get('release_notes', '无')[:100]}...")
                print(f"🔗 发布链接: {result.get('release_url', '无')}")
            elif result.get('status') == 'up_to_date':
                print(f"✅ 当前已是最新版本: {result.get('current_version')}")
            else:
                print(f"ℹ️  状态: {result.get('status')}")
                print(f"📢 消息: {result.get('message')}")
        else:
            print(f"❌ 检查失败: {result.get('error')}")
        
        # Test 3: Verify configuration
        print("\n⚙️  测试3: 验证配置")
        print(f"✅ 仓库配置: {app.config.get('APP_UPDATE_REPO')}")
        print(f"✅ 更新启用: {app.config.get('APP_UPDATE_ENABLED')}")
        print(f"✅ 当前版本: {app.config.get('APP_VERSION')}")
        
        print("\n" + "=" * 60)
        print("✅ 手动更新检查功能测试完成")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_manual_update_check()
    sys.exit(0 if success else 1)
