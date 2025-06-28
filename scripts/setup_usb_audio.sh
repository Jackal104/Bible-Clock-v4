#!/bin/bash
# Setup USB audio devices for Bible Clock
# Run this AFTER connecting USB microphone and speaker

echo "🎤🔊 USB Audio Setup for Bible Clock"
echo "===================================="

echo "📋 Detecting USB audio devices..."

# List all audio devices
echo "Available audio devices:"
aplay -l
echo ""
arecord -l
echo ""

echo "📱 USB audio devices found:"
lsusb | grep -i audio || echo "No USB audio devices detected"
echo ""

# Auto-detect USB audio devices
USB_SPEAKERS=$(aplay -l | grep -i usb | head -1 | sed 's/card \([0-9]\).*/\1/' || echo "")
USB_MIC=$(arecord -l | grep -i usb | head -1 | sed 's/card \([0-9]\).*/\1/' || echo "")

if [ -n "$USB_SPEAKERS" ]; then
    echo "✅ USB Speaker detected on card $USB_SPEAKERS"
    USB_SPEAKER_NAME=$(aplay -l | grep "card $USB_SPEAKERS" | head -1 | sed 's/.*: \([^[]*\).*/\1/' | tr -d ' ')
else
    echo "❌ No USB speakers detected"
fi

if [ -n "$USB_MIC" ]; then
    echo "✅ USB Microphone detected on card $USB_MIC"
    USB_MIC_NAME=$(arecord -l | grep "card $USB_MIC" | head -1 | sed 's/.*: \([^[]*\).*/\1/' | tr -d ' ')
else
    echo "❌ No USB microphones detected"
fi

echo ""

if [ -n "$USB_SPEAKERS" ] || [ -n "$USB_MIC" ]; then
    echo "🔧 Creating USB audio configuration..."
    
    # Create ALSA configuration for USB devices
    cat > ~/.asoundrc << EOF
# USB Audio Configuration for Bible Clock

pcm.!default {
    type asym
EOF

    if [ -n "$USB_SPEAKERS" ]; then
        cat >> ~/.asoundrc << EOF
    playback.pcm "plughw:$USB_SPEAKERS,0"
EOF
    else
        cat >> ~/.asoundrc << EOF
    playback.pcm "plughw:0,0"
EOF
    fi

    if [ -n "$USB_MIC" ]; then
        cat >> ~/.asoundrc << EOF
    capture.pcm "plughw:$USB_MIC,0"
EOF
    else
        cat >> ~/.asoundrc << EOF
    capture.pcm "plughw:0,0"
EOF
    fi

    cat >> ~/.asoundrc << EOF
}

ctl.!default {
    type hw
    card 0
}
EOF

    echo "✅ Created ALSA configuration"

    # Update Bible Clock .env configuration
    echo "📝 Updating Bible Clock configuration..."
    
    if [ -f .env ]; then
        # Update USB audio settings
        sed -i "s/USB_AUDIO_ENABLED=false/USB_AUDIO_ENABLED=true/" .env
        
        if [ -n "$USB_MIC_NAME" ]; then
            sed -i "s/USB_MIC_DEVICE_NAME=\"\"/USB_MIC_DEVICE_NAME=\"$USB_MIC_NAME\"/" .env
            sed -i "s/AUDIO_INPUT_ENABLED=false/AUDIO_INPUT_ENABLED=true/" .env
        fi
        
        if [ -n "$USB_SPEAKER_NAME" ]; then
            sed -i "s/USB_SPEAKER_DEVICE_NAME=\"\"/USB_SPEAKER_DEVICE_NAME=\"$USB_SPEAKER_NAME\"/" .env
            sed -i "s/AUDIO_OUTPUT_ENABLED=false/AUDIO_OUTPUT_ENABLED=true/" .env
        fi
        
        if [ -n "$USB_MIC" ] && [ -n "$USB_SPEAKERS" ]; then
            sed -i "s/ENABLE_VOICE=false/ENABLE_VOICE=true/" .env
        fi
        
        echo "✅ Updated Bible Clock configuration"
    fi

    echo ""
    echo "🧪 Testing USB audio..."
    
    if [ -n "$USB_MIC" ]; then
        echo "Testing USB microphone (5 seconds)..."
        timeout 6 arecord -D plughw:$USB_MIC,0 -f cd -t wav -d 5 usb_mic_test.wav 2>/dev/null && echo "✅ USB microphone works" || echo "❌ USB microphone failed"
    fi
    
    if [ -n "$USB_SPEAKERS" ] && [ -f usb_mic_test.wav ]; then
        echo "Testing USB speaker playback..."
        timeout 6 aplay -D plughw:$USB_SPEAKERS,0 usb_mic_test.wav 2>/dev/null && echo "✅ USB speakers work" || echo "❌ USB speakers failed"
    fi

    echo ""
    echo "🎉 USB audio setup complete!"
    echo "📋 Configuration:"
    [ -n "$USB_SPEAKERS" ] && echo "   🔊 USB Speaker: Card $USB_SPEAKERS ($USB_SPEAKER_NAME)"
    [ -n "$USB_MIC" ] && echo "   🎤 USB Microphone: Card $USB_MIC ($USB_MIC_NAME)"
    echo ""
    echo "🚀 Start Bible Clock with: python main.py"
    
else
    echo "❌ No USB audio devices detected!"
    echo "📋 Please:"
    echo "   1. Connect USB microphone and/or speaker"
    echo "   2. Wait a few seconds for recognition"
    echo "   3. Run this script again"
fi