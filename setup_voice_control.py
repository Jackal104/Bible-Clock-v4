#!/usr/bin/env python3
"""
Setup script for Bible Clock Voice Control System
Verifies all components and configurations
"""

import os
import subprocess
import sys
from pathlib import Path

def check_requirement(name, check_func, fix_func=None):
    """Check a requirement and optionally fix it."""
    print(f"Checking {name}...", end=" ")
    try:
        if check_func():
            print("✅")
            return True
        else:
            print("❌")
            if fix_func:
                print(f"  Attempting to fix {name}...")
                if fix_func():
                    print(f"  ✅ {name} fixed")
                    return True
                else:
                    print(f"  ❌ Failed to fix {name}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def check_python_package(package):
    """Check if a Python package is installed."""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def install_python_package(package):
    """Install a Python package."""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", package], 
                      check=True, capture_output=True)
        return True
    except:
        return False

def check_amy_voice():
    """Check if Amy voice model exists."""
    amy_path = Path.home() / ".local/share/piper/voices/en_US-amy-medium.onnx"
    return amy_path.exists()

def check_piper_command():
    """Check if piper command is available."""
    try:
        result = subprocess.run(['piper', '--help'], capture_output=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def check_aplay_command():
    """Check if aplay command is available."""
    try:
        result = subprocess.run(['aplay', '--help'], capture_output=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def check_env_file():
    """Check if .env file exists with required keys."""
    env_path = Path(".env")
    if not env_path.exists():
        return False
    
    with open(env_path) as f:
        content = f.read()
        required_vars = ['OPENAI_API_KEY', 'WAKE_WORD', 'ENABLE_CHATGPT_VOICE']
        return all(var in content for var in required_vars)

def test_usb_audio():
    """Test USB audio devices."""
    try:
        # Test aplay with USB speakers
        result = subprocess.run(['aplay', '-l'], capture_output=True, text=True)
        if 'USB' in result.stdout or 'UACDemo' in result.stdout:
            return True
        return False
    except:
        return False

def main():
    """Main setup verification."""
    print("🎤 Bible Clock Voice Control Setup Verification")
    print("=" * 50)
    
    all_good = True
    
    # Check Python packages
    packages = [
        ('openai', lambda: check_python_package('openai'), 
         lambda: install_python_package('openai')),
        ('speechrecognition', lambda: check_python_package('speech_recognition'), 
         lambda: install_python_package('speechrecognition')),
        ('pyaudio', lambda: check_python_package('pyaudio'), 
         lambda: install_python_package('pyaudio')),
        ('python-dotenv', lambda: check_python_package('dotenv'), 
         lambda: install_python_package('python-dotenv')),
    ]
    
    for name, check_func, fix_func in packages:
        if not check_requirement(name, check_func, fix_func):
            all_good = False
    
    # Check system components
    system_checks = [
        ('Piper TTS command', check_piper_command),
        ('aplay command', check_aplay_command),
        ('Amy voice model', check_amy_voice),
        ('Environment file', check_env_file),
        ('USB audio devices', test_usb_audio),
    ]
    
    for name, check_func in system_checks:
        if not check_requirement(name, check_func):
            all_good = False
    
    print("\n" + "=" * 50)
    
    if all_good:
        print("✅ All requirements satisfied!")
        print("\nReady to test voice control:")
        print("python3 bible_clock_voice_complete.py")
    else:
        print("❌ Some requirements are missing.")
        print("\nPlease fix the issues above before running voice control.")
        
        print("\nQuick fixes:")
        print("• Install missing packages: pip install openai speechrecognition pyaudio python-dotenv")
        print("• Add your OpenAI API key to .env file")
        print("• Ensure Amy voice is downloaded to ~/.local/share/piper/voices/")
        print("• Check USB audio devices are connected")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()