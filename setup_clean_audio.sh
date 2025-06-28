#!/bin/bash
# Clean Audio Setup for Bible Clock v3.0
# Optimized for Fifine K053 USB Microphone + USB Mini Speaker (30mm driver, 2 channels)
# This script removes conflicting configurations and sets up optimal audio

set -e

echo "🎵 Bible Clock Clean Audio Setup"
echo "================================="
echo "Target Hardware:"
echo "  📱 Fifine K053 USB Microphone (cardioid, 48kHz)"
echo "  🔊 USB Mini Speaker (30mm driver, 2 channels, pure USB audio)"
echo ""

# Get the current user (will be 'admin' on Pi) 
CURRENT_USER=${USER:-$(whoami)}
if [ "$CURRENT_USER" = "root" ]; then
    # If running as root, use the actual logged-in user
    CURRENT_USER=${SUDO_USER:-admin}
fi
USER_HOME="/home/$CURRENT_USER"

echo "🧹 Step 1: Clean up conflicting configurations..."

# Remove any existing ReSpeaker configurations
echo "   Removing ReSpeaker configurations..."
sudo rm -f /boot/config.txt.backup* 2>/dev/null || true
sudo rm -f $USER_HOME/.asoundrc.backup* 2>/dev/null || true

# Remove PulseAudio (causes conflicts with USB audio)
if command -v pulseaudio >/dev/null 2>&1; then
    echo "   Removing PulseAudio (conflicts with USB audio)..."
    sudo systemctl stop pulseaudio 2>/dev/null || true
    sudo systemctl disable pulseaudio 2>/dev/null || true
    sudo apt-get remove -y pulseaudio pulseaudio-utils 2>/dev/null || true
fi

# Clean up old ALSA configurations
echo "   Backing up and removing old ALSA configurations..."
if [ -f "$USER_HOME/.asoundrc" ]; then
    cp "$USER_HOME/.asoundrc" "$USER_HOME/.asoundrc.backup.$(date +%Y%m%d_%H%M%S)"
    rm -f "$USER_HOME/.asoundrc"
fi

echo "✅ Cleanup completed"

echo ""
echo "📦 Step 2: Install required audio packages..."

# Update package list
sudo apt-get update

# Install essential audio packages (without PulseAudio)
sudo apt-get install -y \
    alsa-utils \
    alsa-tools \
    libasound2-dev \
    espeak \
    espeak-data

# Ensure user is in audio group
sudo usermod -a -G audio "$CURRENT_USER"

echo "✅ Audio packages installed"

echo ""
echo "🔍 Step 3: Detect USB audio devices..."

# Function to detect Fifine K053 microphone
detect_fifine_mic() {
    echo "   Scanning for Fifine K053 microphone..."
    
    # Method 1: Check USB devices
    FIFINE_USB=$(lsusb | grep -i "fifine\|k053" | head -1)
    if [ -n "$FIFINE_USB" ]; then
        echo "   ✅ Found Fifine USB device: $FIFINE_USB"
    fi
    
    # Method 2: Check ALSA devices
    FIFINE_CARD=""
    while IFS= read -r line; do
        if echo "$line" | grep -qi "fifine\|k053\|usb.*audio"; then
            CARD_NUM=$(echo "$line" | grep -o "card [0-9]" | cut -d' ' -f2)
            FIFINE_CARD="$CARD_NUM"
            echo "   ✅ Found Fifine ALSA card: $CARD_NUM ($line)"
            break
        fi
    done < /proc/asound/cards
    
    # Method 3: Check recording devices
    if [ -z "$FIFINE_CARD" ]; then
        while IFS= read -r line; do
            if echo "$line" | grep -qi "usb.*device.*capture"; then
                CARD_NUM=$(echo "$line" | grep -o "card [0-9]" | cut -d' ' -f2)
                FIFINE_CARD="$CARD_NUM"
                echo "   ✅ Found USB capture device: $CARD_NUM ($line)"
                break
            fi
        done < <(arecord -l 2>/dev/null)
    fi
    
    echo "$FIFINE_CARD"
}

