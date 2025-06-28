# USB Audio Setup Guide for Bible Clock v3.0

## Recommended USB Audio Devices

### USB Microphones
- **Samson Go Mic** - Compact, good quality, plug-and-play
- **Blue Yeti Nano** - Professional quality, multiple pickup patterns  
- **Audio-Technica ATR2100x-USB** - Excellent for voice recognition
- **Any USB microphone with Linux compatibility**

### USB Speakers
- **Logitech Z120** - Compact, good for voice output
- **Creative Pebble** - Small desktop speakers
- **JBL Clip series** - Portable with good audio quality
- **Any USB-powered speakers with standard USB audio class support**

## Setup Instructions

### 1. Remove ReSpeaker HAT Configuration
```bash
# Clean up ReSpeaker configuration
./scripts/remove_respeaker.sh
sudo reboot
```

### 2. Connect USB Audio Devices
1. Connect USB microphone to Raspberry Pi
2. Connect USB speakers to Raspberry Pi
3. Wait 10-15 seconds for device recognition

### 3. Configure USB Audio
```bash
# Run automatic USB audio setup
./scripts/setup_usb_audio.sh
```

### 4. Test Configuration
```bash
# Test microphone recording
arecord -f cd -t wav -d 5 test.wav
aplay test.wav

# Start Bible Clock with voice control
python main.py
```

## Manual Configuration

If automatic setup doesn't work, manually configure:

### Check Available Devices
```bash
# List playback devices
aplay -l

# List recording devices  
arecord -l

# List USB devices
lsusb | grep -i audio
```

### Update .env File
```bash
# Enable USB audio
USB_AUDIO_ENABLED=true
AUDIO_INPUT_ENABLED=true
AUDIO_OUTPUT_ENABLED=true
ENABLE_VOICE=true

# Set device names (from aplay/arecord output)
USB_MIC_DEVICE_NAME="Your_USB_Mic_Name"
USB_SPEAKER_DEVICE_NAME="Your_USB_Speaker_Name"
```

### Create ALSA Configuration
Create `~/.asoundrc`:
```
pcm.!default {
    type asym
    playback.pcm "plughw:1,0"    # USB speaker card
    capture.pcm "plughw:2,0"     # USB microphone card
}

ctl.!default {
    type hw
    card 1
}
```

## Voice Commands

**Wake Word**: "bible clock" - Say this first, then your command

### 📖 Display Control Commands
- **"speak verse"** - Read current verse aloud
- **"refresh display"** - Update with new verse
- **"clear display"** - Clear screen to white  
- **"change background"** - Switch background style
- **"cycle mode"** - Change Bible translation
- **"change mode"** - Switch time/date/random modes
- **"time mode"** - Time-based verse selection
- **"date mode"** - Biblical calendar events
- **"random mode"** - Random verse inspiration

### ℹ️ Information Commands
- **"what time is it"** - Current time
- **"system status"** - Health and performance report
- **"current verse"** - What verse is displayed
- **"current mode"** - Active display mode
- **"current translation"** - Bible version in use

### ❓ Biblical Questions (ChatGPT Integration)
Ask naturally after "bible clock":
- **"What does this verse mean?"**
- **"Who was King David?"** 
- **"Explain the parable of..."**
- **"Help me understand this passage"**
- **"Tell me about biblical love"**
- **"Why is this verse important?"**
- **"What can I learn from this?"**

### 🆘 Help Commands
- **"help"** - Complete command overview
- **"help display"** - Display control commands
- **"help questions"** - How to ask biblical questions
- **"help examples"** - Question examples

## Troubleshooting

### No Audio Devices Detected
```bash
# Restart audio services
sudo systemctl restart alsa-state
pulseaudio --kill && pulseaudio --start

# Check USB connections
lsusb
dmesg | tail -20
```

### Audio Quality Issues
```bash
# Adjust microphone levels
alsamixer

# Test different sample rates
arecord -r 44100 -f cd -t wav -d 5 test44k.wav
arecord -r 16000 -f S16_LE -c 1 -t wav -d 5 test16k.wav
```

### Voice Recognition Not Working
1. Check microphone positioning (6-12 inches from mouth)
2. Ensure quiet environment for wake word detection
3. Speak clearly and at moderate volume
4. Check `.env` file `WAKE_WORD` setting (default: "bible")

## Benefits of USB Audio

✅ **Plug-and-play compatibility**  
✅ **No kernel module dependencies**  
✅ **Easy device replacement**  
✅ **Better audio quality options**  
✅ **No GPIO pin conflicts**  
✅ **Standard Linux audio support**  

## Hardware Requirements

- Raspberry Pi 4B (recommended) or 3B+
- MicroSD card (32GB+ recommended)
- USB microphone
- USB speakers or USB headphones
- Waveshare 13.3" e-ink display
- Stable power supply (3A+ recommended)