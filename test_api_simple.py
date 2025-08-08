import requests
import json
import time

def test_simple_analysis():
    """Test a simple analysis request"""
    url = "http://127.0.0.1:8000/api/analysis/start"
    
    # Simple test with a small directory
    payload = {
        "directories": ["M:\\Soundeo 2024\\8.2025"],
        "max_files": 3
    }
    
    print("Testing simple analysis...")
    try:
        response = requests.post(url, json=payload, timeout=30)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:500]}...")
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get('task_id')
            print(f"Analysis started with task_id: {task_id}")
            return task_id
        else:
            print(f"Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def test_tracks_endpoint():
    """Test the tracks endpoint"""
    url = "http://127.0.0.1:8000/api/tracks"
    
    print("\nTesting tracks endpoint...")
    try:
        response = requests.get(url, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text[:300]}...")
        
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    print("=== API Test ===")
    
    # Test tracks endpoint first
    test_tracks_endpoint()
    
    # Test analysis
    task_id = test_simple_analysis()
    
    if task_id:
        print(f"\nAnalysis started successfully with task_id: {task_id}")
        print("Check the backend logs for any SQLite threading errors.")
    else:
        print("\nAnalysis failed to start.")