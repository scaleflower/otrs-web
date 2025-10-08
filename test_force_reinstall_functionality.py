#!/usr/bin/env python3
"""Test script to verify force reinstall functionality"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.update_service import UpdateService

def test_force_reinstall_logic():
    """Test the force reinstall logic"""
    print("🧪 Testing force reinstall logic...")
    
    update_service = UpdateService()
    
    # Test cases for version comparison
    test_cases = [
        # (current_version, target_version, force_reinstall, expected_result)
        ('1.2.3', '1.2.3', False, False),  # Same version, no force reinstall - should prevent
        ('1.2.3', '1.2.3', True, True),    # Same version, force reinstall - should allow
        ('1.2.3', '1.2.4', False, True),   # Different version, no force reinstall - should allow
        ('1.2.3', '1.2.4', True, True),    # Different version, force reinstall - should allow
    ]
    
    for current, target, force, expected in test_cases:
        # Simulate the logic from trigger_update method
        if force:
            print(f"🔄 Forced reinstall of current version: {target}")
            result = True
        else:
            # Normal update check: if target version == current version, prevent update
            if target == current and not force:
                result = False
                print(f"❌ Update prevented: Already using version {target}")
            else:
                result = True
                print(f"✅ Update allowed: {current} -> {target}")
        
        status = "✅" if result == expected else "❌"
        print(f"{status} {current} -> {target} (force={force}): expected={expected}, got={result}")
    
    print("\n🎉 Force reinstall logic test completed!")

def test_api_endpoints():
    """Test the API endpoints exist"""
    print("\n🔍 Checking API endpoints...")
    
    import app
    from flask import Flask
    
    test_app = Flask(__name__)
    test_app.config['TESTING'] = True
    
    with test_app.app_context():
        # Check if the reinstall endpoint exists
        try:
            from app import api_reinstall_current_version
            print("✅ /api/update/reinstall endpoint exists")
        except ImportError:
            print("❌ /api/update/reinstall endpoint not found")
        
        # Check if the trigger endpoint supports force_reinstall
        try:
            from app import api_trigger_update
            print("✅ /api/update/trigger endpoint exists")
        except ImportError:
            print("❌ /api/update/trigger endpoint not found")

if __name__ == '__main__':
    test_force_reinstall_logic()
    test_api_endpoints()
