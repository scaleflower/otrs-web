"""
Test script to verify the upload functionality with progress tracking
"""
import requests
import time

def test_progress_endpoint():
    """Test the progress endpoint"""
    print("Testing progress endpoint...")
    response = requests.get('http://127.0.0.1:5000/progress')
    if response.status_code == 200:
        progress_data = response.json()
        print(f"Progress endpoint response: {progress_data}")
        return True
    else:
        print(f"Error: {response.status_code}")
        return False

def test_upload_with_progress():
    """Test file upload and monitor progress"""
    print("\nTesting file upload with progress monitoring...")
    
    # Create a simple test Excel file (or use an existing one)
    # For now, we'll just test the progress polling
    
    # Start monitoring progress
    print("Starting progress monitoring...")
    for i in range(10):
        try:
            response = requests.get('http://127.0.0.1:5000/progress')
            if response.status_code == 200:
                progress_data = response.json()
                print(f"Progress: Step {progress_data['current_step']}/{progress_data['total_steps']} - {progress_data['message']}")
                if progress_data['details']:
                    print(f"  Details: {progress_data['details']}")
            else:
                print(f"Error getting progress: {response.status_code}")
        except Exception as e:
            print(f"Error: {e}")
        
        time.sleep(1)
    
    print("Progress monitoring test completed.")

if __name__ == '__main__':
    # Test the progress endpoint
    if test_progress_endpoint():
        print("✓ Progress endpoint test passed")
    else:
        print("✗ Progress endpoint test failed")
    
    # Test progress monitoring
    test_upload_with_progress()
