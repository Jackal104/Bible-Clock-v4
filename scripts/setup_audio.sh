#!/bin/bash
# Setup audio system for ReSpeaker HAT on Raspberry Pi

echo "🔊 Setting up audio system for Bible Clock..."
echo "=============================================="

echo "📦 Installing ALSA utilities and audio tools..."
sudo apt update
sudo apt install -y alsa-utils pulseaudio pulseaudio-utils

echo "🔧 Configuring audio for ReSpeaker HAT..."

# Enable I2S audio overlay in boot config
if ! grep -q "dtparam=i2s=on" /boot/config.txt; then
    echo "dtparam=i2s=on" | sudo tee -a /boot/config.txt
    echo "✅ Enabled I2S audio interface"
fi

# Add ReSpeaker HAT overlay if not present
if ! grep -q "dtoverlay=seeed-2mic-voicecard" /boot/config.txt; then
    echo "dtoverlay=seeed-2mic-voicecard" | sudo tee -a /boot/config.txt
    echo "✅ Added ReSpeaker HAT device tree overlay"
fi

echo "🎵 Loading audio modules..."
sudo modprobe snd_soc_seeed_voicecard 2>/dev/null || echo "⚠️  ReSpeaker module not available yet (needs reboot)"
sudo modprobe snd_soc_wm8960 2>/dev/null || echo "⚠️  WM8960 codec module not available yet (needs reboot)"

echo "🔊 Setting up ALSA configuration..."
# Create ALSA config for ReSpeaker
cat > ~/.asoundrc << 'EOF'
pcm.!default {
    type asym
    playback.pcm "plughw:1,0"
    capture.pcm "plughw:1,0"
}

ctl.!default {
    type hw
    card 1
}
EOF

echo "✅ Created ALSA configuration for ReSpeaker HAT"

echo "🎚️  Testing audio system..."
if command -v arecord &> /dev/null; then
    echo "✅ ALSA recording tools installed"
    arecord -l 2>/dev/null | head -10 || echo "⚠️  No recording devices found (may need reboot)"
else
    echo "❌ ALSA tools not found"
fi

echo ""
echo "🔄 IMPORTANT: Reboot required to activate ReSpeaker HAT"
echo "   Run: sudo reboot"
echo ""
echo "After reboot, test with:"
echo "   ./quick_mic_test.sh"
echo "   python test_microphone.py"