#!/usr/bin/env python3
"""
40-Pin HAT Installation Guide for 10.3" E-ink Display
Simple plug-and-play installation guide
"""

def print_hat_installation():
    """Print HAT installation guide"""
    
    print("🎩 40-Pin HAT Installation for E-ink Display")
    print("=" * 50)
    print()
    print("The Waveshare 10.3\" e-Paper HAT connects directly to your Pi's")
    print("40-pin GPIO header - no individual wire connections needed!")
    print()
    
    print("📋 Installation Steps:")
    print("-" * 25)
    print("1. 🔌 Power off your Raspberry Pi COMPLETELY")
    print("   sudo shutdown -h now")
    print()
    print("2. 🔧 Align the HAT with Pi GPIO header")
    print("   • The HAT has a 40-pin female connector") 
    print("   • Match it with the Pi's 40-pin male header")
    print("   • Ensure proper orientation (Pin 1 to Pin 1)")
    print()
    print("3. 📌 Press the HAT down firmly")
    print("   • Push evenly until fully seated")
    print("   • All 40 pins should be connected")
    print("   • No gaps between HAT and Pi")
    print()
    print("4. 🖥️  Connect the e-ink display")
    print("   • Connect ribbon cable to HAT's FPC connector")
    print("   • Ensure cable is properly inserted")
    print("   • Lock the FPC connector")
    print()
    print("5. ⚡ Power on and test")
    print("   • Power on the Pi")
    print("   • Run: python test_eink_hardware.py")
    print()

def print_gpio_usage():
    """Show which GPIO pins the HAT uses"""
    
    print("📍 GPIO Pins Used by HAT:")
    print("-" * 30)
    print("The HAT automatically connects to these pins:")
    print()
    print("Power:")
    print("  • 5V Power   (Pin 2)")
    print("  • Ground     (Pin 6)")
    print()
    print("SPI Interface:")
    print("  • SPI0_MOSI  (Pin 19, GPIO 10)")
    print("  • SPI0_MISO  (Pin 21, GPIO 9)")
    print("  • SPI0_SCLK  (Pin 23, GPIO 11)")
    print("  • SPI0_CE0   (Pin 24, GPIO 8)  - Chip Select")
    print()
    print("Control Signals:")
    print("  • RST        (Pin 11, GPIO 17) - Reset")
    print("  • BUSY       (Pin 18, GPIO 24) - Ready/Busy")
    print()
    print("✅ Your .env configuration matches these pins:")
    print("   RST_PIN=17, CS_PIN=8, BUSY_PIN=24")
    print()

def print_troubleshooting():
    """Print HAT troubleshooting guide"""
    
    print("🔧 Troubleshooting HAT Installation:")
    print("-" * 40)
    print()
    print("If the display doesn't work:")
    print()
    print("🔍 Check Physical Connection:")
    print("  • HAT fully seated on GPIO header")
    print("  • No bent or missing pins")
    print("  • Ribbon cable properly connected")
    print("  • FPC connector locked")
    print()
    print("⚙️  Check Software Configuration:")
    print("  • SPI enabled: sudo raspi-config")
    print("  • Libraries installed: pip list | grep IT8951")
    print("  • Run test: python test_eink_hardware.py")
    print()
    print("⚡ Check Power:")
    print("  • Pi power supply adequate (3A recommended)")
    print("  • HAT LED indicators (if any)")
    print("  • Measure 5V on GPIO pins")
    print()
    print("📊 Check System Status:")
    print("  • SPI devices: ls /dev/spi*")
    print("  • SPI module: lsmod | grep spi")
    print("  • GPIO access: groups | grep gpio")
    print()

def print_advantages():
    """Print advantages of HAT installation"""
    
    print("🎉 Advantages of 40-Pin HAT:")
    print("-" * 35)
    print("✅ No individual wire connections")
    print("✅ Secure, reliable connection")
    print("✅ No wiring mistakes possible")
    print("✅ Professional appearance")
    print("✅ Easy to remove/reinstall")
    print("✅ All pins automatically connected")
    print("✅ Standard Raspberry Pi HAT format")
    print()

def main():
    """Display complete HAT installation guide"""
    print_hat_installation()
    print()
    print_gpio_usage()
    print()
    print_advantages()
    print()
    print_troubleshooting()
    
    print()
    print("🌐 Additional Resources:")
    print("• Waveshare Wiki: https://www.waveshare.com/wiki/10.3inch_e-Paper_HAT")
    print("• HAT Specification: https://github.com/raspberrypi/hats")
    print("• Test Hardware: python test_eink_hardware.py")
    print()
    print("🚀 After installation, run: python main.py --hardware")

if __name__ == '__main__':
    main()