# Bible Clock v3.0 - Deployment Guide

## Quick Start

### Development/Testing Environment
```bash
# Clone repository
git clone https://github.com/Jackal104/Bible-Clockv2.git
cd Bible-Clockv2

# Install dependencies
pip install -r requirements.txt

# Run in simulation mode
export SIMULATION_MODE=true
python main.py
```

### Raspberry Pi Production Deployment
```bash
# Clone repository
git clone https://github.com/Jackal104/Bible-Clockv2.git
cd Bible-Clockv2

# Install system dependencies
sudo apt-get update
sudo apt-get install -y espeak espeak-data alsa-utils portaudio19-dev python3-dev build-essential

# Enable hardware interfaces
sudo raspi-config
# Navigate to Interface Options → SPI → Enable
# Navigate to Interface Options → I2C → Enable (if using ReSpeaker HAT)

# Install Python dependencies
pip install -r requirements-pi.txt

# Install hardware drivers
# For E-ink display:
./scripts/setup_eink_display.sh

# For ReSpeaker HAT (optional):
./scripts/setup_respeaker.sh

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Reboot after driver installation
sudo reboot

# Run Bible Clock
python main.py
```

## Dependencies Overview

### Core Requirements (All Platforms)
- Python 3.8+
- Pillow (image processing)
- Flask (web interface)
- Requests (API calls)

### Voice Control Requirements
**System Level:**
```bash
sudo apt-get install espeak espeak-data alsa-utils
```

**Python Packages:**
- pyttsx3 (text-to-speech)
- SpeechRecognition (voice input)
- pyaudio (audio interface)

### Raspberry Pi Hardware
**System Setup:**
```bash
# Enable SPI for e-ink display
sudo raspi-config → Interface Options → SPI → Enable

# Install hardware packages
pip install RPi.GPIO spidev
```

**E-ink Display Setup:**
- Waveshare IT8951 compatible display
- Connect via SPI interface
- Default GPIO pins: RST(17), CS(8), BUSY(24)
- Driver: IT8951 library (auto-installed by setup script)
- Manual installation: `git clone https://github.com/GregDMeyer/IT8951.git && cd IT8951 && pip install .`

**ReSpeaker HAT Setup (Optional - Enhanced Voice):**
- Seeed Studio ReSpeaker 2-Mics Pi HAT
- Connects via GPIO pins (I2C + SPI)
- Driver: seeed-voicecard (auto-installed by setup script)
- Manual installation: `git clone https://github.com/respeaker/seeed-voicecard.git && cd seeed-voicecard && sudo ./install.sh`
- ALSA configuration automatically created
- Provides superior voice recognition and audio quality

### Audio Setup Verification
Test voice synthesis:
```bash
# Test espeak directly
espeak "Hello Bible Clock"

# Test Python TTS
python -c "import pyttsx3; engine = pyttsx3.init(); engine.say('Test'); engine.runAndWait()"

# Test ReSpeaker microphone (if installed)
arecord -D hw:seeedvoicecard,0 -c 2 -r 16000 -f S16_LE test.wav
```

## Environment Configuration

### Required Environment Variables
```bash
# Basic settings
SIMULATION_MODE=false          # Set to true for development
WEB_INTERFACE_ENABLED=true
ENABLE_VOICE=true

# Voice control
ENABLE_CHATGPT=true           # Requires OpenAI API key
OPENAI_API_KEY=sk-your-key-here

# Display settings
DISPLAY_WIDTH=1872
DISPLAY_HEIGHT=1404
FORCE_REFRESH_INTERVAL=3600

# Hardware pins (Raspberry Pi)
RST_PIN=17
CS_PIN=8
BUSY_PIN=24
```

### Performance Optimization (Raspberry Pi)
```bash
# Increase GPU memory split
sudo raspi-config → Advanced Options → Memory Split → 128

# Optional: Increase swap for image processing
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile  # CONF_SWAPSIZE=1024
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

## Troubleshooting

### Voice Control Issues
**Problem**: "TTS engine requires espeak"
```bash
sudo apt-get install espeak espeak-data
```

**Problem**: "No Default Input Device Available"
```bash
# Check audio devices
aplay -l
arecord -l

# Install ALSA utilities
sudo apt-get install alsa-utils
```

### Display Issues
**Problem**: "SPI device not found"
```bash
# Enable SPI
sudo raspi-config → Interface Options → SPI → Enable
sudo reboot

# Verify SPI is enabled
lsmod | grep spi
```

**Problem**: Import errors for RPi.GPIO
```bash
# Install on Raspberry Pi only
pip install RPi.GPIO spidev
```

### Performance Issues
**Problem**: High memory usage
- Reduce background image count in `images/` directory
- Lower image resolution in environment settings
- Increase swap file size

**Problem**: Slow startup
- Use faster SD card (Class 10 or better)
- Enable performance governor: `sudo cpufreq-set -g performance`

## Web Interface Access

**Local Access:**
- http://localhost:5000
- http://raspberrypi.local:5000

**Remote Access:**
- http://YOUR_PI_IP:5000
- Configure firewall if needed: `sudo ufw allow 5000`

## Service Installation (Optional)

Create systemd service for auto-start:
```bash
sudo nano /etc/systemd/system/bible-clock.service
```

```ini
[Unit]
Description=Bible Clock Display Service
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Bible-Clockv2
ExecStart=/usr/bin/python3 main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable bible-clock.service
sudo systemctl start bible-clock.service
```

## Features by Platform

| Feature | Development | Raspberry Pi | Notes |
|---------|-------------|--------------|-------|
| Web Interface | ✅ | ✅ | Full functionality |
| Bible Verses | ✅ | ✅ | Online + offline |
| Image Generation | ✅ | ✅ | All backgrounds |
| Voice Control | ⚠️ | ✅ | Requires audio setup |
| E-ink Display | ❌ | ✅ | Hardware required |
| GPIO Control | ❌ | ✅ | Pi hardware only |
| Statistics | ✅ | ✅ | Full monitoring |
| AI Integration | ✅ | ✅ | Requires API key |

**Legend:**
- ✅ Fully supported
- ⚠️ Limited support (may require additional setup)
- ❌ Not supported on this platform