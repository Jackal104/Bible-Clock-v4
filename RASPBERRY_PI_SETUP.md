# 📖 Bible Clock v3.0 - Raspberry Pi Hardware Setup Guide

Complete setup guide for deploying Bible Clock on Raspberry Pi with e-ink display and ReSpeaker HAT.

## 🛠️ Hardware Requirements

### Required Components
- **Raspberry Pi 4B** (2GB+ RAM recommended)
- **MicroSD Card** (32GB+ Class 10)
- **E-ink Display** (IT8951 controller, 1872x1404 resolution)
- **Power Supply** (5V 3A USB-C for Pi)
- **Jumper Wires** for GPIO connections

### Optional Components
- **ReSpeaker 2-Mics Pi HAT** (for enhanced voice control)
- **Speakers/Headphones** (3.5mm jack or USB)
- **Case** (with cutouts for display and HAT)

## 🔌 Hardware Connection Guide

### E-ink Display Wiring (SPI)
Connect the e-ink display to Raspberry Pi GPIO pins:

```
E-ink Display → Raspberry Pi GPIO
VCC           → Pin 2  (5V)
GND           → Pin 6  (Ground)
DIN           → Pin 19 (SPI0 MOSI)
CLK           → Pin 23 (SPI0 SCLK)
CS            → Pin 24 (GPIO 8)
DC            → Pin 18 (GPIO 24) 
RST           → Pin 11 (GPIO 17)
BUSY          → Pin 16 (GPIO 23)
```

### ReSpeaker HAT Installation (Optional)
1. Power off Raspberry Pi completely
2. Carefully align and press ReSpeaker HAT onto GPIO pins
3. Ensure all 40 pins are properly connected
4. The HAT will cover most GPIO pins but display wiring goes underneath

### Audio Connections
- **Built-in Audio**: 3.5mm jack on Raspberry Pi
- **ReSpeaker Audio**: 3.5mm jack on HAT (higher quality)
- **USB Audio**: Any USB audio device

## 💾 Raspberry Pi OS Setup

### 1. Flash Raspberry Pi OS
```bash
# Download Raspberry Pi Imager
# Flash Raspberry Pi OS Lite (64-bit) to SD card
# Enable SSH and configure WiFi during flashing
```

### 2. Initial System Setup
```bash
# SSH into your Pi
ssh pi@raspberrypi.local

# Update system
sudo apt update && sudo apt upgrade -y

# Configure system
sudo raspi-config
# - Enable SPI (Interface Options → SPI → Yes)
# - Enable I2C (Interface Options → I2C → Yes)
# - Expand filesystem (Advanced Options → Expand Filesystem)
# - Set timezone (Localisation Options → Timezone)
# - Reboot when prompted
```

### 3. Install Git and Clone Repository
```bash
# Install git
sudo apt install git -y

# Clone Bible Clock repository
git clone https://github.com/Jackal104/Bible-Clockv2.git
cd Bible-Clockv2
```

## 🚀 Automated Installation

### Quick Setup (Recommended)
```bash
# Run the complete setup script
chmod +x scripts/setup_bible_clock.sh
./scripts/setup_bible_clock.sh
```

The setup script will:
- ✅ Install all system dependencies
- ✅ Install Python packages
- ✅ Configure hardware interfaces
- ✅ Install e-ink display drivers
- ✅ Install ReSpeaker HAT drivers (optional)
- ✅ Configure hostname resolution
- ✅ Create configuration files
- ✅ Test installation

### Manual Installation (Advanced)
If you prefer manual control:

```bash
# 1. Install system dependencies
sudo apt install -y python3-pip python3-dev python3-venv git \
  build-essential cmake pkg-config libjpeg-dev zlib1g-dev \
  libfreetype6-dev liblcms2-dev libopenjp2-7 libtiff5 \
  espeak espeak-data alsa-utils portaudio19-dev libasound2-dev

# 2. Create virtual environment and install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements-pi.txt

# 3. Setup e-ink display drivers
./scripts/setup_eink_display.sh

# 4. Setup ReSpeaker HAT (if installed)
./scripts/setup_respeaker.sh

# 5. Configure hostname
sudo ./scripts/setup_hostname.sh
```

