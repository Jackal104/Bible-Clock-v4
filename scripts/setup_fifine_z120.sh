#!/bin/bash
# Optimized setup script for Fifine K053 microphone + Logitech Z120 speakers

echo "🎤🔊 Bible Clock Setup: Fifine K053 + Logitech Z120"
echo "=================================================="
echo ""
echo "📋 Please ensure devices are connected:"
echo "   1. Fifine K053 microphone → USB port"
echo "   2. Logitech Z120 speakers → USB power + 3.5mm audio to Pi"
echo ""
read -p "Press Enter when devices are connected..."

# Install required audio packages
echo "📦 Installing audio utilities..."
sudo apt update
sudo apt install -y alsa-utils

# Detect devices
echo "🔍 Detecting audio devices..."
echo ""

# Find Fifine microphone
FIFINE_CARD=$(arecord -l 2>/dev/null | grep -i "fifine\|k053" | head -1 | sed 's/card \([0-9]\).*/\1/' || echo "")

# Find Pi audio output (for Z120 speakers)
PI_AUDIO_CARD=$(aplay -l 2>/dev/null | grep -E "(bcm2835|Headphones)" | head -1 | sed 's/card \([0-9]\).*/\1/' || echo "0")

# Report findings
if [ -n "$FIFINE_CARD" ]; then
    FIFINE_NAME=$(arecord -l 2>/dev/null | grep "card $FIFINE_CARD" | head -1 | sed 's/.*: \([^[]*\).*/\1/' | tr -d ' ')
    echo "✅ Fifine K053 microphone detected:"
    echo "   Card: $FIFINE_CARD ($FIFINE_NAME)"
