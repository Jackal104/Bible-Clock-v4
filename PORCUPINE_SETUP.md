# Porcupine Voice Control Setup for Bible Clock

This guide explains how to set up Porcupine wake word detection for the Bible Clock, which provides much better performance than the previous speech recognition approach.

## 🎯 Why Porcupine?

**Advantages over previous system:**
- ✅ **Efficient wake word detection** - Uses minimal CPU
- ✅ **No internet required** - Works completely offline  
- ✅ **Accurate detection** - Purpose-built for wake words
- ✅ **No PyAudio conflicts** - Better hardware compatibility
- ✅ **Always listening** - Designed for continuous operation
- ✅ **Custom wake words** - Create your own phrases

## 📦 Installation

### Step 1: Install Porcupine
```bash
cd /home/admin/Bible-Clock-v3
python install_porcupine.py
```

This will:
- Install `pvporcupine` package
- Check all dependencies  
- Test Porcupine functionality
- Update your `.env` file with Porcupine settings

### Step 2: Test Installation
```bash
python test_porcupine_voice.py
```

## 🎙️ Basic Usage

### Default Wake Word: "Picovoice"
1. Start Bible Clock: `./start_bible_clock.sh`
2. Say **"Picovoice"** clearly into your microphone
3. Wait for "Yes?" response
4. Say your command: "help", "next verse", "speak verse", etc.

### Example Conversation:
```
You: "Picovoice"
Bible Clock: "Yes?"
You: "Help"
Bible Clock: "I can help you with Bible verses. Say 'next verse'..."
```

## 🛠️ Configuration

### Environment Variables (.env file)
```bash
# Enable voice control
ENABLE_VOICE=true

# Porcupine settings
PORCUPINE_ACCESS_KEY=          # Optional: for custom keywords
PORCUPINE_KEYWORD_PATH=        # Optional: custom .ppn file path
PORCUPINE_SENSITIVITY=0.5      # 0.1 (less sensitive) to 1.0 (more)

# USB Audio (update for your devices)
USB_MIC_DEVICE_NAME="USB PnP Audio Device"
USB_SPEAKER_DEVICE_NAME="USB PnP Audio Device"
```

### Sensitivity Tuning
- **0.1-0.3**: Less sensitive (reduces false positives)
- **0.4-0.6**: Balanced (recommended)
- **0.7-1.0**: More sensitive (may increase false positives)

## 🎯 Custom Wake Words

### Step 1: Create Custom Keyword
1. Visit [Picovoice Console](https://console.picovoice.ai/)
2. Sign up for free account
3. Create custom keyword (e.g., "Hey Bible Clock")
4. Download the `.ppn` file

### Step 2: Configure Bible Clock
```bash
# In your .env file:
PORCUPINE_ACCESS_KEY=your_access_key_here
PORCUPINE_KEYWORD_PATH=/path/to/your/keyword.ppn
WAKE_WORD=hey bible clock
```

### Step 3: Test Custom Keyword
```bash
python test_porcupine_voice.py
```

## 📋 Available Voice Commands

After saying the wake word and hearing "Yes?":

| Command | Action |
|---------|--------|
| **"help"** | List available commands |
| **"next verse"** or **"next"** | Show next Bible verse |
| **"previous verse"** or **"previous"** | Show previous verse |
| **"speak verse"** or **"read verse"** | Read current verse aloud |
| **"refresh display"** or **"update"** | Refresh the display |

## 🔧 Troubleshooting

### Porcupine Not Working
```bash
# Check installation
python -c "import pvporcupine; print('Porcupine OK')"

# Check audio devices  
python -c "import pyaudio; p=pyaudio.PyAudio(); print([p.get_device_info_by_index(i)['name'] for i in range(p.get_device_count())])"

# Run full test
python test_porcupine_voice.py
```

### Wake Word Not Detected
1. **Check microphone**: Ensure USB mic is connected and working
2. **Adjust sensitivity**: Increase `PORCUPINE_SENSITIVITY` in `.env`
3. **Speak clearly**: Say wake word distinctly, not too fast
4. **Check audio levels**: Test recording with `arecord -D hw:2,0 test.wav`

### TTS Not Working
1. **Check speakers**: Ensure USB speakers are connected
2. **Test audio output**: `aplay -D hw:1,0 /usr/share/sounds/alsa/Front_Left.wav`
3. **Install espeak**: `sudo apt-get install espeak espeak-data`

### Fallback to Old System
If Porcupine isn't available, Bible Clock automatically falls back to the original speech recognition system. You'll see this message:
```
INFO - Using traditional speech recognition for wake word
```

## 🔄 Switching Between Systems

### Force Porcupine (Recommended)
```bash
# Ensure Porcupine is installed
python install_porcupine.py

# Start Bible Clock
./start_bible_clock.sh
```

### Force Traditional Speech Recognition
```bash
# Temporarily disable Porcupine
mv src/porcupine_voice_control.py src/porcupine_voice_control.py.disabled

# Start Bible Clock  
./start_bible_clock.sh

# Re-enable later
mv src/porcupine_voice_control.py.disabled src/porcupine_voice_control.py
```

## 📈 Performance Comparison

| Feature | Traditional | Porcupine |
|---------|-------------|-----------|
| CPU Usage | High | Low |
| Accuracy | Medium | High |
| False Positives | Common | Rare |
| Internet Required | Yes (Google) | No |
| Custom Wake Words | Limited | Easy |
| Hardware Compatibility | Poor | Good |

## 🎉 Success Indicators

You'll know Porcupine is working when you see:
```
INFO - Using Porcupine-based voice control
INFO - Porcupine initialized: sample_rate=16000Hz, frame_length=512
INFO - Started Porcupine wake word detection
```

And when you say the wake word:
```
INFO - Wake word detected by Porcupine!
INFO - Wake word detected, listening for command...
```

## 🆘 Support

If you encounter issues:

1. **Run diagnostics**: `python test_porcupine_voice.py`
2. **Check logs**: Look for errors in Bible Clock startup output
3. **Test hardware**: Verify microphone and speakers work with `arecord`/`aplay`
4. **Try defaults**: Use "picovoice" wake word first before custom keywords

The Porcupine integration maintains full compatibility with the existing Bible Clock interface while providing much more reliable voice control!