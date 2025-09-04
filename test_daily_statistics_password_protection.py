"""
Test script for Daily Statistics Password Protection functionality
"""

import requests
import sys
import json

def test_daily_statistics_password_protection():
    """Test the password protection functionality for daily statistics"""
    
    base_url = "http://localhost:5000"
    
    print("Testing Daily Statistics Password Protection...")
    print("=" * 50)
    
    # Test 1: Check authentication status (should be false initially)
    print("1. Testing authentication status check...")
    try:
        response = requests.get(f"{base_url}/api/daily-stats-auth-status")
        data = response.json()
        
        if response.status_code == 200:
            print(f"   ✓ Auth status check successful")
            print(f"   ✓ Initial auth status: {data.get('authenticated', False)}")
        else:
            print(f"   ✗ Auth status check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Error checking auth status: {e}")
        return False
    
    # Test 2: Try to update schedule without authentication (should fail)
    print("\n2. Testing schedule update without authentication...")
    try:
        payload = {
            "schedule_time": "14:30",
            "enabled": True
        }
        response = requests.post(f"{base_url}/api/update-schedule", 
                               json=payload,
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 401:
            data = response.json()
            if data.get('auth_required'):
                print(f"   ✓ Correctly blocked unauthorized schedule update")
                print(f"   ✓ Response: {data.get('error')}")
            else:
                print(f"   ✗ Wrong error format for unauthorized request")
                return False
        else:
            print(f"   ✗ Should have been blocked, got status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Error testing unauthorized schedule update: {e}")
        return False
    
    # Test 3: Try to calculate statistics without authentication (should fail)
    print("\n3. Testing calculate statistics without authentication...")
    try:
        response = requests.post(f"{base_url}/api/calculate-daily-stats",
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 401:
            data = response.json()
            if data.get('auth_required'):
                print(f"   ✓ Correctly blocked unauthorized statistics calculation")
                print(f"   ✓ Response: {data.get('error')}")
            else:
                print(f"   ✗ Wrong error format for unauthorized request")
                return False
        else:
            data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
            print(f"   ✗ Should have been blocked, got status: {response.status_code}")
            print(f"   ✗ Response: {data}")
            return False
    except Exception as e:
        print(f"   ✗ Error testing unauthorized calculation: {e}")
        return False
    
    # Test 4: Try authentication with wrong password (should fail)
    print("\n4. Testing authentication with wrong password...")
    try:
        payload = {"password": "wrongpassword"}
        response = requests.post(f"{base_url}/api/daily-stats-authenticate",
                               json=payload,
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 401:
            data = response.json()
            print(f"   ✓ Correctly rejected wrong password")
            print(f"   ✓ Response: {data.get('error')}")
        else:
            print(f"   ✗ Should have rejected wrong password, got status: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Error testing wrong password: {e}")
        return False
    
    # Test 5: Try authentication with correct password (should succeed)
    print("\n5. Testing authentication with correct password...")
    try:
        payload = {"password": "admin123"}  # Default password from config
        response = requests.post(f"{base_url}/api/daily-stats-authenticate",
                               json=payload,
                               headers={'Content-Type': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✓ Successfully authenticated with correct password")
                print(f"   ✓ Response: {data.get('message')}")
                
                # Store session for next requests
                session_cookies = response.cookies
            else:
                print(f"   ✗ Authentication response format error")
                return False
        else:
            print(f"   ✗ Authentication failed with correct password: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Error testing correct password: {e}")
        return False
    
    # Test 6: Check authentication status after login (should be true)
    print("\n6. Testing authentication status after login...")
    try:
        response = requests.get(f"{base_url}/api/daily-stats-auth-status", 
                              cookies=session_cookies)
        data = response.json()
        
        if response.status_code == 200 and data.get('authenticated'):
            print(f"   ✓ Auth status correctly shows authenticated")
        else:
            print(f"   ✗ Auth status should show authenticated: {data}")
            return False
    except Exception as e:
        print(f"   ✗ Error checking auth status after login: {e}")
        return False
    
    # Test 7: Try to update schedule with authentication (should succeed or at least not be blocked by auth)
    print("\n7. Testing schedule update with authentication...")
    try:
        payload = {
            "schedule_time": "14:30",
            "enabled": True
        }
        response = requests.post(f"{base_url}/api/update-schedule", 
                               json=payload,
                               headers={'Content-Type': 'application/json'},
                               cookies=session_cookies)
        
        if response.status_code != 401:
            print(f"   ✓ Authentication passed (status: {response.status_code})")
            data = response.json()
            if response.status_code == 200:
                print(f"   ✓ Schedule update successful")
            else:
                print(f"   ⚠ Other error (not auth): {data.get('error', 'Unknown error')}")
        else:
            print(f"   ✗ Still blocked by authentication")
            return False
    except Exception as e:
        print(f"   ✗ Error testing authenticated schedule update: {e}")
        return False
    
    # Test 8: Test logout functionality
    print("\n8. Testing logout functionality...")
    try:
        response = requests.post(f"{base_url}/api/daily-stats-logout",
                               headers={'Content-Type': 'application/json'},
                               cookies=session_cookies)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✓ Successfully logged out")
                print(f"   ✓ Response: {data.get('message')}")
            else:
                print(f"   ✗ Logout response format error")
                return False
        else:
            print(f"   ✗ Logout failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Error testing logout: {e}")
        return False
    
    # Test 9: Check authentication status after logout (should be false)
    print("\n9. Testing authentication status after logout...")
    try:
        response = requests.get(f"{base_url}/api/daily-stats-auth-status",
                              cookies=session_cookies)
        data = response.json()
        
        if response.status_code == 200 and not data.get('authenticated'):
            print(f"   ✓ Auth status correctly shows not authenticated")
        else:
            print(f"   ✗ Auth status should show not authenticated: {data}")
            return False
    except Exception as e:
        print(f"   ✗ Error checking auth status after logout: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ All password protection tests passed!")
    print("\nPassword protection is working correctly:")
    print("- Modification endpoints are protected")
    print("- Authentication system is functional")
    print("- Session management works properly")
    print("- Default password is: admin123")
    return True

def test_daily_statistics_page_access():
    """Test that the daily statistics page loads correctly"""
    
    base_url = "http://localhost:5000"
    
    print("\nTesting Daily Statistics Page Access...")
    print("=" * 50)
    
    try:
        # Test page access
        response = requests.get(f"{base_url}/daily-statistics")
        
        if response.status_code == 200:
            print("✓ Daily statistics page loads successfully")
            
            # Check if page contains password modal
            if 'passwordModal' in response.text:
                print("✓ Password modal is present in the page")
            else:
                print("✗ Password modal not found in the page")
                return False
                
            # Check if auth status indicator is present
            if 'authStatusIndicator' in response.text:
                print("✓ Authentication status indicator is present")
            else:
                print("✗ Authentication status indicator not found")
                return False
                
            return True
        else:
            print(f"✗ Daily statistics page failed to load: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"✗ Error accessing daily statistics page: {e}")
        return False

if __name__ == "__main__":
    print("Daily Statistics Password Protection Test")
    print("Make sure the Flask application is running on http://localhost:5000")
    print()
    
    # Test page access first
    if not test_daily_statistics_page_access():
        print("❌ Page access test failed")
        sys.exit(1)
    
    # Test password protection functionality
    if not test_daily_statistics_password_protection():
        print("❌ Password protection test failed")
        sys.exit(1)
    
    print("\n🎉 All tests passed! Password protection is working correctly.")
