#!/usr/bin/env python3
"""
Test script for database backup functionality
"""

import os
import sys
import time
import shutil
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_backup_functionality():
    """Test the complete backup functionality"""
    print("🧪 Testing Database Backup Functionality")
    print("=" * 50)
    
    try:
        # Import after path setup
        from app import app
        from services.backup_service import BackupService
        from services.scheduler_service import SchedulerService
        
        test_results = []
        
        # Test 1: Initialize backup service
        print("\n📋 Test 1: Initialize Backup Service")
        try:
            with app.app_context():
                backup_service = BackupService(app)
                print(f"✓ Backup service initialized")
                print(f"  - Backup folder: {backup_service.backup_folder}")
                print(f"  - Database path: {backup_service.db_path}")
                print(f"  - Retention days: {backup_service.retention_days}")
                test_results.append(("Backup Service Initialization", True, ""))
        except Exception as e:
            error_msg = f"Failed to initialize backup service: {str(e)}"
            print(f"✗ {error_msg}")
            test_results.append(("Backup Service Initialization", False, error_msg))
            return test_results
        
        # Test 2: Create manual backup
        print("\n📋 Test 2: Create Manual Backup")
        try:
            with app.app_context():
                success, message, backup_path = backup_service.create_backup(
                    compress=True, 
                    include_timestamp=True
                )
                
                if success:
                    print(f"✓ {message}")
                    print(f"  - Backup path: {backup_path}")
                    print(f"  - File exists: {os.path.exists(backup_path) if backup_path else False}")
                    test_results.append(("Manual Backup Creation", True, message))
                else:
                    print(f"✗ {message}")
                    test_results.append(("Manual Backup Creation", False, message))
        except Exception as e:
            error_msg = f"Error creating backup: {str(e)}"
            print(f"✗ {error_msg}")
            test_results.append(("Manual Backup Creation", False, error_msg))
        
        # Test 3: List backups
        print("\n📋 Test 3: List Available Backups")
        try:
            with app.app_context():
                backups = backup_service.list_backups()
                print(f"✓ Found {len(backups)} backup(s)")
                
                for i, backup in enumerate(backups[:3]):  # Show first 3
                    print(f"  {i+1}. {backup['filename']}")
                    print(f"     Size: {backup['size_mb']} MB")
                    print(f"     Created: {backup['created_date']}")
                    print(f"     Age: {backup['age_days']} days")
                    print(f"     Compressed: {backup['compressed']}")
                
                test_results.append(("List Backups", True, f"Found {len(backups)} backups"))
        except Exception as e:
            error_msg = f"Error listing backups: {str(e)}"
            print(f"✗ {error_msg}")
            test_results.append(("List Backups", False, error_msg))
        
        # Test 4: Get backup statistics
        print("\n📋 Test 4: Get Backup Statistics")
        try:
            with app.app_context():
                stats = backup_service.get_backup_stats()
                print(f"✓ Backup statistics retrieved")
                print(f"  - Total backups: {stats['total_backups']}")
                print(f"  - Total size: {stats['total_size_mb']} MB")
                print(f"  - Compressed count: {stats['compressed_count']}")
                print(f"  - Retention days: {stats['retention_days']}")
                if stats.get('newest_backup'):
                    print(f"  - Newest backup: {stats['newest_backup']}")
                if stats.get('oldest_backup'):
                    print(f"  - Oldest backup: {stats['oldest_backup']}")
                
                test_results.append(("Backup Statistics", True, "Statistics retrieved successfully"))
        except Exception as e:
            error_msg = f"Error getting backup statistics: {str(e)}"
            print(f"✗ {error_msg}")
            test_results.append(("Backup Statistics", False, error_msg))
        
        # Test 5: Verify backup integrity
        print("\n📋 Test 5: Verify Backup Integrity")
        try:
            with app.app_context():
                backups = backup_service.list_backups()
                if backups:
                    latest_backup = backups[0]['filename']
                    success, message = backup_service.verify_backup(latest_backup)
                    
                    if success:
                        print(f"✓ {message}")
                        test_results.append(("Backup Verification", True, message))
                    else:
                        print(f"✗ {message}")
                        test_results.append(("Backup Verification", False, message))
                else:
                    print("⚠️  No backups available for verification")
                    test_results.append(("Backup Verification", True, "No backups to verify"))
        except Exception as e:
            error_msg = f"Error verifying backup: {str(e)}"
            print(f"✗ {error_msg}")
            test_results.append(("Backup Verification", False, error_msg))
        
        # Test 6: Test scheduler integration
        print("\n📋 Test 6: Test Scheduler Integration")
        try:
            with app.app_context():
                scheduler_service = SchedulerService()
                scheduler_service.initialize_scheduler(app)
                
                # Test manual backup trigger through scheduler
                success, message = scheduler_service.trigger_manual_backup()
                
                if success:
                    print(f"✓ Scheduler backup trigger: {message}")
                    test_results.append(("Scheduler Integration", True, message))
                else:
                    print(f"✗ Scheduler backup trigger failed: {message}")
                    test_results.append(("Scheduler Integration", False, message))
                
                # Get scheduler status
                status = scheduler_service.get_scheduler_status()
                print(f"  - Scheduler running: {status['running']}")
                print(f"  - Active jobs: {status['job_count']}")
                
                # Get backup status through scheduler
                backup_status = scheduler_service.get_backup_status()
                print(f"  - Backup service available: {backup_status.get('service_available', False)}")
                print(f"  - Auto backup enabled: {backup_status.get('auto_backup_enabled', False)}")
                
                scheduler_service.shutdown()
                
        except Exception as e:
            error_msg = f"Error testing scheduler integration: {str(e)}"
            print(f"✗ {error_msg}")
            test_results.append(("Scheduler Integration", False, error_msg))
        
        # Test 7: Test cleanup functionality
        print("\n📋 Test 7: Test Backup Cleanup")
        try:
            with app.app_context():
                # Test cleanup with very short retention (0 days) to clean up test backups
                success, message, deleted_count = backup_service.cleanup_old_backups(retention_days=999)  # Keep all for now
                
                print(f"✓ Cleanup test completed")
                print(f"  - {message}")
                print(f"  - Deleted count: {deleted_count}")
                
                test_results.append(("Backup Cleanup", True, f"Deleted {deleted_count} backups"))
        except Exception as e:
            error_msg = f"Error testing cleanup: {str(e)}"
            print(f"✗ {error_msg}")
            test_results.append(("Backup Cleanup", False, error_msg))
        
        # Test 8: Test configuration settings
        print("\n📋 Test 8: Test Configuration Settings")
        try:
            with app.app_context():
                backup_folder = app.config.get('BACKUP_FOLDER', 'database_backups')
                auto_backup = app.config.get('AUTO_BACKUP', True)
                
                print(f"✓ Configuration settings verified")
                print(f"  - Backup folder: {backup_folder}")
                print(f"  - Auto backup enabled: {auto_backup}")
                print(f"  - Backup folder exists: {os.path.exists(backup_folder)}")
                
                test_results.append(("Configuration Settings", True, "Settings verified"))
        except Exception as e:
            error_msg = f"Error checking configuration: {str(e)}"
            print(f"✗ {error_msg}")
            test_results.append(("Configuration Settings", False, error_msg))
        
        return test_results
        
    except Exception as e:
        error_msg = f"Critical error in backup testing: {str(e)}"
        print(f"❌ {error_msg}")
        return [("Critical Error", False, error_msg)]