## ⚙️ Configuration

### 1. Environment Configuration
Edit the `.env` file created during setup:

```bash
nano .env
```

**Key Settings to Review:**
```bash
# Hardware Settings
SIMULATION_MODE=false          # Set to false for real hardware
DISPLAY_WIDTH=1872            # Match your display resolution
DISPLAY_HEIGHT=1404           # Match your display resolution

# Voice Control
ENABLE_VOICE=true             # Enable voice control
RESPEAKER_ENABLED=true        # Enable if ReSpeaker HAT installed

# ChatGPT Integration (Optional)
ENABLE_CHATGPT=true           # Enable AI assistance
OPENAI_API_KEY=your_key_here  # Add your OpenAI API key

# Web Interface
WEB_HOST=bible-clock          # Custom hostname
WEB_PORT=5000                 # Web interface port
```

### 2. Test Hardware Connections
```bash
# Activate virtual environment first
source venv/bin/activate

# Test e-ink display
python -c "
from src.display_manager import DisplayManager
dm = DisplayManager()
print('Display initialized successfully!')
"

# Test voice control (if enabled)
python -c "
from src.voice_control import VoiceControl
vc = VoiceControl(None, None)
print('Voice control initialized successfully!')
"
```

## 🔊 Audio Configuration

### For Built-in Audio
```bash
# Set audio output to 3.5mm jack
sudo raspi-config
# Advanced Options → Audio → Force 3.5mm jack
```

### For ReSpeaker HAT
The setup script configures ReSpeaker automatically. Manual configuration:

```bash
# Check ReSpeaker is detected
aplay -l | grep seeed

# Test ReSpeaker playback
speaker-test -c2 -t wav

# Test ReSpeaker recording
arecord -f cd -Dhw:1 test.wav
# Press Ctrl+C after a few seconds
aplay test.wav
```

## 🌐 Network Access

After setup, access the web interface:

- **Local access**: `http://bible-clock:5000`
- **Network access**: `http://[pi-ip-address]:5000`
- **Fallback**: `http://localhost:5000`

Find your Pi's IP address:
```bash
hostname -I
```

## 🚀 Running Bible Clock

### Start Bible Clock
```bash
cd Bible-Clockv2
# Activate virtual environment
source venv/bin/activate
# Start Bible Clock
python main.py
```

### Run as System Service (Recommended)
Create a systemd service for automatic startup:

```bash
# Create service file
sudo tee /etc/systemd/system/bible-clock.service > /dev/null << EOF
[Unit]
Description=Bible Clock v3.0
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/Bible-Clockv2
ExecStart=/home/pi/Bible-Clockv2/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl enable bible-clock.service
sudo systemctl start bible-clock.service

# Check service status
sudo systemctl status bible-clock.service
```

### Service Management Commands
```bash
# Start service
sudo systemctl start bible-clock

# Stop service
sudo systemctl stop bible-clock

# Restart service
sudo systemctl restart bible-clock

# View logs
sudo journalctl -u bible-clock -f
```

## 🎛️ Usage

### Web Interface Features
- **Dashboard**: View current verse and system status
- **Settings**: Configure display, fonts, backgrounds
- **Voice Control**: Test voice and configure ChatGPT
- **Statistics**: View usage stats and performance

### Voice Commands
Wake word: **"Bible Clock"**

**Examples:**
- "Bible Clock, speak verse" - Read current verse
- "Bible Clock, refresh display" - Update display
- "Bible Clock, help" - Voice help system
- "Bible Clock, what does this verse mean?" - AI explanation

### Display Modes
- **Time Mode**: Shows verses based on current time
- **Date Mode**: Shows verses related to today's date
- **Parallel Mode**: Shows two translations side-by-side

