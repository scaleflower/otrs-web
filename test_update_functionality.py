#!/usr/bin/env python3
"""
测试自动更新功能的脚本
用于验证GitHub release检测和更新流程
"""

import os
import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.update_service import UpdateService
from flask import Flask
from config import Config
from models import init_db


def test_update_service():
    """测试更新服务的基本功能"""
    print("🧪 开始测试自动更新功能...")
    
    # 创建测试Flask应用
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # 初始化数据库
    init_db(app)
    
    # 初始化更新服务
    update_service = UpdateService()
    update_service.initialize(app)
    
    print("✅ 更新服务初始化成功")
    
    # 测试状态获取
    with app.app_context():
        status = update_service.get_status()
        print(f"📊 当前状态: {status}")
        
        # 测试GitHub release检测
        print("🔄 测试GitHub release检测...")
        try:
            result = update_service.check_for_updates(force=True)
            if result:
                print(f"✅ GitHub检测成功: {result.get('status', 'unknown')}")
                print(f"   当前版本: {result.get('current_version', 'unknown')}")
                print(f"   最新版本: {result.get('latest_version', 'unknown')}")
            else:
                print("⚠️  GitHub检测返回空结果")
        except Exception as e:
            print(f"❌ GitHub检测失败: {e}")
        
        # 测试更新状态检查
        is_running = update_service.is_update_running()
        print(f"🔄 更新是否运行中: {is_running}")
    
    print("✅ 自动更新功能测试完成")


def test_update_script():
    """测试更新脚本"""
    print("\n🧪 测试更新脚本...")
    
    update_script = project_root / 'scripts' / 'update_app.py'
    if not update_script.exists():
        print("❌ 更新脚本不存在")
        return
    
    print(f"✅ 更新脚本存在: {update_script}")
    
    # 测试脚本参数解析
    import subprocess
    try:
        result = subprocess.run([
            sys.executable, str(update_script), '--help'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print("✅ 更新脚本参数解析正常")
        else:
            print(f"❌ 更新脚本参数解析失败: {result.stderr}")
    except Exception as e:
        print(f"❌ 更新脚本测试失败: {e}")


def main():
    """主测试函数"""
    print("=" * 50)
    print("OTRS Web 自动更新功能测试")
    print("=" * 50)
    
    try:
        test_update_service()
        test_update_script()
        
        print("\n" + "=" * 50)
        print("✅ 所有测试完成")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
