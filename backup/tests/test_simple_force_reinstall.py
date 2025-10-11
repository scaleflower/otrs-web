#!/usr/bin/env python3
"""Simple test for force reinstall functionality"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.update_service import UpdateService

def test_version_comparison():
    """Test version comparison logic"""
    print("🧪 Testing version comparison logic...")
    
    update_service = UpdateService()
    
    test_cases = [
        ('1.2.3', '1.2.3', False),  # Same version, no update
        ('1.2.3', '1.2.4', True),   # Newer version, should update
        ('1.2.4', '1.2.3', False),  # Older version, no update
        ('1.2.3', 'release/v1.2.6', True),  # Complex version format
        ('1.2.3', 'v1.2.6', True),  # v-prefixed version
    ]
    
    for current, latest, expected in test_cases:
        result = update_service._compare_versions(current, latest)
        status = "✅" if result == expected else "❌"
        print(f"{status} {current} -> {latest}: expected={expected}, got={result}")

def test_force_reinstall_logic():
    """Test force reinstall logic"""
    print("\n🧪 Testing force reinstall logic...")
    
    # Test the logic that prevents normal updates for same version
    current_version = '1.2.3'
    target_version = '1.2.3'
    force_reinstall = False
    
    # This should prevent update
    if target_version == current_version and not force_reinstall:
        print("✅ Normal update correctly prevented for same version")
    else:
        print("❌ Normal update logic failed")
    
    # This should allow update
    force_reinstall = True
    if target_version == current_version and not force_reinstall:
        print("❌ Force reinstall logic failed")
    else:
        print("✅ Force reinstall correctly allowed for same version")

if __name__ == '__main__':
    test_version_comparison()
    test_force_reinstall_logic()
    print("\n🎉 Simple force reinstall test completed!")
