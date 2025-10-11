#!/usr/bin/env python3
"""
OTRS Web 密码修改工具
用于修改.env文件中的每日统计管理员密码
"""

import os
import re
import sys
import getpass
from pathlib import Path

def read_env_file():
    """读取.env文件内容"""
    env_file = Path('.env')
    if not env_file.exists():
        return None, "错误：.env文件不存在！"
    
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            return f.read(), None
    except Exception as e:
        return None, f"读取.env文件失败：{str(e)}"

def write_env_file(content):
    """写入.env文件内容"""
    try:
        with open('.env', 'w', encoding='utf-8') as f:
            f.write(content)
        return True, None
    except Exception as e:
        return False, f"写入.env文件失败：{str(e)}"

def get_current_password():
    """获取当前密码"""
    content, error = read_env_file()
    if error:
        return None, error
    
    # 查找当前密码
    match = re.search(r'^DAILY_STATS_PASSWORD=(.*)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip(), None
    else:
        return None, "未找到DAILY_STATS_PASSWORD配置"

def update_password(new_password):
    """更新密码"""
    content, error = read_env_file()
    if error:
        return False, error
    
    # 替换密码
    new_content = re.sub(
        r'^DAILY_STATS_PASSWORD=.*$',
        f'DAILY_STATS_PASSWORD={new_password}',
        content,
        flags=re.MULTILINE
    )
    
    # 检查是否成功替换
    if new_content == content:
        return False, "未找到DAILY_STATS_PASSWORD配置，无法更新"
    
    # 写入文件
    success, error = write_env_file(new_content)
    return success, error

def validate_password(password):
    """验证密码强度"""
    if len(password) < 6:
        return False, "密码长度至少6位"
    
    if password.isalnum():
        return False, "建议密码包含特殊字符以提高安全性"
    
    return True, None

def main():
    """主函数"""
    print("=" * 60)
    print("🔐 OTRS Web 每日统计密码修改工具")
    print("=" * 60)
    
    # 检查.env文件是否存在
    if not Path('.env').exists():
        print("❌ 错误：.env文件不存在！")
        print("请先运行应用程序创建.env文件，或手动创建。")
        return 1
    
    # 显示当前密码
    current_password, error = get_current_password()
    if error:
        print(f"❌ {error}")
        return 1
    
    print(f"📋 当前密码：{current_password}")
    print()
    
    # 选择操作
    print("请选择操作：")
    print("1. 修改密码")
    print("2. 查看当前密码")
    print("3. 验证密码")
    print("4. 退出")
    
    choice = input("\n请输入选项 (1-4): ").strip()
    
    if choice == '1':
        # 修改密码
        print("\n🔧 修改密码")
        print("-" * 30)
        
        while True:
            new_password = getpass.getpass("请输入新密码: ").strip()
            
            if not new_password:
                print("❌ 密码不能为空，请重新输入。")
                continue
            
            # 验证密码
            is_valid, msg = validate_password(new_password)
            if not is_valid:
                print(f"⚠️  警告：{msg}")
                continue_choice = input("是否继续使用此密码？(y/N): ").strip().lower()
                if continue_choice != 'y':
                    continue
            
            # 确认密码
            confirm_password = getpass.getpass("请确认新密码: ").strip()
            
            if new_password != confirm_password:
                print("❌ 两次输入的密码不一致，请重新输入。")
                continue
            
            break
        
        # 更新密码
        success, error = update_password(new_password)
        if success:
            print("✅ 密码修改成功！")
            print("⚠️  请重启应用程序使新密码生效。")
        else:
            print(f"❌ 密码修改失败：{error}")
            return 1
    
    elif choice == '2':
        # 查看当前密码
        print(f"\n📋 当前密码：{current_password}")
    
    elif choice == '3':
        # 验证密码
        print("\n🔍 验证密码")
        print("-" * 30)
        
        test_password = getpass.getpass("请输入密码: ").strip()
        
        if test_password == current_password:
            print("✅ 密码正确！")
        else:
            print("❌ 密码错误！")
    
    elif choice == '4':
        print("👋 退出程序。")
        return 0
    
    else:
        print("❌ 无效选项，请重新运行程序。")
        return 1
    
    return 0

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n👋 用户取消操作。")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 程序异常：{str(e)}")
        sys.exit(1)