# Function to detect USB Mini Speaker
detect_audio_output() {
    echo "   Scanning for USB Mini Speaker..."
    
    # Look for USB audio output devices
    if [ -f /proc/asound/cards ]; then
        # First, look for USB audio devices
        while IFS= read -r line; do
            if echo "$line" | grep -qi "usb.*audio\|speaker\|mini"; then
                CARD_NUM=$(echo "$line" | grep -o "card [0-9]" | cut -d' ' -f2)
                echo "   ✅ Found USB Mini Speaker: card $CARD_NUM ($line)"
                echo "$CARD_NUM"
                return
            fi
        done < /proc/asound/cards
        
        # Check playback devices for USB audio
        while IFS= read -r line; do
            if echo "$line" | grep -qi "usb.*device.*playback"; then
                CARD_NUM=$(echo "$line" | grep -o "card [0-9]" | cut -d' ' -f2)
                echo "   ✅ Found USB playback device: card $CARD_NUM ($line)"
                echo "$CARD_NUM"
                return
            fi
        done < <(aplay -l 2>/dev/null)
        
        # Fallback to Pi built-in audio if no USB speaker found
        if grep -q "bcm2835" /proc/asound/cards; then
            echo "   ⚠️ USB speaker not found, using Pi built-in audio"
            echo "0"
            return
        fi
        
        # Last resort - first available playback device
        PLAYBACK_CARD=$(aplay -l 2>/dev/null | grep "card" | head -1 | grep -o "card [0-9]" | cut -d' ' -f2)
        if [ -n "$PLAYBACK_CARD" ]; then
            echo "   ✅ Using first available playback device: card $PLAYBACK_CARD"
            echo "$PLAYBACK_CARD"
            return
        fi
    fi
    
    echo "   ⚠️ Using default audio output"
    echo "0"
}

# Detect devices
FIFINE_CARD=$(detect_fifine_mic)
OUTPUT_CARD=$(detect_audio_output)

if [ -z "$FIFINE_CARD" ]; then
    echo "   ⚠️ Fifine K053 not detected. Please ensure it's connected."
    echo "   Available capture devices:"
    arecord -l 2>/dev/null || echo "   No capture devices found"
    
    # Set fallback
    FIFINE_CARD="1"
    echo "   Using fallback capture device: card $FIFINE_CARD"
fi

echo ""
echo "📁 Step 4: Create optimal ALSA configuration..."

# Create optimized .asoundrc for Fifine K053 + USB Mini Speaker setup
cat > "$USER_HOME/.asoundrc" << EOF
# Bible Clock Audio Configuration
# Optimized for Fifine K053 (USB mic) + USB Mini Speaker (pure USB audio)

# Default device (asymmetric: different input/output)
pcm.!default {
    type asym
    playback.pcm "usb_speaker_output"
    capture.pcm "fifine_input"
}

# Fifine K053 USB Microphone Input
pcm.fifine_input {
    type plug
    slave {
        pcm "hw:${FIFINE_CARD},0"
        rate 48000          # K053 native sample rate
        channels 1          # Cardioid microphone (mono)
        format S16_LE       # 16-bit little endian
    }
    # Route mono input to both channels for compatibility
    route_policy "average"
}

# USB Mini Speaker Output (30mm driver, 2 channels)
pcm.usb_speaker_output {
    type plug
    slave {
        pcm "hw:${OUTPUT_CARD},0"
        rate 44100          # Standard audio output rate (works with most USB speakers)
        channels 2          # 2 channel stereo (30mm driver)
        format S16_LE       # 16-bit little endian
    }
}

# Control interface
ctl.!default {
    type hw
    card ${OUTPUT_CARD}
}

# Named devices for explicit use
pcm.microphone {
    type plug
    slave.pcm "fifine_input"
}

pcm.speakers {
    type plug
    slave.pcm "usb_speaker_output"
}

# Alternative device names
pcm.usb_mic {
    type plug
    slave.pcm "fifine_input"
}

pcm.usb_speakers {
    type plug
    slave.pcm "usb_speaker_output"
}

pcm.headphones {
    type plug
    slave.pcm "usb_speaker_output"
}
EOF

echo "✅ ALSA configuration created: $USER_HOME/.asoundrc"

echo ""
echo "🔊 Step 5: Maximize audio output levels..."

# For pure USB audio setup, ensure proper USB audio routing
echo "   Configuring USB audio routing..."
# Note: USB speakers don't need the 3.5mm force setting

# Set output volume to maximum safe level
echo "   Setting output volume to 85% (safe maximum)..."
amixer set Master 85% >/dev/null 2>&1 || true
amixer set PCM 85% >/dev/null 2>&1 || true
amixer set Headphone 85% >/dev/null 2>&1 || true

# Unmute all outputs
echo "   Unmuting audio outputs..."
amixer set Master unmute >/dev/null 2>&1 || true
amixer set PCM unmute >/dev/null 2>&1 || true
amixer set Headphone unmute >/dev/null 2>&1 || true

echo "✅ Audio levels maximized"

echo ""
echo "🧪 Step 6: Test audio configuration..."