## 🔧 Troubleshooting

### Display Issues
```bash
# Check SPI is enabled
lsmod | grep spi

# Test SPI device
ls -la /dev/spidev0.0

# Check display initialization
tail -f /var/log/bible-clock.log | grep display
```

### Voice Control Issues
```bash
# Check audio devices
aplay -l
arecord -l

# Test espeak
espeak "Hello World"

# Check microphone
arecord -d 5 test.wav && aplay test.wav
```

### ReSpeaker HAT Issues
```bash
# Check HAT detection
dmesg | grep seeed

# Reinstall drivers
./scripts/setup_respeaker.sh

# Check ALSA configuration
cat /proc/asound/cards
```

### Service Issues
```bash
# View detailed logs
sudo journalctl -u bible-clock -n 50

# Check service status
sudo systemctl status bible-clock

# Restart service
sudo systemctl restart bible-clock
```

### Performance Optimization
```bash
# Check system resources
htop

# Monitor memory usage
free -h

# Check disk space
df -h

# Optimize for low memory
echo 'gpu_mem=16' | sudo tee -a /boot/config.txt
```

## 📚 Advanced Configuration

### Custom Backgrounds
Add your own background images:
```bash
# Copy images to backgrounds directory
cp your_image.jpg images/backgrounds/

# Images should be 1872x1404 for best results
```

### Custom Fonts
Add additional fonts:
```bash
# Copy font files to fonts directory
cp your_font.ttf fonts/

# Update font configuration in web interface
```

### API Configuration
For custom Bible API:
```bash
# Edit .env file
BIBLE_API_URL=https://your-api.com
```

## 🔒 Security

### Firewall Configuration
```bash
# Install UFW
sudo apt install ufw

# Allow SSH
sudo ufw allow ssh

# Allow web interface
sudo ufw allow 5000

# Enable firewall
sudo ufw enable
```

### Regular Updates
```bash
# Create update script
tee ~/update_bible_clock.sh > /dev/null << 'EOF'
#!/bin/bash
cd ~/Bible-Clockv2
git pull origin main
pip3 install -r requirements-pi.txt --upgrade
sudo systemctl restart bible-clock
EOF

chmod +x ~/update_bible_clock.sh

# Run monthly via cron
echo "0 2 1 * * ~/update_bible_clock.sh" | crontab -
```

## 📱 Remote Access

### SSH Access
```bash
# Enable SSH key authentication
ssh-copy-id pi@bible-clock.local

# Disable password authentication (optional)
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart ssh
```

### VNC Access (Optional)
```bash
# Enable VNC
sudo raspi-config
# Interface Options → VNC → Yes

# Access via VNC Viewer: bible-clock.local:5900
```

## 📊 Monitoring

### System Health
The Bible Clock includes built-in monitoring:
- CPU temperature and usage
- Memory usage
- Display refresh status
- Voice control status
- Network connectivity

Access monitoring at: `http://bible-clock:5000/statistics`

### Log Management
```bash
# View application logs
tail -f bible_clock.log

# Rotate logs automatically (configured in .env)
LOG_FILE=/var/log/bible-clock.log
MAX_LOG_SIZE=10485760
LOG_BACKUP_COUNT=3
```

## 🎯 Final Steps

1. **Test all features** via web interface
2. **Configure voice control** and test with sample commands
3. **Set up automatic startup** with systemd service
4. **Configure remote access** if needed
5. **Schedule regular updates** via cron
6. **Document your configuration** for future reference

## 🆘 Support

- **Documentation**: Check `DEPLOYMENT.md` for deployment details
- **Issues**: Report problems on GitHub repository
- **Logs**: Check `/var/log/bible-clock.log` for errors
- **Status**: Monitor via web interface at `/statistics`

---

**🎉 Congratulations!** Your Bible Clock v3.0 is now ready for use. Enjoy your personalized biblical verse display with AI-powered voice assistance!