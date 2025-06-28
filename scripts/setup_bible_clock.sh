#!/bin/bash
# Bible Clock v3.0 - Complete Setup Script for Raspberry Pi
# Installs all dependencies and drivers for full functionality

set -e

echo "📖 Bible Clock v3.0 - Complete Setup Script"
echo "============================================="
echo ""

# Check if running on Raspberry Pi
if ! command -v raspi-config &> /dev/null; then
    echo "❌ This script must be run on a Raspberry Pi"
    echo "For development setup, use: pip install -r requirements.txt"
    exit 1
fi

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📁 Project directory: $PROJECT_DIR"
echo ""

# Update system
echo "🔄 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install basic system dependencies
echo "📦 Installing system dependencies..."

# Try to install libtiff with fallback for different package names
TIFF_PACKAGE=""
if apt-cache show libtiff5-dev >/dev/null 2>&1; then
    TIFF_PACKAGE="libtiff5-dev"
elif apt-cache show libtiff-dev >/dev/null 2>&1; then
    TIFF_PACKAGE="libtiff-dev"
elif apt-cache show libtiff5 >/dev/null 2>&1; then
    TIFF_PACKAGE="libtiff5"
else
    echo "⚠️  Warning: Could not find libtiff package, skipping..."
fi

sudo apt-get install -y \
    python3-pip \
    python3-dev \
    python3-venv \
    git \
    build-essential \
    cmake \
    pkg-config \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libopenjp2-7 \
    $TIFF_PACKAGE \
    espeak \
    espeak-data \
    alsa-utils \
    portaudio19-dev \
    libasound2-dev

echo "✅ System dependencies installed"
echo ""

# Enable hardware interfaces
echo "🔧 Enabling hardware interfaces..."
sudo raspi-config nonint do_spi 0
sudo raspi-config nonint do_i2c 0
echo "✅ SPI and I2C enabled"
echo ""

# Install Python dependencies in virtual environment
echo "🐍 Setting up Python virtual environment..."
cd "$PROJECT_DIR"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ Virtual environment created"
else
    echo "ℹ️  Virtual environment already exists"
fi

# Activate virtual environment and install dependencies
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-pi.txt
echo "✅ Python dependencies installed in virtual environment"
echo ""

# Prompt for hardware setup
echo "🛠️  Hardware Setup Options:"
echo "1. E-ink Display (IT8951) - Required for display output"
echo "2. ReSpeaker HAT - Optional, enhances voice control"
echo ""

read -p "Install E-ink display drivers? [Y/n]: " install_eink
install_eink=${install_eink:-Y}

if [[ $install_eink =~ ^[Yy] ]]; then
    echo "🖥️  Installing E-ink display drivers..."
    "$SCRIPT_DIR/setup_eink_display.sh"
    echo "✅ E-ink display setup completed"
    echo ""
fi

read -p "Install ReSpeaker HAT drivers? [y/N]: " install_respeaker
install_respeaker=${install_respeaker:-N}

if [[ $install_respeaker =~ ^[Yy] ]]; then
    echo "🎤 Installing ReSpeaker HAT drivers..."
    "$SCRIPT_DIR/setup_respeaker.sh"
    echo "✅ ReSpeaker HAT setup completed"
    echo ""
fi

# Create environment file if it doesn't exist
echo "⚙️  Setting up configuration..."
if [ ! -f "$PROJECT_DIR/.env" ]; then
    cat > "$PROJECT_DIR/.env" << EOF
# Bible Clock v3.0 Configuration
# Basic Settings
SIMULATION_MODE=false
WEB_INTERFACE_ENABLED=true
WEB_HOST=bible-clock
WEB_PORT=5000
ENABLE_VOICE=true

# Display Settings
DISPLAY_WIDTH=1872
DISPLAY_HEIGHT=1404
DISPLAY_ROTATION=0
DISPLAY_VCOM=-1.21
FORCE_REFRESH_INTERVAL=3600

