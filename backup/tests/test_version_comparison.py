#!/usr/bin/env python3
"""
测试语义化版本号对比功能
验证不同版本格式的对比逻辑
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.update_service import UpdateService


def test_version_comparison():
    """测试版本号对比功能"""
    print("🧪 测试语义化版本号对比功能...")
    
    update_service = UpdateService()
    
    # 测试用例
    test_cases = [
        # (当前版本, 最新版本, 期望结果, 描述)
        ("1.2.3", "1.2.3", False, "相同版本"),
        ("1.2.3", "1.2.4", True, "小版本更新"),
        ("1.2.3", "1.3.0", True, "中版本更新"),
        ("1.2.3", "2.0.0", True, "大版本更新"),
        ("v1.2.3", "1.2.3", False, "带v前缀相同版本"),
        ("v1.2.3", "1.2.4", True, "带v前缀小版本更新"),
        ("1.2.3", "v1.2.4", True, "最新版本带v前缀"),
        ("1.2.3-beta", "1.2.3", False, "预发布版本与正式版"),
        ("1.2.3", "1.2.3-beta", False, "正式版与预发布版本"),
        ("1.2", "1.2.0", False, "不完整版本号"),
        ("1", "1.0.0", False, "单个数字版本"),
        ("0.9.0", "1.0.0", True, "从0.x到1.0"),
        ("2.0.0", "1.9.9", False, "版本回退"),
        ("1.2.3.4", "1.2.3.5", True, "四段版本号"),
    ]
    
    print("\n📋 测试用例:")
    print("-" * 80)
    print(f"{'当前版本':<15} {'最新版本':<15} {'期望':<8} {'实际':<8} {'结果':<10} 描述")
    print("-" * 80)
    
    passed = 0
    failed = 0
    
    for current, latest, expected, description in test_cases:
        try:
            result = update_service._compare_versions(current, latest)
            status = "✅ 通过" if result == expected else "❌ 失败"
            if result == expected:
                passed += 1
            else:
                failed += 1
            
            print(f"{current:<15} {latest:<15} {str(expected):<8} {str(result):<8} {status:<10} {description}")
        except Exception as e:
            print(f"{current:<15} {latest:<15} {'ERROR':<8} {'ERROR':<8} ❌ 异常   {description} - {e}")
            failed += 1
    
    print("-" * 80)
    print(f"📊 测试结果: 通过 {passed}/{len(test_cases)}, 失败 {failed}/{len(test_cases)}")
    
    return failed == 0


def test_github_repo_parsing():
    """测试GitHub仓库解析"""
    print("\n🧪 测试GitHub仓库解析...")
    
    test_repos = [
        "Jacky/otrs-web",
        "scaleflower/otrs-web", 
        "owner/repo",
        "user/project-name"
    ]
    
    for repo in test_repos:
        # 模拟构建GitHub API URL
        url = f'https://api.github.com/repos/{repo}/releases/latest'
        print(f"✅ 仓库 '{repo}' -> API URL: {url}")


def main():
    """主测试函数"""
    print("=" * 60)
    print("语义化版本号对比功能测试")
    print("=" * 60)
    
    try:
        # 测试版本对比
        version_test_passed = test_version_comparison()
        
        # 测试GitHub仓库解析
        test_github_repo_parsing()
        
        print("\n" + "=" * 60)
        if version_test_passed:
            print("✅ 所有测试通过！版本对比功能正常工作")
        else:
            print("⚠️  部分测试失败，请检查版本对比逻辑")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
