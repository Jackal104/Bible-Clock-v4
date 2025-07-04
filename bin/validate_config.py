#!/usr/bin/env python3
"""
Validate Bible Clock configuration and dependencies.
"""

import sys
import os
import json
from pathlib import Path
from dotenv import load_dotenv

def check_environment():
    """Check environment configuration."""
    print("Checking environment configuration...")
    
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ .env file not found. Copy .env.template to .env")
        return False
    
    load_dotenv()
    
    required_vars = [
        'DISPLAY_WIDTH', 'DISPLAY_HEIGHT', 'BIBLE_API_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment configuration valid")
    return True

def check_dependencies():
    """Check Python dependencies."""
    print("Checking Python dependencies...")
    
    required_packages = [
        'PIL', 'requests', 'dotenv', 'schedule', 'flask', 'psutil'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install -r requirements.txt")
        return False
    
    print("✅ Python dependencies satisfied")
    return True

def check_data_files():
    """Check required data files."""
    print("Checking data files...")
    
    required_files = [
        'data/fallback_verses.json',
        'data/bible_book_summaries_kjv_all_66.json',
        'data/translations/bible_kjv.json'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print(f"❌ Missing data files: {', '.join(missing_files)}")
        return False
    
    # Validate JSON files
    for file_path in required_files:
        try:
            with open(file_path, 'r') as f:
                json.load(f)
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON in {file_path}")
            return False
    
    print("✅ Data files valid")
    return True

def check_hardware():
    """Check hardware availability."""
    print("Checking hardware...")
    
    simulation_mode = os.getenv('SIMULATION_MODE', 'false').lower() == 'true'
    
    if simulation_mode:
        print("ℹ️  Running in simulation mode - hardware checks skipped")
        return True
    
    try:
        import RPi.GPIO
        import spidev
        print("✅ Hardware libraries available")
        return True
    except ImportError as e:
        print(f"❌ Hardware libraries missing: {e}")
        print("Install with: pip install RPi.GPIO spidev")
        return False

def main():
    """Run all validation checks."""
    print("Bible Clock Configuration Validator")
    print("=" * 40)
    
    checks = [
        check_environment,
        check_dependencies,
        check_data_files,
        check_hardware
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 All checks passed! Bible Clock is ready to run.")
        return 0
    else:
        print("❌ Some checks failed. Please resolve the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())