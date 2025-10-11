#!/usr/bin/env python3
"""Debug version comparison logic"""

import sys
from pathlib import Path
import re

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.update_service import UpdateService

def debug_version_comparison():
    """Debug version comparison logic"""
    print("🔍 Debugging version comparison logic...")
    
    update_service = UpdateService()
    
    test_cases = [
        ('1.2.3', 'release/v1.2.6'),
        ('1.2.3', 'v1.2.6'),
    ]
    
    for current, latest in test_cases:
        print(f"\n--- Testing: {current} -> {latest} ---")
        
        # Test the clean_version function
        def clean_version(version):
            if not version:
                return "0.0.0"
            
            version_str = str(version).strip()
            print(f"  Original: '{version_str}'")
            
            # 查找版本号模式：数字.数字.数字
            match = re.search(r'(\d+\.\d+\.\d+)', version_str)
            if match:
                result = match.group(1)
                print(f"  Cleaned: '{result}' (full match)")
                return result
            
            # 如果没有找到完整的三段版本号，尝试查找两段或一段
            match = re.search(r'(\d+\.\d+)', version_str)
            if match:
                result = match.group(1) + '.0'
                print(f"  Cleaned: '{result}' (two-part match)")
                return result
            
            match = re.search(r'(\d+)', version_str)
            if match:
                result = match.group(1) + '.0.0'
                print(f"  Cleaned: '{result}' (one-part match)")
                return result
            
            print(f"  Cleaned: '0.0.0' (no match)")
            return "0.0.0"
        
        current_clean = clean_version(current)
        latest_clean = clean_version(latest)
        
        print(f"  Current cleaned: {current_clean}")
        print(f"  Latest cleaned: {latest_clean}")
        
        # Test the actual comparison
        result = update_service._compare_versions(current, latest)
        print(f"  Comparison result: {result}")

if __name__ == '__main__':
    debug_version_comparison()
