# Bible Clock v3.0 - Specific Device Setup Guide

## Your Chosen USB Audio Devices

### Fifine USB Lavalier Lapel Microphone (K053)
- **Model**: K053 USB Lavalier with Sound Card
- **Type**: Cardioid Condenser with built-in USB sound card
- **Compatibility**: Plug-and-play with Linux/Raspberry Pi
- **Special Features**: Built-in sound card eliminates driver needs
- **Optimal Settings**: 48kHz, 16-bit, mono input

### Logitech Z120 Compact Stereo Speakers  
- **Model**: Z120 USB-Powered Speakers
- **Power**: USB-powered (no external adapter needed)
- **Compatibility**: Standard USB Audio Class (UAC) - Linux native support
- **Output**: 1.2W RMS stereo output
- **Connection**: USB for power + 3.5mm audio jack

## Device-Specific Configuration

### Fifine K053 Setup
The K053 has a built-in USB sound card, making it appear as a complete audio interface:

```bash
# Expected device detection
# Input: Fifine K053 Microphone (USB Audio Class)
# Output: May also provide audio output capability
```

### Logitech Z120 Setup  
The Z120 speakers are USB-powered but use 3.5mm audio input:

```bash
# Power: USB port (any USB port for power)
# Audio: Connect to Pi's 3.5mm audio jack OR USB audio adapter
```

## Updated Setup Script for Your Devices

```bash
#!/bin/bash
# Device-specific setup for Fifine K053 + Logitech Z120

echo "🎤🔊 Setting up Fifine K053 + Logitech Z120"
echo "==========================================="

# Connect devices and detect
echo "📱 Please ensure devices are connected:"
echo "   1. Fifine K053 microphone → USB port"
echo "   2. Logitech Z120 speakers → USB power + 3.5mm audio"
echo ""

# Detect Fifine microphone
FIFINE_CARD=$(arecord -l | grep -i fifine | head -1 | sed 's/card \([0-9]\).*/\1/' || echo "")
PI_AUDIO_CARD=$(aplay -l | grep -E "(bcm2835|Headphones)" | head -1 | sed 's/card \([0-9]\).*/\1/' || echo "0")

if [ -n "$FIFINE_CARD" ]; then
    echo "✅ Fifine K053 microphone detected on card $FIFINE_CARD"
else
    echo "❌ Fifine K053 microphone not detected"
    echo "   Check USB connection and run: lsusb | grep -i fifine"
fi

echo "📊 Audio configuration:"
echo "   🎤 Input: Fifine K053 (Card $FIFINE_CARD)"  
echo "   🔊 Output: Pi 3.5mm + Z120 speakers (Card $PI_AUDIO_CARD)"

# Create optimized ALSA configuration
cat > ~/.asoundrc << EOF
# Optimized configuration for Fifine K053 + Logitech Z120

pcm.!default {
    type asym
    playback.pcm "pi_output"
    capture.pcm "fifine_input"
}

pcm.fifine_input {
    type plug
    slave {
        pcm "hw:$FIFINE_CARD,0"
        rate 48000
        channels 1
        format S16_LE
    }
}

pcm.pi_output {
    type plug
    slave {
        pcm "hw:$PI_AUDIO_CARD,0"
        rate 44100
        channels 2
        format S16_LE
    }
}

ctl.!default {
    type hw
    card $FIFINE_CARD
}
EOF

echo "✅ Created optimized ALSA configuration"

# Update Bible Clock configuration
if [ -f .env ]; then
    sed -i "s/USB_AUDIO_ENABLED=false/USB_AUDIO_ENABLED=true/" .env
    sed -i "s/USB_MIC_DEVICE_NAME=\"\"/USB_MIC_DEVICE_NAME=\"Fifine_K053\"/" .env
    sed -i "s/USB_SPEAKER_DEVICE_NAME=\"\"/USB_SPEAKER_DEVICE_NAME=\"Logitech_Z120\"/" .env
    sed -i "s/AUDIO_INPUT_ENABLED=false/AUDIO_INPUT_ENABLED=true/" .env
    sed -i "s/AUDIO_OUTPUT_ENABLED=false/AUDIO_OUTPUT_ENABLED=true/" .env
    sed -i "s/ENABLE_VOICE=false/ENABLE_VOICE=true/" .env
    echo "✅ Updated Bible Clock configuration"
fi

# Test setup
echo "🧪 Testing audio setup..."

# Test Fifine microphone
if [ -n "$FIFINE_CARD" ]; then
    echo "Testing Fifine K053 microphone (3 seconds)..."
    timeout 4 arecord -D fifine_input -f S16_LE -r 48000 -c 1 -t wav -d 3 test_fifine.wav 2>/dev/null && echo "✅ Fifine K053 recording works" || echo "❌ Fifine K053 recording failed"
fi

# Test speakers via Pi audio
echo "Testing Pi audio output to Z120 speakers..."
if [ -f test_fifine.wav ]; then
    timeout 4 aplay -D pi_output test_fifine.wav 2>/dev/null && echo "✅ Z120 speaker output works" || echo "❌ Z120 speaker output failed"
else
    # Generate test tone
    timeout 4 speaker-test -D pi_output -c 2 -r 44100 -s 1 2>/dev/null && echo "✅ Z120 speaker test works" || echo "❌ Z120 speaker test failed"
fi

echo ""
echo "🎉 Device-specific setup complete!"
echo "📋 Configuration summary:"
echo "   🎤 Fifine K053: 48kHz, 16-bit, mono input"
echo "   🔊 Z120 Speakers: 44.1kHz, 16-bit, stereo output via Pi 3.5mm"
echo ""
echo "🚀 Start Bible Clock: python main.py"
```