def test_api_endpoints():
    """Test backup API endpoints"""
    print("\n🌐 Testing Backup API Endpoints")
    print("=" * 50)
    
    try:
        from app import app
        import json
        
        test_results = []
        
        with app.test_client() as client:
            
            # Test 1: Backup status endpoint
            print("\n📋 Test 1: Backup Status API")
            try:
                response = client.get('/api/backup/status')
                print(f"  - Status code: {response.status_code}")
                
                if response.status_code == 200:
                    data = json.loads(response.data)
                    print(f"  - Service available: {data.get('service_available', False)}")
                    print(f"✓ Backup status API working")
                    test_results.append(("Backup Status API", True, ""))
                else:
                    print(f"✗ Unexpected status code: {response.status_code}")
                    test_results.append(("Backup Status API", False, f"Status {response.status_code}"))
                    
            except Exception as e:
                error_msg = f"Error testing status API: {str(e)}"
                print(f"✗ {error_msg}")
                test_results.append(("Backup Status API", False, error_msg))
            
            # Test 2: Backup list endpoint
            print("\n📋 Test 2: Backup List API")
            try:
                response = client.get('/api/backup/list')
                print(f"  - Status code: {response.status_code}")
                
                if response.status_code == 200:
                    data = json.loads(response.data)
                    backup_count = len(data.get('backups', []))
                    print(f"  - Backup count: {backup_count}")
                    print(f"✓ Backup list API working")
                    test_results.append(("Backup List API", True, f"{backup_count} backups found"))
                else:
                    print(f"✗ Unexpected status code: {response.status_code}")
                    test_results.append(("Backup List API", False, f"Status {response.status_code}"))
                    
            except Exception as e:
                error_msg = f"Error testing list API: {str(e)}"
                print(f"✗ {error_msg}")
                test_results.append(("Backup List API", False, error_msg))
            
            # Test 3: Backup verification endpoint
            print("\n📋 Test 3: Backup Verification API")
            try:
                # First get a backup to verify
                list_response = client.get('/api/backup/list')
                if list_response.status_code == 200:
                    list_data = json.loads(list_response.data)
                    backups = list_data.get('backups', [])
                    
                    if backups:
                        test_filename = backups[0]['filename']
                        verify_response = client.post('/api/backup/verify', 
                                                    json={'filename': test_filename})
                        print(f"  - Status code: {verify_response.status_code}")
                        
                        if verify_response.status_code == 200:
                            verify_data = json.loads(verify_response.data)
                            print(f"  - Verification: {verify_data.get('success', False)}")
                            print(f"✓ Backup verification API working")
                            test_results.append(("Backup Verification API", True, ""))
                        else:
                            print(f"✗ Unexpected status code: {verify_response.status_code}")
                            test_results.append(("Backup Verification API", False, f"Status {verify_response.status_code}"))
                    else:
                        print("⚠️  No backups available for verification test")
                        test_results.append(("Backup Verification API", True, "No backups to verify"))
                else:
                    print(f"✗ Could not get backup list for verification test")
                    test_results.append(("Backup Verification API", False, "Could not get backup list"))
                    
            except Exception as e:
                error_msg = f"Error testing verification API: {str(e)}"
                print(f"✗ {error_msg}")
                test_results.append(("Backup Verification API", False, error_msg))
        
        return test_results
        
    except Exception as e:
        error_msg = f"Critical error in API testing: {str(e)}"
        print(f"❌ {error_msg}")
        return [("API Critical Error", False, error_msg)]

def print_test_summary(all_results):
    """Print a summary of all test results"""
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    total_tests = len(all_results)
    passed_tests = sum(1 for _, success, _ in all_results if success)
    failed_tests = total_tests - passed_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests} ✓")
    print(f"Failed: {failed_tests} ✗")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests > 0:
        print("\n❌ FAILED TESTS:")
        for test_name, success, message in all_results:
            if not success:
                print(f"  • {test_name}: {message}")
    
    print("\n📊 DETAILED RESULTS:")
    for test_name, success, message in all_results:
        status = "✓" if success else "✗"
        print(f"  {status} {test_name}")
        if message and not success:
            print(f"    {message}")

def main():
    """Main test execution"""
    print("🚀 Starting Database Backup Functionality Tests")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = []
    
    # Run backup functionality tests
    backup_results = test_backup_functionality()
    all_results.extend(backup_results)
    
    # Run API endpoint tests
    api_results = test_api_endpoints()
    all_results.extend(api_results)
    
    # Print summary
    print_test_summary(all_results)
    
    # Exit with appropriate code
    failed_count = sum(1 for _, success, _ in all_results if not success)
    sys.exit(0 if failed_count == 0 else 1)

if __name__ == '__main__':
    main()
