# Complete Bible Clock Setup Guide

This guide provides step-by-step instructions for setting up the Bible Clock v3.0 with clean audio configuration and Porcupine voice control.

## 🎯 Prerequisites

**Required Hardware:**
- Raspberry Pi 4 (recommended) or Pi 3B+
- **Fifine K053 USB Microphone** (cardioid, 48kHz)
- **USB Mini Speaker** (2.0 channel, dynamic driver, pure USB audio)
- SD card (32GB+)
- HDMI display
- Internet connection

**Software Requirements:**
- Raspberry Pi OS (Bullseye or newer)
- Python 3.8+
- Git

## 🚀 Setup Process

### Step 1: Clone and Prepare Repository

```bash
# Clone the repository
cd /home/admin
git clone https://github.com/Jackal104/Bible-Clockv2.git Bible-Clock-v3
cd Bible-Clock-v3

# Verify clean repository (should be ~20MB without duplicates)
du -sh .
```

### Step 2: Clean Audio Setup

This removes all conflicting audio configurations and sets up optimal USB audio:

```bash
# Make script executable and run
chmod +x setup_clean_audio.sh
./setup_clean_audio.sh

# Reboot to ensure all changes take effect
sudo reboot
```

**What this script does:**
- ✅ Removes conflicting ReSpeaker/PulseAudio configurations
- ✅ Installs optimal ALSA packages (no PulseAudio)
- ✅ Creates optimized `.asoundrc` for Fifine K053 + USB Mini Speaker
- ✅ Maximizes audio output levels (85% safe maximum)
- ✅ Tests microphone recording and speaker playback
- ✅ Updates `.env` file with correct audio settings

### Step 3: Verify Audio Setup

After reboot, test the audio manually:

```bash
# Test microphone recording (5 seconds)
arecord -D microphone -f S16_LE -r 48000 -c 1 test_audio.wav

# Test speaker playback
aplay -D speakers test_audio.wav

# Clean up
rm test_audio.wav
```

**Expected results:**
- 🎤 Recording should capture clear audio from Fifine K053
- 🔊 Playback should be loud and clear through USB Mini Speaker

### Step 4: Python Environment Setup

```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install core dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install additional voice control dependencies
pip install pyttsx3 SpeechRecognition pyaudio numpy
```

### Step 5: Install Porcupine Voice Control

```bash
# Install Porcupine and dependencies
python install_porcupine.py

# Test Porcupine installation
python test_porcupine_voice.py
```

**Expected output:**
```
✅ Porcupine and dependencies available
✅ Managers initialized
✅ Porcupine voice control created
✅ Porcupine ready for wake word detection
```

### Step 6: Test Voice Control

```bash
# Start the voice control test
python test_porcupine_voice.py

# When prompted, say "Picovoice" clearly into your microphone
# Then say "help" when you hear "Yes?"
```

### Step 7: Launch Bible Clock

```bash
# Start Bible Clock with voice control
./start_bible_clock.sh
```

## 🎙️ Voice Control Usage

### Basic Wake Word: "Picovoice"

1. **Say "Picovoice"** clearly into the Fifine K053 microphone
2. **Wait for "Yes?" response** from the Z120 speakers
3. **Say your command** within 5 seconds

### Available Commands

| Command | Action |
|---------|--------|
| **"help"** | List all available commands |
| **"next verse"** or **"next"** | Show next Bible verse |
| **"previous verse"** or **"previous"** | Show previous verse |
| **"speak verse"** or **"read verse"** | Read current verse aloud |
| **"refresh display"** or **"update"** | Refresh the display |

### Example Conversation
```
You: "Picovoice"
Bible Clock: "Yes?"
You: "Next verse"
Bible Clock: "Showing next verse."

You: "Picovoice"  
Bible Clock: "Yes?"
You: "Read verse"
Bible Clock: "John 3:16: For God so loved the world..."
```

## 🔧 Configuration

### Environment Variables (.env file)

The setup script creates optimal settings, but you can customize:

```bash
# Voice Control
ENABLE_VOICE=true
VOICE_VOLUME=0.9          # 90% TTS volume
VOICE_RATE=160            # Speech rate (words per minute)

# Porcupine Settings  
PORCUPINE_SENSITIVITY=0.5 # 0.1 (less) to 1.0 (more sensitive)
WAKE_WORD=picovoice       # Display name only

# USB Audio (optimized names)
USB_AUDIO_ENABLED=true
USB_MIC_DEVICE_NAME="fifine_input"
USB_SPEAKER_DEVICE_NAME="usb_speaker_output"
```

