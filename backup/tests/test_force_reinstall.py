#!/usr/bin/env python3
"""Test script for force reinstall functionality"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from services.update_service import UpdateService
from models import db, AppUpdateStatus
from config import Config

def test_force_reinstall():
    """Test force reinstall functionality"""
    print("🧪 Testing force reinstall functionality...")
    
    # Create a mock Flask app for testing
    from flask import Flask
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize database
    with app.app_context():
        db.init_app(app)
        db.create_all()
        
        # Initialize update service
        update_service = UpdateService()
        update_service.initialize(app)
        
        # Test 1: Check version comparison logic
        print("\n1. Testing version comparison logic...")
        test_cases = [
            ('1.2.3', '1.2.3', False),  # Same version, no update
            ('1.2.3', '1.2.4', True),   # Newer version, should update
            ('1.2.4', '1.2.3', False),  # Older version, no update
            ('release/v1.2.6', '1.2.3', True),  # Complex version format
            ('v1.2.6', '1.2.3', True),  # v-prefixed version
        ]
        
        for current, latest, expected in test_cases:
            result = update_service._compare_versions(current, latest)
            status = "✅" if result == expected else "❌"
            print(f"{status} {current} -> {latest}: expected={expected}, got={result}")
        
        # Test 2: Check if force_reinstall parameter is accepted
        print("\n2. Testing force_reinstall parameter...")
        try:
            # This should work without raising an error
            result = update_service.trigger_update('1.2.3', force_reinstall=True)
            print(f"✅ Force reinstall parameter accepted: {result}")
        except Exception as e:
            print(f"❌ Force reinstall parameter failed: {e}")
        
        # Test 3: Check normal update with same version (should fail)
        print("\n3. Testing normal update with same version (should fail)...")
        try:
            # Reset update status first
            status = AppUpdateStatus.query.first()
            if status:
                status.status = 'up_to_date'
                db.session.commit()
            
            result = update_service.trigger_update('1.2.3', force_reinstall=False)
            print(f"❌ Normal update with same version should have failed but got: {result}")
        except RuntimeError as e:
            if "Already using version" in str(e):
                print(f"✅ Normal update correctly rejected same version: {e}")
            else:
                print(f"❌ Unexpected error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error type: {e}")
        
        # Test 4: Check force reinstall with same version
        print("\n4. Testing force reinstall with same version...")
        try:
            # Reset update status first
            status = AppUpdateStatus.query.first()
            if status:
                status.status = 'up_to_date'
                db.session.commit()
            
            result = update_service.trigger_update('1.2.3', force_reinstall=True)
            print(f"✅ Force reinstall with same version: {result}")
        except Exception as e:
            print(f"❌ Force reinstall with same version failed: {e}")
        
        print("\n🎉 Force reinstall functionality test completed!")

if __name__ == '__main__':
    test_force_reinstall()
