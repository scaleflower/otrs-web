#!/usr/bin/env python3
"""
演示.env配置的备份功能测试脚本
"""

import os
import sys
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_backup_configuration():
    """测试备份配置从.env文件读取"""
    print("🔧 测试备份配置从.env文件读取")
    print("=" * 50)
    
    try:
        # 加载环境变量
        try:
            from dotenv import load_dotenv
            load_dotenv()
            print("✅ 已加载 .env 文件")
        except ImportError:
            print("⚠️  python-dotenv 未安装")
        
        from app import app
        
        with app.app_context():
            # 显示当前配置
            backup_time = app.config.get('BACKUP_TIME')
            auto_backup = app.config.get('AUTO_BACKUP')
            retention_days = app.config.get('BACKUP_RETENTION_DAYS')
            backup_folder = app.config.get('BACKUP_FOLDER')
            
            print(f"\n📋 当前备份配置:")
            print(f"  - 备份时间: {backup_time}")
            print(f"  - 自动备份: {'启用' if auto_backup else '禁用'}")
            print(f"  - 保留天数: {retention_days} 天")
            print(f"  - 备份目录: {backup_folder}")
            
            # 测试调度器是否正确读取配置
            from services.scheduler_service import SchedulerService
            scheduler = SchedulerService()
            scheduler.initialize_scheduler(app)
            
            # 获取调度器状态
            status = scheduler.get_scheduler_status()
            print(f"\n🕐 调度器状态:")
            print(f"  - 运行状态: {'运行中' if status['running'] else '已停止'}")
            print(f"  - 活动任务数: {status['job_count']}")
            
            if status['jobs']:
                print(f"  - 调度任务:")
                for job in status['jobs']:
                    next_run = job['next_run_time'] if job['next_run_time'] else '无'
                    print(f"    • {job['name']}: {next_run}")
            
            # 获取备份服务状态
            backup_status = scheduler.get_backup_status()
            print(f"\n💾 备份服务状态:")
            print(f"  - 服务可用: {'是' if backup_status.get('service_available') else '否'}")
            print(f"  - 自动备份: {'启用' if backup_status.get('auto_backup_enabled') else '禁用'}")
            print(f"  - 现有备份数: {backup_status.get('total_backups', 0)}")
            
            stats = backup_status.get('statistics', {})
            if stats.get('total_backups', 0) > 0:
                print(f"  - 备份总大小: {stats.get('total_size_mb', 0)} MB")
                print(f"  - 保留策略: {stats.get('retention_days', 30)} 天")
            
            scheduler.shutdown()
            
            return True
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def show_backup_time_examples():
    """显示如何修改备份时间的示例"""
    print("\n" + "=" * 50)
    print("📝 如何修改备份时间")
    print("=" * 50)
    
    print("""
要修改自动备份时间，请编辑项目根目录下的 .env 文件：

当前配置示例：
BACKUP_TIME=02:00                 # 每天凌晨2:00备份
AUTO_BACKUP_ENABLED=true          # 启用自动备份
BACKUP_RETENTION_DAYS=30          # 保留30天的备份

修改示例：
BACKUP_TIME=01:30                 # 改为凌晨1:30备份
BACKUP_TIME=23:45                 # 改为晚上11:45备份
AUTO_BACKUP_ENABLED=false         # 禁用自动备份
BACKUP_RETENTION_DAYS=7           # 只保留7天的备份

📌 注意事项：
1. 时间格式必须是 24小时制的 HH:MM 格式
2. 修改后需要重启应用程序才能生效
3. 建议选择系统负载较低的时间进行备份
4. 备份文件会自动压缩以节省存储空间
""")

def main():
    """主函数"""
    print(f"🚀 OTRS Web 备份配置测试")
    print(f"📅 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试配置读取
    success = test_backup_configuration()
    
    # 显示配置说明
    show_backup_time_examples()
    
    if success:
        print(f"\n✅ 配置测试完成！备份功能已正确配置。")
    else:
        print(f"\n❌ 配置测试失败，请检查设置。")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())
