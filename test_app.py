#!/usr/bin/env python3
"""
简单的测试脚本来验证Flask应用的基本功能
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_flask_app():
    """测试Flask应用的基本功能"""
    try:
        # 导入Flask应用
        from app import app
        
        # 测试应用是否能够正常创建
        with app.test_client() as client:
            # 测试主页访问
            response = client.get('/')
            assert response.status_code == 200
            print("✓ 主页访问正常")
            
            # 测试静态文件访问
            response = client.get('/static/css/style.css')
            assert response.status_code == 200
            print("✓ CSS文件访问正常")
            
            response = client.get('/static/js/script.js')
            assert response.status_code == 200
            print("✓ JS文件访问正常")
            
            # 测试上传接口（无文件）
            response = client.post('/upload')
            assert response.status_code == 400
            print("✓ 上传接口无文件验证正常")
            
            print("\n✅ 基本功能测试通过！")
            print("应用已准备好接收Excel文件上传")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("开始测试OTRS工单分析Web应用...")
    print("=" * 50)
    
    if test_flask_app():
        print("\n🎉 应用测试成功！")
        print("请访问 http://localhost:5000 使用Web界面")
    else:
        print("\n💥 应用测试失败，请检查错误信息")
        sys.exit(1)
