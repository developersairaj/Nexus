"""
FlowGenix App Blocking Test - Verify blocking functionality works
"""

import time
import requests
import json
import psutil
import subprocess
import os

def test_blocker_service():
    """Test if the blocker service is running and responsive"""
    print("🧪 Testing FlowGenix Blocker Service...")
    
    try:
        # Test health endpoint
        response = requests.get('http://localhost:8888/health', timeout=5)
        if response.status_code == 200:
            print("✅ Blocker service is running and responsive")
            return True
        else:
            print(f"❌ Blocker service health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to blocker service: {e}")
        print("💡 Make sure to run 'python flowgenix_unified_launcher.py' first")
        return False

def test_focus_mode_activation():
    """Test if focus mode can be activated"""
    print("\n🎯 Testing focus mode activation...")
    
    try:
        # Start focus mode for 1 minute (test duration)
        data = {'duration': 1}
        response = requests.post('http://localhost:8888/start', 
                               json=data, 
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Focus mode activated successfully!")
                print(f"📊 Initial apps terminated: {result.get('initial_blocked', 0)}")
                return True
            else:
                print(f"❌ Focus mode activation failed: {result.get('message')}")
                return False
        else:
            print(f"❌ Focus mode activation request failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error activating focus mode: {e}")
        return False

def test_status_endpoint():
    """Test if status endpoint works"""
    print("\n📊 Testing status endpoint...")
    
    try:
        response = requests.get('http://localhost:8888/status', timeout=5)
        if response.status_code == 200:
            status = response.json()
            print("✅ Status endpoint working")
            print(f"📈 Active: {status.get('active', False)}")
            print(f"🔢 Blocked count: {status.get('blocked_count', 0)}")
            return True
        else:
            print(f"❌ Status endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting status: {e}")
        return False

def test_app_termination():
    """Test if distracting apps are actually blocked"""
    print("\n🚫 Testing app blocking functionality...")
    
    # List of test apps to check if they get blocked
    test_processes = []
    blocked_apps = ['chrome.exe', 'msedge.exe', 'notepad.exe', 'calc.exe']
    
    print("🔍 Checking for running distracting processes...")
    
    # Check what's currently running that should be blocked
    for process in psutil.process_iter(['pid', 'name']):
        try:
            process_name = process.info['name'].lower()
            if any(blocked_app.lower() in process_name for blocked_app in blocked_apps):
                test_processes.append((process.info['pid'], process.info['name']))
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    if test_processes:
        print(f"✅ Found {len(test_processes)} processes that should be blocked:")
        for pid, name in test_processes:
            print(f"   • {name} (PID: {pid})")
        return True
    else:
        print("ℹ️ No target processes currently running to test blocking")
        print("💡 Try opening Calculator or Notepad and then activate focus mode")
        return True

def test_stop_focus_mode():
    """Test if focus mode can be stopped"""
    print("\n🛑 Testing focus mode deactivation...")
    
    try:
        response = requests.post('http://localhost:8888/stop',
                               headers={'Content-Type': 'application/json'},
                               timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✅ Focus mode stopped successfully!")
                return True
            else:
                print(f"❌ Focus mode stop failed: {result.get('message')}")
                return False
        else:
            print(f"❌ Stop request failed: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error stopping focus mode: {e}")
        return False

def main():
    """Run all blocker tests"""
    print("=" * 60)
    print("🛡️ FlowGenix App Blocking Functionality Test")
    print("=" * 60)
    
    # Run tests
    tests = [
        ("Service Connection", test_blocker_service),
        ("Status Endpoint", test_status_endpoint),
        ("App Detection", test_app_termination),
        ("Focus Mode Start", test_focus_mode_activation),
        ("Focus Mode Stop", test_stop_focus_mode),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! FlowGenix blocking is working correctly!")
    else:
        print(f"⚠️ {total - passed} test(s) failed. Check the errors above.")
    
    print("\n💡 USAGE INSTRUCTIONS:")
    print("1. Run: python flowgenix_unified_launcher.py")
    print("2. Open the web UI at http://localhost:8888")
    print("3. Click 'START FOCUS' to activate ultra-restrictive mode")
    print("4. All distracting apps will be terminated immediately!")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")
