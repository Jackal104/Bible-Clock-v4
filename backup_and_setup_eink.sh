#!/bin/bash
# Bible Clock v3 - Backup and E-ink Display Setup Script
# Based on Waveshare 10.3inch e-Paper HAT documentation

set -e

echo "📖 Bible Clock v3 - Backup and E-ink Setup"
echo "=========================================="

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

BACKUP_DIR="/home/admin/Bible-Clock-v3-backup-$(date +%Y%m%d_%H%M%S)"
TEMP_DIR="/tmp/eink_setup"

echo "🗂️  Creating backup at: $BACKUP_DIR"

# Create comprehensive backup
mkdir -p "$BACKUP_DIR"
cp -r /home/admin/Bible-Clock-v3/* "$BACKUP_DIR/"

# Also backup important system files
mkdir -p "$BACKUP_DIR/system_backup"
cp /boot/config.txt "$BACKUP_DIR/system_backup/" 2>/dev/null || echo "Note: /boot/config.txt not accessible"
cp /etc/modules "$BACKUP_DIR/system_backup/" 2>/dev/null || echo "Note: /etc/modules not accessible"

echo "✅ Backup completed"

echo ""
echo "🔧 Setting up E-ink Display Drivers"
echo "==================================="

# Check if SPI is enabled
echo "📋 Checking SPI configuration..."
if lsmod | grep -q spi_bcm2835; then
    echo "✅ SPI module is loaded"
else
    echo "❌ SPI module not loaded - will enable SPI"
fi

# Create temp directory for downloads
mkdir -p "$TEMP_DIR"
cd "$TEMP_DIR"

echo ""
echo "📦 Installing system dependencies..."

# Update package list
sudo apt-get update

# Install required packages
sudo apt-get install -y \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    build-essential \
    wget \
    unzip \
    p7zip-full \
    git

echo ""
echo "🔌 Checking Raspberry Pi model..."
PI_MODEL=$(cat /proc/cpuinfo | grep "Model" | head -n1)
echo "Detected: $PI_MODEL"

# Install appropriate GPIO library based on Pi model
if echo "$PI_MODEL" | grep -q "Raspberry Pi 5"; then
    echo "📦 Installing lg library for Pi 5..."
    if [ ! -f "/usr/local/lib/liblg.so" ]; then
        wget https://github.com/joan2937/lg/archive/master.zip -O lg-master.zip
        unzip lg-master.zip
        cd lg-master
        make
        sudo make install
        cd ..
        echo "✅ lg library installed"
    else
        echo "✅ lg library already installed"
    fi
else
    echo "📦 Installing BCM2835 library for Pi 4 and earlier..."
    if [ ! -f "/usr/local/lib/libbcm2835.a" ]; then
        wget http://www.airspayce.com/mikem/bcm2835/bcm2835-1.60.tar.gz
        tar zxvf bcm2835-1.60.tar.gz
        cd bcm2835-1.60
        ./configure
        make
        sudo make check
        sudo make install
        cd ..
        echo "✅ BCM2835 library installed"
    else
        echo "✅ BCM2835 library already installed"
    fi
fi

echo ""
echo "🐍 Installing Python e-ink libraries..."

# Return to Bible Clock directory
cd "$SCRIPT_DIR"
source venv/bin/activate

# Install IT8951 library and dependencies
pip install --upgrade pip
pip install IT8951
pip install Pillow
pip install numpy
pip install spidev
pip install gpiozero

echo "✅ Python libraries installed"

echo ""
echo "⚙️  Configuring SPI interface..."

# Enable SPI if not already enabled
if ! grep -q "dtparam=spi=on" /boot/config.txt; then
    echo "Adding SPI configuration to /boot/config.txt..."
    echo "dtparam=spi=on" | sudo tee -a /boot/config.txt
    SPI_MODIFIED=1
else
    echo "✅ SPI already enabled in /boot/config.txt"
fi

# For lg library support (Pi 5), add spi0-0cs overlay
if echo "$PI_MODEL" | grep -q "Raspberry Pi 5"; then
    if ! grep -q "dtoverlay=spi0-0cs" /boot/config.txt; then
        echo "Adding Pi 5 SPI overlay to /boot/config.txt..."
        echo "dtoverlay=spi0-0cs" | sudo tee -a /boot/config.txt
        SPI_MODIFIED=1
    else
        echo "✅ Pi 5 SPI overlay already configured"
    fi
fi

echo ""
echo "🧪 Testing e-ink library installation..."

# Test IT8951 import
python3 -c "
try:
    from IT8951.display import AutoEPDDisplay
    print('✅ IT8951 library import successful')
except ImportError as e:
    print(f'❌ IT8951 library import failed: {e}')
    exit(1)
except Exception as e:
    print(f'⚠️  IT8951 library imported but may need hardware: {e}')
"

echo ""
echo "📋 E-ink Display Setup Summary"
echo "=============================="
echo "40-Pin HAT Installation Guide:"
echo ""
echo "🔌 Hardware Installation:"
echo "  1. Power off your Raspberry Pi completely"
echo "  2. Carefully align the 40-pin HAT connector with Pi GPIO header"
echo "  3. Press down firmly until HAT is fully seated"
echo "  4. Ensure all 40 pins are properly connected"
echo "  5. Connect the e-ink display ribbon cable to the HAT"
echo "  6. Power on the Pi"
echo ""
echo "✅ The HAT uses these GPIO pins automatically:"
echo "    RST  = GPIO 17 (Pin 11)"
echo "    CS   = GPIO 8  (Pin 24)"
echo "    BUSY = GPIO 24 (Pin 18)"
echo "    SPI0 MOSI, MISO, SCLK (Pins 19, 21, 23)"
echo ""
echo "Your .env configuration:"
echo "  RST_PIN=17"
echo "  CS_PIN=8" 
echo "  BUSY_PIN=24"
echo "  SPI_BUS=0"
echo "  SPI_DEVICE=0"
echo ""

if [ "$SPI_MODIFIED" = "1" ]; then
    echo "⚠️  REBOOT REQUIRED: SPI configuration was modified"
    echo "   Run: sudo reboot"
    echo ""
fi

echo "📝 Next Steps:"
echo "1. Connect the e-ink display following the pin guide above"
echo "2. If SPI was modified, reboot the Pi: sudo reboot"
echo "3. Test the display: python main.py --hardware"
echo "4. Check for hardware mode in web interface"
echo ""
echo "🗂️  Backup saved to: $BACKUP_DIR"

# Cleanup temp directory
rm -rf "$TEMP_DIR"

echo "✅ Setup complete!"