else
    echo "❌ Fifine K053 microphone not detected"
    echo "   Available recording devices:"
    arecord -l 2>/dev/null | grep "card" || echo "   No recording devices found"
    echo ""
    echo "Troubleshooting:"
    echo "   1. Check USB connection"
    echo "   2. Try different USB port"
    echo "   3. Run: lsusb | grep -i fifine"
    echo ""
    read -p "Continue anyway? (y/N): " continue_setup
    if [[ ! $continue_setup =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "📊 Logitech Z120 speakers:"
echo "   Using Pi 3.5mm audio output (Card $PI_AUDIO_CARD)"
echo "   Ensure Z120 audio cable connected to Pi 3.5mm jack"
echo ""

# Create optimized ALSA configuration
echo "🔧 Creating audio configuration..."

if [ -n "$FIFINE_CARD" ]; then
    # Configuration with Fifine microphone
    cat > ~/.asoundrc << EOF
# Optimized for Fifine K053 + Logitech Z120 setup

pcm.!default {
    type asym
    playback.pcm "z120_output"
    capture.pcm "fifine_input"
}

pcm.fifine_input {
    type plug
    slave {
        pcm "hw:$FIFINE_CARD,0"
        rate 48000
        channels 1
        format S16_LE
        buffer_time 100000
        period_time 20000
    }
    hint {
        show on
        description "Fifine K053 USB Microphone"
    }
}

pcm.z120_output {
    type plug
    slave {
        pcm "hw:$PI_AUDIO_CARD,0"  
        rate 44100
        channels 2
        format S16_LE
        buffer_time 100000
        period_time 20000
    }
    hint {
        show on
        description "Pi Audio for Z120 Speakers"
    }
}

ctl.!default {
    type hw
    card $FIFINE_CARD
}
EOF
else
    # Fallback configuration without microphone
    cat > ~/.asoundrc << EOF
# Fallback audio configuration

pcm.!default {
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
    card $PI_AUDIO_CARD
}
EOF
fi

echo "✅ Created ALSA configuration"

# Configure Pi audio output for 3.5mm jack
echo "🔌 Configuring Pi audio output..."
amixer cset numid=3 1 2>/dev/null  # Force 3.5mm output
amixer set Master 75% 2>/dev/null  # Set reasonable volume

# Update Bible Clock configuration
if [ -f .env ]; then
    echo "📝 Updating Bible Clock configuration..."
    
    # Enable USB audio
    sed -i "s/USB_AUDIO_ENABLED=false/USB_AUDIO_ENABLED=true/" .env
    
    if [ -n "$FIFINE_CARD" ]; then
        # Configure for Fifine microphone
        sed -i "s/USB_MIC_DEVICE_NAME=\"\"/USB_MIC_DEVICE_NAME=\"Fifine_K053\"/" .env
        sed -i "s/AUDIO_INPUT_ENABLED=false/AUDIO_INPUT_ENABLED=true/" .env
        sed -i "s/ENABLE_VOICE=false/ENABLE_VOICE=true/" .env
    fi
    
    # Configure for Z120 speakers
    sed -i "s/USB_SPEAKER_DEVICE_NAME=\"\"/USB_SPEAKER_DEVICE_NAME=\"Logitech_Z120\"/" .env
    sed -i "s/AUDIO_OUTPUT_ENABLED=false/AUDIO_OUTPUT_ENABLED=true/" .env
    
    # Set to hardware mode (disable simulation)
    sed -i "s/SIMULATION_MODE=true/SIMULATION_MODE=false/" .env
    
    echo "✅ Updated Bible Clock configuration"
fi

# Test audio setup
echo ""
echo "🧪 Testing audio setup..."

if [ -n "$FIFINE_CARD" ]; then
    echo "Testing Fifine K053 microphone (3 seconds)..."
    echo "Please speak into the microphone..."
    
    if timeout 4 arecord -D fifine_input -f S16_LE -r 48000 -c 1 -t wav -d 3 test_fifine.wav 2>/dev/null; then
        echo "✅ Fifine K053 recording successful"
        
        # Test playback through Z120
        echo "Testing Z120 speaker playback..."
        if timeout 4 aplay -D z120_output test_fifine.wav 2>/dev/null; then
            echo "✅ Z120 speaker playback successful"
            echo "🎉 Audio test complete - you should have heard your voice!"
        else
            echo "❌ Z120 speaker playback failed"
            echo "   Check 3.5mm cable connection to Pi audio jack"
        fi
    else
        echo "❌ Fifine K053 recording failed"
        echo "   Check USB connection and microphone positioning"
    fi
else
    echo "⚠️  Skipping microphone test (device not detected)"
    
    # Test speaker output with tone
    echo "Testing Z120 speakers with test tone..."
    if timeout 3 speaker-test -D z120_output -c 2 -r 44100 -s 1 2>/dev/null; then
        echo "✅ Z120 speaker test successful"
    else
        echo "❌ Z120 speaker test failed"
    fi
fi

# Clean up test files
rm -f test_fifine.wav

echo ""
echo "🎉 Setup complete!"
echo "📋 Configuration summary:"
if [ -n "$FIFINE_CARD" ]; then
    echo "   🎤 Fifine K053: Card $FIFINE_CARD (48kHz, mono)"
fi
echo "   🔊 Z120 Speakers: Pi 3.5mm output (44.1kHz, stereo)"
echo ""
echo "📱 Volume controls:"
echo "   Hardware: Z120 volume knob"
echo "   Software: alsamixer or Bible Clock web interface"
echo ""
echo "🚀 Start Bible Clock:"
echo "   python main.py"
echo ""
echo "🌐 Web interface will be available at:"
echo "   http://bible-clock:5000"
echo ""

if [ -n "$FIFINE_CARD" ]; then
    echo "🎙️  Voice Commands (say 'bible clock' to activate):"
    echo ""
    echo "📖 Display Control:"
    echo "   'speak verse' - Read current verse aloud"
    echo "   'refresh display' - Get new verse"
    echo "   'change background' - Switch background style"
    echo "   'change mode' - Switch between time/date/random modes"
    echo "   'time mode' - Time-based verses"
    echo "   'date mode' - Biblical calendar events"
    echo "   'random mode' - Random inspiration"
    echo ""
    echo "ℹ️  Information:"
    echo "   'what time is it' - Current time"
    echo "   'system status' - Health report"
    echo "   'current verse' - What's displayed"
    echo "   'current mode' - Active display mode"
    echo "   'current translation' - Bible version"
    echo ""
    echo "❓ Biblical Questions (ChatGPT):"
    echo "   'What does this verse mean?'"
    echo "   'Who was King David?'"
    echo "   'Explain the parable of...'"
    echo "   'Help me understand this passage'"
    echo "   'Tell me about biblical love'"
    echo ""
    echo "🆘 Help:"
    echo "   'help' - Complete command overview"
    echo "   'help display' - Display commands"
    echo "   'help questions' - How to ask biblical questions"
    echo "   'help examples' - Question examples"
fi