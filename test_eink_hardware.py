#!/usr/bin/env python3
"""
E-ink Display Hardware Test Script
Tests the 10.3" Waveshare e-Paper HAT connection and functionality
"""

import sys
import os
from pathlib import Path

def test_system_requirements():
    """Test system-level requirements"""
    print("🔍 Testing System Requirements")
    print("=" * 40)
    
    # Test SPI module
    try:
        import subprocess
        result = subprocess.run(['lsmod'], capture_output=True, text=True)
        if 'spi_bcm2835' in result.stdout:
            print("✅ SPI module loaded")
        else:
            print("❌ SPI module not loaded")
            print("   Run: sudo raspi-config -> Interface Options -> SPI -> Enable")
    except Exception as e:
        print(f"⚠️  Could not check SPI module: {e}")
    
    # Test /dev/spidev* existence
    spi_devices = list(Path('/dev').glob('spidev*'))
    if spi_devices:
        print(f"✅ SPI devices found: {[str(d) for d in spi_devices]}")
    else:
        print("❌ No SPI devices found in /dev/")
    
    print()

def test_python_libraries():
    """Test Python library imports"""
    print("🐍 Testing Python Libraries")
    print("=" * 40)
    
    libraries = [
        ('IT8951', 'IT8951.display'),
        ('Pillow', 'PIL.Image'),
        ('NumPy', 'numpy'),
        ('SpiDev', 'spidev'),
        ('GPIOZero', 'gpiozero')
    ]
    
    for name, module in libraries:
        try:
            __import__(module)
            print(f"✅ {name}")
        except ImportError as e:
            print(f"❌ {name}: {e}")
    
    print()

def test_gpio_access():
    """Test GPIO access permissions"""
    print("🔌 Testing GPIO Access")
    print("=" * 40)
    
    try:
        import gpiozero
        # Test basic GPIO access without actually controlling pins
        print("✅ GPIOZero import successful")
        
        # Check if running as root or in gpio group
        import subprocess
        groups = subprocess.run(['groups'], capture_output=True, text=True).stdout
        if 'gpio' in groups:
            print("✅ User is in gpio group")
        else:
            print("⚠️  User not in gpio group (may need sudo)")
            
    except Exception as e:
        print(f"❌ GPIO access test failed: {e}")
    
    print()

def test_it8951_initialization():
    """Test IT8951 display initialization"""
    print("📺 Testing IT8951 Display Initialization")
    print("=" * 40)
    
    try:
        from IT8951.display import AutoEPDDisplay
        print("✅ IT8951 AutoEPDDisplay import successful")
        
        # Try to initialize display (will fail if not connected, but we can catch that)
        try:
            print("🔌 Attempting to connect to display...")
            display = AutoEPDDisplay(vcom=-1.21)  # Using .env VCOM value
            print("✅ Display connected successfully!")
            print(f"   Resolution: {display.width}x{display.height}")
            print(f"   VCOM: {display.epd.get_vcom()}")
            
            # Test basic display operation
            print("🧪 Testing basic display operations...")
            from PIL import Image, ImageDraw, ImageFont
            
            # Create test image
            img = Image.new('L', (display.width, display.height), 255)
            draw = ImageDraw.Draw(img)
            draw.text((50, 50), "Bible Clock Hardware Test", fill=0)
            draw.text((50, 100), "If you see this, hardware is working!", fill=0)
            
            # Display test image
            display.display(img)
            print("✅ Test image displayed successfully!")
            
            return True
            
        except Exception as e:
            print(f"❌ Display connection failed: {e}")
            print("   This is expected if display is not connected")
            return False
            
    except ImportError as e:
        print(f"❌ IT8951 library not available: {e}")
        return False

def test_bible_clock_config():
    """Test Bible Clock configuration"""
    print("📖 Testing Bible Clock Configuration")
    print("=" * 40)
    
    # Check .env file
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file found")
        
        # Read relevant settings
        with open(env_file, 'r') as f:
            content = f.read()
            
        settings = {}
        for line in content.split('\n'):
            if '=' in line and not line.startswith('#'):
                key, value = line.split('=', 1)
                settings[key.strip()] = value.strip()
        
        required_settings = ['RST_PIN', 'CS_PIN', 'BUSY_PIN', 'DISPLAY_WIDTH', 'DISPLAY_HEIGHT', 'SIMULATION_MODE']
        for setting in required_settings:
            if setting in settings:
                print(f"✅ {setting}={settings[setting]}")
            else:
                print(f"❌ {setting} not found in .env")
                
    else:
        print("❌ .env file not found")
    
    print()

def main():
    """Run all hardware tests"""
    print("🧪 Bible Clock E-ink Hardware Test")
    print("=" * 50)
    print()
    
    # Change to script directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Run tests
    test_system_requirements()
    test_python_libraries() 
    test_gpio_access()
    test_bible_clock_config()
    
    # The main hardware test
    hardware_working = test_it8951_initialization()
    
    print("📋 Test Summary")
    print("=" * 40)
    if hardware_working:
        print("🎉 All tests passed! E-ink display is working.")
        print("   You can now run: python main.py --hardware")
    else:
        print("⚠️  Hardware tests incomplete.")
        print("   If display is connected:")
        print("   1. Check physical connections")
        print("   2. Verify SPI is enabled: sudo raspi-config")
        print("   3. Try running with sudo: sudo python test_eink_hardware.py")
        print("   4. Reboot if SPI was just enabled")
    
    print()
    print("🔗 Waveshare Documentation:")
    print("   https://www.waveshare.com/wiki/10.3inch_e-Paper_HAT")

if __name__ == '__main__':
    main()