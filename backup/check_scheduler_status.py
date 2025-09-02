#!/usr/bin/env python3
"""
检查调度器状态和执行日志
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, StatisticsConfig, StatisticsLog, DailyStatistics

with app.app_context():
    # 检查调度器配置
    config = StatisticsConfig.query.first()
    if config:
        print(f"当前调度时间配置: {config.schedule_time}")
        print(f"调度器启用状态: {config.enabled}")
    else:
        print("未找到调度器配置")
    
    # 检查执行日志
    log_count = StatisticsLog.query.count()
    print(f"\n执行日志总数: {log_count}")
    
    if log_count > 0:
        print("最新的5条执行日志:")
        logs = StatisticsLog.query.order_by(StatisticsLog.execution_time.desc()).limit(5).all()
        for log in logs:
            print(f"  {log.execution_time}: {log.status} - {log.error_message or 'Success'}")
    
    # 检查每日统计数据
    daily_stats_count = DailyStatistics.query.count()
    print(f"\n每日统计数据记录数: {daily_stats_count}")
    
    if daily_stats_count > 0:
        print("最新的5条每日统计数据:")
        stats = DailyStatistics.query.order_by(DailyStatistics.statistic_date.desc()).limit(5).all()
        for stat in stats:
            print(f"  {stat.statistic_date}: 开单{stat.opening_balance}, 新增{stat.new_tickets}, 解决{stat.resolved_tickets}, 结单{stat.closing_balance}")
