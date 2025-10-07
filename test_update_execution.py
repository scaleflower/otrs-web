#!/usr/bin/env python3
"""
Test script for update execution functionality
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

def test_update_execution():
    """Test the update execution functionality"""
    print("=" * 60)
    print("OTRS Web 更新执行功能测试")
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
        
        # Test 2: Check if update script exists
        print("\n📁 测试2: 检查更新脚本是否存在")
        from pathlib import Path
        script_path = Path('scripts/update_app.py')
        if script_path.exists():
            print(f"✅ 更新脚本存在: {script_path.absolute()}")
        else:
            print(f"❌ 更新脚本不存在: {script_path.absolute()}")
            return False
        
        # Test 3: Test path resolution
        print("\n🛠️  测试3: 测试路径解析")
        resolved_path = Path.cwd() / script_path
        print(f"✅ 解析后路径: {resolved_path}")
        print(f"✅ 路径存在: {resolved_path.exists()}")
        
        # Test 4: Test update trigger (dry run)
        print("\n🚀 测试4: 测试更新触发（模拟）")
        try:
            # 这里我们只是测试路径解析，不实际执行更新
            target_version = status.get('latest_version', 'release/v1.2.6')
            print(f"✅ 目标版本: {target_version}")
            print(f"✅ 仓库配置: {app.config.get('APP_UPDATE_REPO')}")
            print(f"✅ 分支配置: {app.config.get('APP_UPDATE_BRANCH')}")
            print("✅ 更新配置检查完成")
        except Exception as e:
            print(f"❌ 更新触发测试失败: {e}")
            return False
        
        print("\n" + "=" * 60)
        print("✅ 更新执行功能测试完成")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_update_execution()
    sys.exit(0 if success else 1)
