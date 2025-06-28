#!/bin/bash
# Fix ReSpeaker HAT audio configuration

echo "🔧 Fixing ReSpeaker HAT audio configuration..."

# Create proper ALSA configuration for ReSpeaker
cat > ~/.asoundrc << 'EOF'
# ReSpeaker 2-Mic Hat ALSA Configuration

pcm.!default {
    type asym
    playback.pcm "respeaker_playback"
    capture.pcm "respeaker_capture"
}

pcm.respeaker_playback {
    type plug
    slave {
        pcm "hw:2,0"
        rate 48000
        channels 2
        format S16_LE
    }
}

pcm.respeaker_capture {
    type plug
    slave {
        pcm "hw:2,0"
        rate 48000
        channels 2
        format S16_LE
    }
}

ctl.!default {
    type hw
    card 2
}
EOF

echo "✅ Created ReSpeaker ALSA configuration"

# Set up PulseAudio for ReSpeaker
mkdir -p ~/.pulse
cat > ~/.pulse/default.pa << 'EOF'
#!/usr/bin/pulseaudio -nF

# Load core modules
load-module module-device-restore
load-module module-stream-restore
load-module module-card-restore

# Load ALSA modules for ReSpeaker
load-module module-alsa-sink device=hw:2,0 sink_name=respeaker_output
load-module module-alsa-source device=hw:2,0 source_name=respeaker_input

# Set defaults
set-default-sink respeaker_output
set-default-source respeaker_input

# Load additional modules
load-module module-native-protocol-unix
EOF

echo "✅ Created PulseAudio configuration"

# Try to fix audio group permissions
sudo usermod -a -G audio $USER

echo "🎵 Testing audio with new configuration..."

# Restart PulseAudio
pulseaudio --kill 2>/dev/null || true
sleep 2
pulseaudio --start --log-target=stderr &

sleep 3

# Test with PulseAudio
echo "Testing PulseAudio recording..."
timeout 5 parecord --device=respeaker_input test_pulse.wav 2>/dev/null && echo "✅ PulseAudio recording works" || echo "❌ PulseAudio recording failed"

# Test playback
if [ -f test_pulse.wav ]; then
    echo "Testing playback..."
    timeout 5 paplay test_pulse.wav 2>/dev/null && echo "✅ PulseAudio playback works" || echo "❌ PulseAudio playback failed"
fi

echo ""
echo "🔄 If audio still doesn't work, try:"
echo "   1. sudo reboot"
echo "   2. Use USB microphone as alternative"
echo "   3. Use audio output only (TTS without voice input)"