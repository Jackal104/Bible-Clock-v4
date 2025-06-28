# Bible Clock Pi Setup Instructions

## Step 1: Download Code to Your Pi

SSH to your Pi and run these commands:

```bash
# SSH to your Pi
ssh admin@Bible-Clock.local

# Navigate to home directory
cd /home/admin

# Clone or update the repository to Bible-Clock-v3 directory
if [ -d "Bible-Clock-v3" ]; then
    cd Bible-Clock-v3
    git pull origin main
else
    git clone https://github.com/Jackal104/Bible-Clockv2.git Bible-Clock-v3
    cd Bible-Clock-v3
fi
```

## Step 2: Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3-pip python3-venv python3-pyaudio portaudio19-dev espeak alsa-utils

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Install voice control packages
pip install pvporcupine speechrecognition pyaudio openai pyttsx3
```

## Step 3: Setup Piper TTS with Amy Voice

```bash
# Download Piper TTS
wget https://github.com/rhasspy/piper/releases/download/v1.2.0/piper_linux_x86_64.tar.gz
tar -xzf piper_linux_x86_64.tar.gz
sudo cp piper/piper /usr/local/bin/

# Create voices directory
mkdir -p voices

# Download Amy voice model
cd voices
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx
wget https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/en/en_US/amy/medium/en_US-amy-medium.onnx.json
cd ..
```

## Step 4: Configure Environment Variables

Create your `.env` file:

```bash
cp .env.example .env
nano .env
```

Add these settings to your `.env` file:

```bash
# Bible Clock Settings
TIME_FORMAT=12
BIBLE_VERSION=ESV
UPDATE_INTERVAL=60

# Voice Control
ENABLE_VOICE=true
ENABLE_CHATGPT_VOICE=true
WAKE_WORD=bible clock

# ChatGPT API (Replace with your API key)
OPENAI_API_KEY=your_openai_api_key_here
CHATGPT_MODEL=gpt-3.5-turbo
CHATGPT_MAX_TOKENS=150

# Porcupine Wake Word (Get free key from https://picovoice.ai/)
PORCUPINE_ACCESS_KEY=your_porcupine_key_here
PORCUPINE_SENSITIVITY=0.5

# Piper TTS
PIPER_VOICE_MODEL=en_US-amy-medium.onnx
PIPER_VOICE_SPEED=1.0

# Audio Settings
USB_AUDIO_ENABLED=true
AUDIO_INPUT_ENABLED=true
AUDIO_OUTPUT_ENABLED=true
```

## Step 5: Test Audio Devices

```bash
# Check audio devices
arecord -l  # List recording devices (microphones)
aplay -l    # List playback devices (speakers)

# Test microphone
arecord -d 5 test.wav
aplay test.wav

# Test Piper TTS
echo "Hello from Piper" | piper --model voices/en_US-amy-medium.onnx --output_file test_piper.wav
aplay test_piper.wav
```

## Step 6: Test Voice Control Components

### Test 1: Basic Piper TTS
```bash
python3 -c "
from src.voice_manager import VoiceManager
vm = VoiceManager()
vm.speak('Bible Clock voice test successful')
"
```

### Test 2: Microphone Recognition
```bash
python3 -c "
import speech_recognition as sr
r = sr.Recognizer()
m = sr.Microphone()
print('Say something...')
with m as source: audio = r.listen(source, timeout=5)
try:
    text = r.recognize_google(audio)
    print(f'You said: {text}')
except: print('Could not understand')
"
```

### Test 3: Porcupine Wake Word Detection
```bash
# Get free access key from https://picovoice.ai/
# Add it to your .env file as PORCUPINE_ACCESS_KEY
python3 src/porcupine_voice_control.py
# Say "picovoice" and check if it detects (default keyword)
```

### Test 4: ChatGPT Integration
```bash
python3 -c "
import openai
openai.api_key = 'your_api_key_here'
response = openai.ChatCompletion.create(
    model='gpt-3.5-turbo',
    messages=[{'role': 'user', 'content': 'What is John 3:16?'}]
)
print(response.choices[0].message.content)
"
```

## Step 7: Run the Complete System

```bash
# Start the Bible Clock with voice control
python3 main.py

# Or start individual components:
python3 src/chatgpt_voice_control.py  # ChatGPT + Piper voice control
python3 src/porcupine_voice_control.py  # Porcupine wake word detection
```

## Quick Start - Complete Voice Control System

**After setup, run the enhanced voice control system:**
```bash
# Verify all components are ready
python3 setup_voice_control.py

# Run the complete voice control system
python3 bible_clock_voice_complete.py
```

## Expected Voice Flow

1. **Amy announces:** "Bible Clock voice control with ChatGPT is ready"
2. **Say "Bible Clock"** → Amy responds: "Yes, how can I help you?"
3. **Say your command:**
   - "Explain this verse" → Current verse explanation via ChatGPT
   - "What does John 3:16 say?" → Bible question via ChatGPT
   - "Next verse" → Navigate to next verse
   - "Previous verse" → Navigate to previous verse
   - "Read current verse" → Speak current verse
4. **Amy voice responds** via Piper TTS through USB speakers

## Troubleshooting

### Audio Issues:
```bash
# Check ALSA configuration
cat /proc/asound/cards
sudo alsamixer

# Test audio output
speaker-test -t wav -c 2

# Restart audio service
sudo systemctl restart alsa-state
```

### Permission Issues:
```bash
# Add user to audio group
sudo usermod -a -G audio admin
# Logout and login again
```

### Piper TTS Issues:
```bash
# Check Piper installation
which piper
piper --help

# Test voice model
ls -la voices/
```

### Voice Recognition Issues:
```bash
# Check microphone permissions
sudo chmod 666 /dev/snd/*

# Install additional audio packages
sudo apt install pulseaudio pulseaudio-utils
```

## Service Setup (Optional)

Create a systemd service to auto-start:

```bash
sudo nano /etc/systemd/system/bible-clock.service
```

```ini
[Unit]
Description=Bible Clock with Voice Control
After=network.target

[Service]
Type=simple
User=admin
WorkingDirectory=/home/admin/Bible-Clock-v3
Environment=PATH=/home/admin/Bible-Clock-v3/venv/bin
ExecStart=/home/admin/Bible-Clock-v3/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable bible-clock.service
sudo systemctl start bible-clock.service
```

## Web Interface

Access the web interface at: http://Bible-Clock.local:5000

You should see the time displaying with leading zeros (02:05 instead of 2:5) and be able to test the live preview.