#!/bin/bash
# Clean installation script for Bible Clock v3.0
# Removes unnecessary packages and configurations

echo "🧹 Bible Clock v3.0 - Clean Installation"
echo "========================================"
echo ""
echo "This will remove unnecessary packages and reset audio configuration."
echo "⚠️  This will:"
echo "   - Remove ReSpeaker HAT packages and configuration"
echo "   - Clean up old audio settings"  
echo "   - Remove unused Python packages"
echo "   - Reset to minimal required dependencies"
echo ""
read -p "Continue with clean installation? (y/N): " confirm

if [[ ! $confirm =~ ^[Yy]$ ]]; then
    echo "❌ Installation cancelled"
    exit 1
fi

echo ""
echo "🗑️  Removing unnecessary packages..."

# Remove ReSpeaker and related packages
sudo apt remove --purge -y \
    seeed-voicecard \
    pulseaudio-module-* \
    jackd2 \
    libjack-jackd2-* 2>/dev/null || true

# Keep essential audio packages
echo "📦 Ensuring essential audio packages are installed..."
sudo apt update
sudo apt install -y alsa-utils

# Clean up package cache
echo "🧽 Cleaning package cache..."
sudo apt autoremove -y
sudo apt autoclean

echo "🔧 Cleaning audio configuration..."

# Backup and remove old audio configs
if [ -f ~/.asoundrc ]; then
    mv ~/.asoundrc ~/.asoundrc.backup.$(date +%s)
    echo "✅ Backed up old ALSA configuration"
fi

if [ -d ~/.pulse ]; then
    mv ~/.pulse ~/.pulse.backup.$(date +%s)
    echo "✅ Backed up old PulseAudio configuration"
fi

# Remove ReSpeaker from boot configuration
if [ -f /boot/config.txt ]; then
    sudo cp /boot/config.txt /boot/config.txt.backup.$(date +%s)
    sudo sed -i '/dtoverlay=seeed-2mic-voicecard/d' /boot/config.txt
    echo "✅ Removed ReSpeaker HAT from boot configuration"
fi

# Kill any running audio processes
pulseaudio --kill 2>/dev/null || true
sudo pkill -f pulseaudio 2>/dev/null || true

echo "🐍 Cleaning Python environment..."

# Navigate to Bible Clock directory
if [ ! -d "Bible-Clockv2" ]; then
    echo "📥 Cloning fresh Bible Clock repository..."
    git clone https://github.com/Jackal104/Bible-Clockv2.git
    cd Bible-Clockv2
else
    cd Bible-Clockv2
    echo "📥 Updating Bible Clock repository..."
    git pull origin main
fi

# Remove old virtual environment
if [ -d "venv" ]; then
    rm -rf venv
    echo "✅ Removed old virtual environment"
fi

# Create fresh virtual environment
echo "🔧 Creating fresh Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install minimal required packages
echo "📦 Installing minimal required packages..."
pip install --upgrade pip
pip install -r requirements.txt

echo "⚙️  Configuring for clean setup..."

# Create clean .env configuration
cp .env.template .env 2>/dev/null || cp .env .env.clean.backup

# Update .env for clean USB audio setup
cat > .env << 'EOF'
# Bible Clock v3.0 - Clean Configuration

# Display Settings
DISPLAY_WIDTH=1872
DISPLAY_HEIGHT=1404
DISPLAY_ROTATION=0
DISPLAY_VCOM=-1.21
FORCE_REFRESH_INTERVAL=60

# Bible API Settings
BIBLE_API_URL=https://bible-api.com
DEFAULT_TRANSLATION=kjv
CACHE_DURATION=3600
REQUEST_TIMEOUT=15

# Voice Control Settings (USB Audio Devices)
ENABLE_VOICE=false
WAKE_WORD=bible clock
VOICE_RATE=150
VOICE_VOLUME=0.8

# Audio Input/Output Controls (To be configured by setup script)
AUDIO_INPUT_ENABLED=false
AUDIO_OUTPUT_ENABLED=false

# USB Audio Settings (Fifine K053 + Logitech Z120)
USB_AUDIO_ENABLED=false
USB_MIC_DEVICE_NAME=""
USB_SPEAKER_DEVICE_NAME=""

# System Settings
LOG_LEVEL=INFO
LOG_FILE=/var/log/bible-clock.log
MAX_LOG_SIZE=10485760
LOG_BACKUP_COUNT=3

# Memory Management
MEMORY_THRESHOLD=80
GC_INTERVAL=300

# Web Interface
WEB_ENABLED=true
WEB_PORT=5000
WEB_HOST=0.0.0.0

# Hardware Settings
SIMULATION_MODE=false
SPI_BUS=0
SPI_DEVICE=0
RST_PIN=17
CS_PIN=8
BUSY_PIN=24
EOF

echo "✅ Created clean configuration"

# Set proper permissions
chmod +x scripts/*.sh

echo ""
echo "🎉 Clean installation complete!"
echo ""
echo "📋 What was cleaned:"
echo "   ✅ Removed ReSpeaker HAT packages and configuration"
echo "   ✅ Cleaned old audio settings"
echo "   ✅ Fresh Python virtual environment"
echo "   ✅ Minimal required dependencies"
echo "   ✅ Clean .env configuration"
echo ""
echo "📱 Next steps:"
echo "   1. Connect your Fifine K053 microphone (USB)"
echo "   2. Connect your Logitech Z120 speakers (USB power + 3.5mm audio)"
echo "   3. Run device setup: ./scripts/setup_fifine_z120.sh"
echo "   4. Start Bible Clock: python main.py"
echo ""
echo "🌐 Web interface will be available at: http://bible-clock:5000"
echo ""
echo "💾 Backups created:"
ls -la *.backup.* ~/.*.backup.* /boot/*.backup.* 2>/dev/null | head -5 || echo "   (No backups needed)"

echo ""
echo "🔄 Reboot recommended to ensure clean audio state:"
echo "   sudo reboot"