#!/usr/bin/env python3
"""
Diagnostic script to troubleshoot web interface issues
"""

import os
import sys
import socket
import subprocess
from pathlib import Path

def check_python_environment():
    """Check Python and virtual environment"""
    print("=== Python Environment ===")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Virtual environment: {sys.prefix}")
    
    # Check if we're in virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment is active")
    else:
        print("❌ Virtual environment not active")
    
    print()

def check_flask_installation():
    """Check Flask installation"""
    print("=== Flask Installation ===")
    try:
        import flask
        print(f"✅ Flask version: {flask.__version__}")
        print(f"Flask path: {flask.__file__}")
    except ImportError as e:
        print(f"❌ Flask not installed: {e}")
    print()

def check_network_connectivity():
    """Check network settings"""
    print("=== Network Configuration ===")
    
    # Get hostname
    hostname = socket.gethostname()
    print(f"Hostname: {hostname}")
    
    # Get IP addresses
    try:
        # Get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"Local IP: {local_ip}")
    except Exception as e:
        print(f"Could not get local IP: {e}")
    
    # Check if port 5000 is available
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 5000))
        s.close()
        print("✅ Port 5000 is available")
    except OSError as e:
        print(f"❌ Port 5000 issue: {e}")
    
    print()

def check_file_permissions():
    """Check file permissions"""
    print("=== File Permissions ===")
    
    files_to_check = [
        'main.py',
        'src/web_interface/app.py',
        'src/web_interface/templates/dashboard.html',
        '.env'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            stat = os.stat(file_path)
            print(f"✅ {file_path} - Mode: {oct(stat.st_mode)}")
        else:
            print(f"❌ {file_path} - Not found")
    
    print()

def check_dependencies():
    """Check required dependencies"""
    print("=== Dependencies ===")
    
    required_modules = [
        'flask', 'pathlib', 'json', 'logging', 'datetime', 
        'psutil', 'threading', 'os'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module} - Missing")
    
    print()

def check_processes():
    """Check running processes"""
    print("=== Running Processes ===")
    try:
        import psutil
        bible_processes = []
        flask_processes = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'bible' in cmdline.lower() or 'main.py' in cmdline:
                    bible_processes.append(f"PID {proc.info['pid']}: {cmdline}")
                elif 'flask' in cmdline.lower():
                    flask_processes.append(f"PID {proc.info['pid']}: {cmdline}")
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        if bible_processes:
            print("Bible Clock processes:")
            for proc in bible_processes:
                print(f"  {proc}")
        else:
            print("❌ No Bible Clock processes running")
            
        if flask_processes:
            print("Flask processes:")
            for proc in flask_processes:
                print(f"  {proc}")
        else:
            print("❌ No Flask processes running")
            
    except ImportError:
        print("psutil not available for process checking")
    
    print()

def main():
    """Run all diagnostic checks"""
    print("🔍 Bible Clock Web Interface Diagnostics")
    print("=" * 50)
    
    check_python_environment()
    check_flask_installation()
    check_network_connectivity()
    check_file_permissions()
    check_dependencies()
    check_processes()
    
    print("=== Recommendations ===")
    print("1. Try starting the simple test server:")
    print("   python test_web_simple.py")
    print()
    print("2. If that works, try the main application:")
    print("   python main.py --web-only")
    print()
    print("3. Check firewall settings if still not accessible")
    print("4. Try accessing from Pi locally first: http://localhost:5000")

if __name__ == '__main__':
    main()