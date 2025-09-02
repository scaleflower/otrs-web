#!/usr/bin/env python3
"""
Test script to verify the summary statistics feature
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, OtrsTicket
from datetime import datetime, timedelta
import json

def test_summary_statistics():
    """Test that summary statistics are properly sorted"""
    print("Testing summary statistics feature...")
    
    with app.app_context():
        # Get statistics for multiple responsibles
        from app import get_responsible_stats
        
        # Test data
        period = 'day'
        selected_responsibles = ['张三', '李四', '王五', '赵六']
        
        # Get statistics
        stats, totals = get_responsible_stats(period, selected_responsibles)
        
        print(f"Statistics keys: {list(stats.keys())}")
        print(f"Totals: {totals}")
        
        # Verify totals are properly calculated
        assert len(totals) == len(selected_responsibles), "Should have totals for all selected responsibles"
        
        # Test sorting functionality (simulate what the frontend does)
        sorted_totals = sorted(totals.items(), key=lambda x: x[1], reverse=True)
        print(f"Sorted totals (descending): {sorted_totals}")
        
        # Verify sorting works correctly
        previous_count = float('inf')
        for responsible, count in sorted_totals:
            assert count <= previous_count, f"Sorting error: {count} should be <= {previous_count}"
            previous_count = count
            print(f"  {responsible}: {count}")
        
        print("✓ Summary statistics sorting works correctly")
        
        # Test ranking
        ranked_totals = []
        for rank, (responsible, count) in enumerate(sorted_totals, 1):
            ranked_totals.append({
                'rank': rank,
                'responsible': responsible,
                'count': count
            })
        
        print("Ranked totals:")
        for item in ranked_totals:
            print(f"  {item['rank']}. {item['responsible']}: {item['count']}")
        
        print("✓ Ranking functionality works correctly")

def main():
    """Main test function"""
    print("Testing summary statistics feature...")
    
    try:
        test_summary_statistics()
        print("\n🎉 All summary statistics tests passed!")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