### Custom Wake Words (Optional)

1. **Create custom keyword:**
   - Visit [Picovoice Console](https://console.picovoice.ai/)
   - Sign up for free account
   - Create keyword like "Hey Bible Clock"
   - Download `.ppn` file

2. **Configure Bible Clock:**
   ```bash
   # Add to .env file:
   PORCUPINE_ACCESS_KEY=your_access_key_here
   PORCUPINE_KEYWORD_PATH=/path/to/your/keyword.ppn
   WAKE_WORD=hey bible clock
   ```

## 🛠️ Troubleshooting

### Audio Issues

**Microphone not working:**
```bash
# Check USB connection
lsusb | grep -i fifine

# Check ALSA detection  
arecord -l | grep -i fifine

# Test direct recording
arecord -D hw:CARD=Device,DEV=0 test.wav
```

**Speakers not working:**
```bash
# Check USB Mini Speaker connection
lsusb | grep -i "audio\|speaker"

# Test direct USB audio output
aplay -D hw:1,0 /usr/share/sounds/alsa/Front_Left.wav

# Check volume levels
alsamixer
```

### Voice Control Issues

**Wake word not detected:**
- Speak clearly and at normal volume
- Ensure microphone is 6-12 inches away
- Try increasing `PORCUPINE_SENSITIVITY` to 0.7
- Check microphone orientation (speak into the front)

**TTS too quiet:**
- Increase `VOICE_VOLUME` to 1.0 in `.env`
- Check USB Mini Speaker physical volume (if available)
- Run `alsamixer` and increase levels

**Porcupine not working:**
```bash
# Check installation
python -c "import pvporcupine; print('OK')"

# Re-run setup
python install_porcupine.py

# Check audio devices
python -c "import pyaudio; p=pyaudio.PyAudio(); [print(f'{i}: {p.get_device_info_by_index(i)[\"name\"]}') for i in range(p.get_device_count())]"
```

### System Issues

**Bible Clock won't start:**
```bash
# Check virtual environment
source venv/bin/activate
python --version  # Should be 3.8+

# Check dependencies
pip list | grep -E "(speech|pyttsx|pvporcupine)"

# Check logs
tail -f ~/.local/share/Bible-Clock/logs/bible-clock.log
```

**Display issues:**
- Ensure correct `DISPLAY_WIDTH` and `DISPLAY_HEIGHT` in `.env`
- Check HDMI connection
- Verify X11 forwarding if using SSH

## 📊 Performance Optimization

### Recommended Settings

**For maximum reliability:**
```bash
# In .env file:
PORCUPINE_SENSITIVITY=0.4    # Reduce false positives
VOICE_TIMEOUT=3              # Shorter command timeout
VOICE_RATE=150               # Slightly slower for clarity
```

**For maximum responsiveness:**
```bash
# In .env file:
PORCUPINE_SENSITIVITY=0.6    # More sensitive detection
VOICE_TIMEOUT=7              # Longer command timeout
VOICE_RATE=180               # Faster speech
```

### System Resources

**Expected usage:**
- **CPU**: 5-15% on Pi 4 (Porcupine is very efficient)
- **Memory**: 150-200MB total
- **Storage**: 500MB with dependencies

## 🎉 Success Checklist

✅ **Audio Setup Complete:**
- Fifine K053 detected and recording clearly
- Z120 speakers playing at good volume
- No ALSA/PulseAudio error messages

✅ **Porcupine Working:**
- "Picovoice" wake word reliably detected
- TTS responses clear and loud
- Commands processed correctly

✅ **Bible Clock Running:**
- Display shows verses correctly
- Web interface accessible at `http://localhost:5000`
- Voice control status shows "Online"

✅ **Integration Working:**
- Voice commands change verses
- TTS reads verses clearly
- Wake word detection resumes after TTS

## 🆘 Getting Help

If you encounter issues:

1. **Run diagnostics:**
   ```bash
   ./setup_clean_audio.sh     # Re-run audio setup
   python test_porcupine_voice.py  # Test voice control
   ```

2. **Check hardware:**
   - Verify all USB connections
   - Test with other audio applications
   - Check for loose 3.5mm cable

3. **Reset configuration:**
   ```bash
   # Back up and reset audio config
   mv ~/.asoundrc ~/.asoundrc.backup
   ./setup_clean_audio.sh
   ```

The setup process creates a robust, efficient voice-controlled Bible Clock that works reliably with USB audio devices!