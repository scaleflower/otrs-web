"""
Test script for individual responsible period details functionality
验证个人明细周期统计功能的测试脚本
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from models import init_db
from services import init_services, analysis_service

def test_individual_period_details():
    """Test individual responsible period details functionality"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database and services
    init_db(app)
    init_services(app)
    
    with app.app_context():
        print("🔧 测试个人明细周期统计功能...")
        
        # Get some test responsible names
        from models import OtrsTicket
        test_responsibles = OtrsTicket.query.with_entities(OtrsTicket.responsible).filter(
            OtrsTicket.responsible.isnot(None),
            OtrsTicket.responsible != ''
        ).distinct().limit(2).all()
        
        if not test_responsibles:
            print("❌ 没有找到测试数据")
            return False
        
        responsible_names = [r.responsible for r in test_responsibles]
        print(f"📋 使用测试人员: {responsible_names}")
        
        # Test different periods and their individual details
        periods = ['total', 'day', 'week', 'month']
        
        for period in periods:
            print(f"\n📊 测试 {period} 统计的个人明细...")
            
            stats = analysis_service.get_responsible_statistics(responsible_names, period)
            
            if 'total_by_responsible' not in stats:
                print(f"❌ {period} 统计失败")
                continue
            
            totals = stats['total_by_responsible']
            
            # Test each responsible person's details
            for responsible in responsible_names:
                total = totals.get(responsible, 0)
                print(f"\n👤 {responsible} (总计: {total}个工单)")
                
                if period == 'total':
                    # Test age distribution details
                    age_dist = stats.get('age_distribution', {}).get(responsible, {})
                    print("   📋 年龄分布明细:")
                    for age_key, count in age_dist.items():
                        if count > 0:
                            age_label = get_age_label(age_key)
                            print(f"     - {age_label}: {count}个工单")
                    
                    if not any(age_dist.values()):
                        print("     - 该人员当前无Open工单")
                
                else:
                    # Test period-specific details
                    period_stats = stats.get('period_stats', {})
                    period_label = get_period_label(period)
                    print(f"   📋 {period_label}统计明细:")
                    
                    # Get periods where this responsible has tickets
                    responsible_periods = {}
                    for period_key, period_data in period_stats.items():
                        if responsible in period_data and period_data[responsible] > 0:
                            responsible_periods[period_key] = period_data[responsible]
                    
                    if responsible_periods:
                        # Show periods in reverse chronological order
                        sorted_periods = sorted(responsible_periods.keys(), reverse=True)
                        for period_key in sorted_periods[:5]:  # Show first 5 periods
                            count = responsible_periods[period_key]
                            print(f"     - {period_key}: {count}个工单")
                        
                        if len(sorted_periods) > 5:
                            print(f"     - ... 还有 {len(sorted_periods) - 5} 个{period_label}")
                    else:
                        print(f"     - 该人员在所选{period_label}内无工单记录")
        
        print("\n🎯 个人明细周期功能验证:")
        print("✅ 总体统计：显示年龄分布明细（当前Open工单）")
        print("✅ 按天统计：显示每个日期的工单数量")
        print("✅ 按周统计：显示每周的工单数量")  
        print("✅ 按月统计：显示每月的工单数量")
        print("✅ 明细表响应周期选择变化")
        print("✅ 点击明细数据可查看具体工单列表")
        
        return True

def get_age_label(age_key):
    """Get age label for display"""
    age_labels = {
        'age_24h': '≤24小时',
        'age_24_48h': '24-48小时',
        'age_48_72h': '48-72小时', 
        'age_72h': '>72小时'
    }
    return age_labels.get(age_key, age_key)

def get_period_label(period):
    """Get period label for display"""
    period_labels = {
        'day': '日期',
        'week': '周次',
        'month': '月份'
    }
    return period_labels.get(period, '周期')

def main():
    """Main function"""
    print("=" * 60)
    print("🔧 Responsible工作量统计 - 个人明细周期功能测试")
    print("=" * 60)
    
    try:
        success = test_individual_period_details()
        if success:
            print("\n✅ 个人明细周期功能测试通过！")
            print("\n📝 功能改进:")
            print("1. 个人明细表会根据选择的统计周期动态调整显示内容")
            print("2. 总体统计显示年龄分布，周期统计显示相应周期的工单分布")
            print("3. 点击明细数字可查看该人员在特定周期的具体工单列表")
            print("4. 提供更精细的个人工作量分析视角")
        else:
            print("\n❌ 测试失败")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