# Voice Control
WAKE_WORD=bible clock
VOICE_RATE=150
VOICE_VOLUME=0.8
VOICE_HELP_ENABLED=true

# ReSpeaker HAT (if installed)
RESPEAKER_ENABLED=true
RESPEAKER_CHANNELS=6
RESPEAKER_SAMPLE_RATE=16000
FORCE_RESPEAKER_OUTPUT=true

# ChatGPT Integration (optional)
ENABLE_CHATGPT=false
# OPENAI_API_KEY=your_openai_api_key_here

# Hardware GPIO Pins
RST_PIN=17
CS_PIN=8
BUSY_PIN=24

# Performance
PERFORMANCE_MONITORING=true
LOG_LEVEL=INFO
EOF
    echo "✅ Configuration file created: .env"
else
    echo "ℹ️  Configuration file already exists: .env"
fi
echo ""

# Test installation
echo "🧪 Testing installation..."

# Test Python imports
echo "📦 Testing Python dependencies..."
python3 -c "
import sys
missing = []
try:
    import PIL
    from PIL import Image
    print('✅ Pillow (image processing)')
except ImportError:
    missing.append('Pillow')

try:
    import requests
    print('✅ Requests (API calls)')
except ImportError:
    missing.append('requests')

try:
    import flask
    print('✅ Flask (web interface)')
except ImportError:
    missing.append('flask')

try:
    import RPi.GPIO
    print('✅ RPi.GPIO (hardware control)')
except ImportError:
    missing.append('RPi.GPIO')

try:
    import spidev
    print('✅ SpiDev (SPI communication)')
except ImportError:
    missing.append('spidev')

try:
    import pyttsx3
    print('✅ pyttsx3 (text-to-speech)')
except ImportError:
    missing.append('pyttsx3')

try:
    import speech_recognition
    print('✅ SpeechRecognition (voice input)')
except ImportError:
    missing.append('speech_recognition')

if missing:
    print(f'❌ Missing dependencies: {missing}')
    sys.exit(1)
"

# Test hardware interfaces
echo ""
echo "🔍 Testing hardware interfaces..."
if [ -e /dev/spidev0.0 ]; then
    echo "✅ SPI interface available"
else
    echo "⚠️  SPI interface not found"
fi

if [ -e /dev/i2c-1 ]; then
    echo "✅ I2C interface available"
else
    echo "⚠️  I2C interface not found"
fi

# Test audio
echo ""
echo "🔊 Testing audio system..."
if command -v espeak &> /dev/null; then
    echo "✅ espeak installed"
    echo "🎵 Testing voice synthesis..."
    espeak -s 150 "Bible Clock setup completed successfully" 2>/dev/null || echo "⚠️  espeak test failed"
else
    echo "❌ espeak not found"
fi

# Setup hostname resolution
echo "🌐 Setting up hostname resolution..."
if command -v sudo &> /dev/null; then
    "$SCRIPT_DIR/setup_hostname.sh" 2>/dev/null || echo "⚠️  Hostname setup requires manual configuration"
else
    echo "⚠️  Hostname setup requires sudo privileges - run setup_hostname.sh separately"
fi
echo ""

echo "🎉 Bible Clock setup completed!"
echo ""
echo "📋 Next Steps:"
echo "1. Review configuration in .env file"
echo "2. Add your OpenAI API key (optional) for ChatGPT features"
echo "3. Connect your hardware:"
if [[ $install_eink =~ ^[Yy] ]]; then
    echo "   - E-ink display via SPI (RST:17, CS:8, BUSY:24)"
fi
if [[ $install_respeaker =~ ^[Yy] ]]; then
    echo "   - ReSpeaker HAT on GPIO pins"
fi
echo "4. Reboot: sudo reboot"
echo "5. Start Bible Clock: python3 main.py"
echo ""
echo "🌐 Web interface will be available at:"
echo "   http://bible-clock:5000"
echo "   http://localhost:5000"
echo "   http://$(hostname).local:5000"
echo "   http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "📚 For troubleshooting, see DEPLOYMENT.md"