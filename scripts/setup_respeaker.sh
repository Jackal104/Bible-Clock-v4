#!/bin/bash
# Bible Clock v3.0 - ReSpeaker HAT Setup Script
# Installs drivers for Seeed Studio ReSpeaker 2-Mics Pi HAT

set -e

echo "🎤 Setting up ReSpeaker HAT for Bible Clock..."

# Check if running on Raspberry Pi
if ! command -v raspi-config &> /dev/null; then
    echo "❌ This script must be run on a Raspberry Pi"
    exit 1
fi

# Enable I2C and SPI interfaces
echo "📡 Enabling I2C and SPI interfaces..."
sudo raspi-config nonint do_i2c 0
sudo raspi-config nonint do_spi 0

# Install system dependencies
echo "📦 Installing audio system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    git \
    dkms \
    alsa-utils \
    portaudio19-dev \
    python3-dev \
    build-essential \
    libasound2-dev

# Clone and install seeed-voicecard drivers
echo "🔧 Installing ReSpeaker drivers..."
cd /tmp
if [ -d "seeed-voicecard" ]; then
    rm -rf seeed-voicecard
fi

git clone https://github.com/respeaker/seeed-voicecard.git
cd seeed-voicecard
sudo ./install.sh

# Install Python audio dependencies
echo "🐍 Installing Python audio libraries..."
pip3 install pyaudio pyttsx3 SpeechRecognition

# Create ALSA configuration for ReSpeaker
echo "🔊 Configuring ALSA for ReSpeaker..."
cat > ~/.asoundrc << EOF
# ReSpeaker 2-Mics Pi HAT Configuration
pcm.!default {
  type asym
  playback.pcm {
    type plug
    slave.pcm "hw:seeedvoicecard,0"
  }
  capture.pcm {
    type plug
    slave.pcm "hw:seeedvoicecard,0"
  }
}

ctl.!default {
  type hw
  card seeedvoicecard
}
EOF

# Test audio devices
echo "🔍 Testing audio configuration..."
echo "Available audio devices:"
aplay -l | grep -E "(card|device)" || echo "No playback devices found"
echo ""
arecord -l | grep -E "(card|device)" || echo "No capture devices found"
echo ""

# Test microphone
echo "🎤 Testing microphone (you should see input levels):"
echo "Speak into the microphone for 3 seconds..."
timeout 3s arecord -D hw:seeedvoicecard,0 -c 2 -r 16000 -f S16_LE /tmp/test.wav || true
if [ -f /tmp/test.wav ]; then
    echo "✅ Microphone recording successful"
    rm /tmp/test.wav
else
    echo "⚠️  Microphone test failed - check connections"
fi

# Verify ReSpeaker detection
echo "✅ Verifying ReSpeaker detection..."
python3 -c "
import speech_recognition as sr
devices = sr.Microphone.list_microphone_names()
respeaker_found = any('respeaker' in device.lower() or 'seeed' in device.lower() for device in devices)
if respeaker_found:
    print('✅ ReSpeaker device detected')
else:
    print('⚠️  ReSpeaker device not detected in microphone list')
    print('Available microphones:')
    for i, device in enumerate(devices):
        print(f'  {i}: {device}')
"

echo ""
echo "🎉 ReSpeaker HAT setup completed!"
echo ""
echo "📝 Next steps:"
echo "1. Reboot your Raspberry Pi: sudo reboot"
echo "2. Set RESPEAKER_ENABLED=true in your .env file"
echo "3. Set ENABLE_VOICE=true in your .env file"
echo "4. Start Bible Clock: python3 main.py"
echo ""
echo "🔧 Troubleshooting:"
echo "- If no audio: Check HAT is properly seated on GPIO pins"
echo "- Test with: speaker-test -c2 -D hw:seeedvoicecard,0"
echo "- Record test: arecord -D hw:seeedvoicecard,0 -c 2 -r 16000 -f S16_LE test.wav"