## Clean Installation Guide for Raspberry Pi

### Option 1: Fresh Raspberry Pi OS Installation

1. **Download Fresh Raspberry Pi OS**
   ```bash
   # Download Raspberry Pi Imager
   # Flash fresh Raspberry Pi OS Lite (64-bit) to SD card
   ```

2. **Initial Setup**
   ```bash
   # Enable SSH and configure WiFi during flash
   # OR manually enable after first boot:
   sudo systemctl enable ssh
   sudo raspi-config  # Configure WiFi, locale, timezone
   ```

3. **Essential System Updates**
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y git python3-pip python3-venv
   ```

4. **Clone Bible Clock**
   ```bash
   git clone https://github.com/Jackal104/Bible-Clockv2.git
   cd Bible-Clockv2
   ```

5. **Run Automated Setup**
   ```bash
   chmod +x scripts/setup_bible_clock.sh
   ./scripts/setup_bible_clock.sh
   ```

### Option 2: Clean Current Installation

1. **Remove Unnecessary Packages**
   ```bash
   # Remove ReSpeaker and audio packages you don't need
   sudo apt remove --purge -y pulseaudio* respeaker*
   sudo apt autoremove -y
   sudo apt autoclean
   ```

2. **Clean Audio Configuration**
   ```bash
   # Remove old audio configs
   rm -f ~/.asoundrc ~/.pulse/default.pa
   rm -rf ~/.pulse/
   
   # Remove ReSpeaker boot config
   sudo sed -i '/dtoverlay=seeed-2mic-voicecard/d' /boot/config.txt
   ```

3. **Update Bible Clock**
   ```bash
   cd ~/Bible-Clockv2
   git pull origin main
   ```

4. **Fresh Virtual Environment**
   ```bash
   rm -rf venv/
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

### Hardware Connection Setup

1. **Connect Devices**
   ```
   Raspberry Pi Setup:
   ┌─────────────────┐
   │  Raspberry Pi   │
   │  ┌─────────────┐│
   │  │ USB Ports   ││ ← Fifine K053 Microphone
   │  │ ┌─────────┐ ││ ← Z120 Speakers (USB power only)
   │  │ │ 3.5mm   │ ││ ← Z120 Speakers (audio cable)
   │  │ │ Audio   │ ││
   │  │ └─────────┘ ││
   │  └─────────────┘│
   │  ┌─────────────┐│ ← E-ink Display (SPI)
   │  │ GPIO Header ││
   │  └─────────────┘│
   └─────────────────┘
   ```

2. **Power Requirements**
   - **Raspberry Pi**: 5V/3A power supply (recommended)
   - **Fifine K053**: Powered via USB (low power)
   - **Z120 Speakers**: USB powered (additional ~500mA)
   - **E-ink Display**: Powered via GPIO (low power)

## Troubleshooting Your Specific Devices

### Fifine K053 Issues
```bash
# Check USB detection
lsusb | grep -i fifine

# Check audio capabilities  
cat /proc/asound/card*/stream0

# Test direct recording
arecord -D hw:CARD=K053,DEV=0 -f S16_LE -r 48000 -c 1 test.wav
```

### Logitech Z120 Issues
```bash
# Check Pi audio output
amixer cset numid=3 1  # Force 3.5mm output

# Test audio output
speaker-test -c 2 -r 44100 -D hw:0,0

# Check volume levels
alsamixer
```

### Bible Clock Voice Commands for Your Setup

**Wake Word**: "bible clock" (optimized for Fifine K053 cardioid pattern)

#### 📖 Display Control Commands
- **"speak verse"** - Read current verse aloud
- **"refresh display"** - Update with new verse  
- **"clear display"** - Clear screen to white
- **"change background"** - Switch background style
- **"cycle mode"** - Change Bible translation
- **"change mode"** - Switch time/date/random modes
- **"time mode"** - Time-based verse selection
- **"date mode"** - Biblical calendar events
- **"random mode"** - Random verse inspiration

#### ℹ️ Information Commands  
- **"what time is it"** - Current time
- **"system status"** - Health and performance report
- **"current verse"** - What verse is displayed
- **"current mode"** - Active display mode
- **"current translation"** - Bible version in use

#### ❓ Biblical Questions (ChatGPT Integration)
Ask naturally after "bible clock":
- **"What does this verse mean?"**
- **"Who was King David?"**
- **"Explain the parable of the prodigal son"**
- **"What happened in the book of Exodus?"**
- **"Help me understand this passage"**
- **"Tell me about biblical love"**
- **"Why is this verse important?"**
- **"What can I learn from this?"**
- **"What is the significance of the cross?"**
- **"How should I pray?"**

#### 🆘 Help Commands
- **"help"** - Complete command overview
- **"help display"** - Display control commands
- **"help information"** - Information commands
- **"help questions"** - How to ask biblical questions
- **"help examples"** - Question examples
- **"help setup"** - Configuration guidance

## Performance Optimization

### For Fifine K053
- **Sample Rate**: 48kHz (native)
- **Bit Depth**: 16-bit
- **Channels**: Mono (cardioid pattern)
- **Position**: 6-8 inches from mouth

### For Z120 Speakers  
- **Volume**: Set via alsamixer or Bible Clock web interface
- **Position**: Angled toward listening area
- **Connection**: Ensure 3.5mm cable fully inserted

This setup will give you excellent voice recognition with the Fifine K053's built-in sound card and clear audio output through the Z120 speakers!