# Test microphone recording
echo "   Testing Fifine K053 microphone (5 second recording)..."
timeout 6s arecord -D fifine_input -f S16_LE -r 48000 -c 1 test_mic.wav >/dev/null 2>&1 && {
    echo "   ✅ Microphone recording successful"
    
    # Test speaker playback
    echo "   Testing USB Mini Speaker playback..."
    if aplay -D usb_speaker_output test_mic.wav >/dev/null 2>&1; then
        echo "   ✅ Speaker playback successful"
        AUDIO_TEST_PASSED=true
    else
        echo "   ❌ Speaker playback failed"
        AUDIO_TEST_PASSED=false
    fi
    
    # Clean up test file
    rm -f test_mic.wav
} || {
    echo "   ❌ Microphone recording failed"
    AUDIO_TEST_PASSED=false
}

echo ""
echo "📋 Step 7: Update Bible Clock configuration..."

# Update .env file with optimal settings
if [ -f ".env" ]; then
    echo "   Updating .env with USB audio settings..."
    
    # Create backup
    cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
    
    # Update audio settings
    sed -i 's/^ENABLE_VOICE=.*/ENABLE_VOICE=true/' .env
    sed -i 's/^USB_AUDIO_ENABLED=.*/USB_AUDIO_ENABLED=true/' .env
    sed -i 's/^RESPEAKER_ENABLED=.*/RESPEAKER_ENABLED=false/' .env
    sed -i 's/^AUDIO_INPUT_ENABLED=.*/AUDIO_INPUT_ENABLED=true/' .env
    sed -i 's/^AUDIO_OUTPUT_ENABLED=.*/AUDIO_OUTPUT_ENABLED=true/' .env
    
    # Update device names
    sed -i 's/^USB_MIC_DEVICE_NAME=.*/USB_MIC_DEVICE_NAME="fifine_input"/' .env
    sed -i 's/^USB_SPEAKER_DEVICE_NAME=.*/USB_SPEAKER_DEVICE_NAME="usb_speaker_output"/' .env
    
    # Set optimal voice settings
    sed -i 's/^VOICE_VOLUME=.*/VOICE_VOLUME=0.9/' .env
    sed -i 's/^VOICE_RATE=.*/VOICE_RATE=160/' .env
    
    echo "   ✅ .env file updated"
else
    echo "   ⚠️ .env file not found, creating basic configuration..."
    cat > .env << EOF
# Bible Clock Configuration - USB Audio Setup
ENABLE_VOICE=true
USB_AUDIO_ENABLED=true
RESPEAKER_ENABLED=false
AUDIO_INPUT_ENABLED=true
AUDIO_OUTPUT_ENABLED=true
USB_MIC_DEVICE_NAME="fifine_input"
USB_SPEAKER_DEVICE_NAME="usb_speaker_output"
VOICE_VOLUME=0.9
VOICE_RATE=160
WAKE_WORD=bible clock
EOF
    echo "   ✅ Created .env file with USB audio settings"
fi

echo ""
echo "🎉 Audio Setup Complete!"
echo "======================="

echo ""
echo "📊 Configuration Summary:"
echo "   🎤 Input Device: Fifine K053 (card $FIFINE_CARD) - 48kHz, mono"
echo "   🔊 Output Device: USB Mini Speaker (card $OUTPUT_CARD) - 44.1kHz, 2.0 stereo"
echo "   📁 Config File: $USER_HOME/.asoundrc"
echo "   🔊 Volume Level: 85% (safe maximum)"
echo "   ⚙️ Bible Clock: .env file updated"

if [ "$AUDIO_TEST_PASSED" = true ]; then
    echo "   ✅ Audio Tests: All passed"
else
    echo "   ❌ Audio Tests: Some issues detected"
fi

echo ""
echo "🔄 Next Steps:"
echo "   1. Reboot the system to ensure all changes take effect:"
echo "      sudo reboot"
echo ""
echo "   2. After reboot, test audio manually:"
echo "      arecord -D microphone -f S16_LE -r 48000 -c 1 test.wav"
echo "      aplay -D speakers test.wav"
echo ""
echo "   3. Install and test Porcupine voice control:"
echo "      python install_porcupine.py"
echo "      python test_porcupine_voice.py"
echo ""
echo "   4. Start Bible Clock:"
echo "      ./start_bible_clock.sh"

echo ""
echo "💡 Troubleshooting:"
echo "   • If audio doesn't work, check USB connections"
echo "   • USB Mini Speaker needs secure USB connection for both power and audio"
echo "   • Run 'alsamixer' to adjust levels if needed"
echo "   • Check 'arecord -l' and 'aplay -l' for device detection"
echo "   • Try different USB ports if speaker not detected"

# Show current audio device status
echo ""
echo "📱 Current Audio Devices:"
echo "Capture devices:"
arecord -l 2>/dev/null || echo "No capture devices found"
echo ""
echo "Playback devices:"
aplay -l 2>/dev/null || echo "No playback devices found"

echo ""
echo "✅ Clean audio setup completed successfully!"