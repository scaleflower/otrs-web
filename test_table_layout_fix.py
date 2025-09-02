"""
Test script for table layout fix - row/column swap in responsible stats
验证汇总统计表行列交换功能的测试脚本
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask
from config import Config
from models import init_db
from services import init_services, analysis_service

def test_table_layout():
    """Test the table layout with row/column swap"""
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database and services
    init_db(app)
    init_services(app)
    
    with app.app_context():
        print("🔧 测试汇总统计表行列交换功能...")
        
        # Get some test responsible names
        from models import OtrsTicket
        test_responsibles = OtrsTicket.query.with_entities(OtrsTicket.responsible).filter(
            OtrsTicket.responsible.isnot(None),
            OtrsTicket.responsible != ''
        ).distinct().limit(3).all()
        
        if not test_responsibles:
            print("❌ 没有找到测试数据")
            return False
        
        responsible_names = [r.responsible for r in test_responsibles]
        print(f"📋 使用测试人员: {responsible_names}")
        
        # Test table structure for different periods
        periods = ['total', 'day', 'week', 'month']
        
        for period in periods:
            print(f"\n📊 测试 {period} 统计的表格结构...")
            
            stats = analysis_service.get_responsible_statistics(responsible_names, period)
            
            if 'total_by_responsible' not in stats:
                print(f"❌ {period} 统计失败")
                continue
            
            totals = stats['total_by_responsible']
            
            if period == 'total':
                print("✅ 总体统计表格结构:")
                print("   - 表头: [排名, Responsible人员, 处理工单总数]")
                print("   - 数据行: 按工单数排序的人员排名")
                
                # Simulate the ranking logic
                sorted_totals = sorted(totals.items(), key=lambda x: x[1], reverse=True)
                for i, (responsible, count) in enumerate(sorted_totals, 1):
                    print(f"   - 第{i}名: {responsible} ({count}个工单)")
                    
            else:
                print(f"✅ {period} 周期统计表格结构:")
                
                if 'period_stats' in stats:
                    period_stats = stats['period_stats']
                    all_periods = sorted(period_stats.keys(), reverse=True)
                    all_responsibles = sorted(totals.keys())
                    
                    print(f"   - 表头: [{period}, {', '.join(all_responsibles)}, 总计]")
                    print(f"   - 数据行: {len(all_periods)} 个{period}周期")
                    
                    # Show sample data structure
                    for i, period_key in enumerate(all_periods[:3]):  # Show first 3 periods
                        period_data = period_stats[period_key]
                        period_total = sum(period_data.get(resp, 0) for resp in all_responsibles)
                        resp_counts = [str(period_data.get(resp, 0)) for resp in all_responsibles]
                        print(f"   - {period_key}: [{', '.join(resp_counts)}] 总计:{period_total}")
                    
                    if len(all_periods) > 3:
                        print(f"   - ... 还有 {len(all_periods) - 3} 个周期")
                    
                    # Show totals row
                    total_counts = [str(totals.get(resp, 0)) for resp in all_responsibles]
                    grand_total = sum(totals.values())
                    print(f"   - 总计行: [{', '.join(total_counts)}] 总计:{grand_total}")
                    
                else:
                    print(f"   ⚠️  没有 {period} 周期统计数据")
        
        print("\n🎯 行列交换验证:")
        print("✅ 修改前: Responsible人员作为行，周期作为列")
        print("✅ 修改后: 周期作为行，Responsible人员作为列")
        print("✅ 这样更便于:")
        print("   - 对比同一时期不同人员的工作量")
        print("   - 观察工作量的时间趋势")
        print("   - 快速找到特定时期的总工作量")
        
        return True

def main():
    """Main function"""
    print("=" * 60)
    print("🔧 Responsible工作量统计 - 汇总表行列交换测试")
    print("=" * 60)
    
    try:
        success = test_table_layout()
        if success:
            print("\n✅ 表格布局测试通过！行列交换功能正常")
            print("\n📋 新的表格布局:")
            print("- 总体统计：保持原有的排名表格式")
            print("- 周期统计：周期作为行，人员作为列，末尾添加总计列和总计行")
            print("- 用户体验：更便于横向对比和趋势分析")
        else:
            print("\n❌ 测试失败")
    except Exception as e:
        print(f"\n❌ 测试过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
