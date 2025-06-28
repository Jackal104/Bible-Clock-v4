#!/bin/bash

# Bible Clock Voice Control Setup Script
# This script installs and configures voice control dependencies

echo "🎤 Setting up Bible Clock Voice Control..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check if we're in the right directory
if [[ ! -f "main.py" ]]; then
    print_error "Please run this script from the Bible-Clock-v3 directory"
    exit 1
fi

# Install system dependencies
print_status "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y espeak espeak-data alsa-utils portaudio19-dev python3-dev build-essential

# Activate virtual environment
print_status "Activating virtual environment..."
if [[ ! -d "venv" ]]; then
    print_error "Virtual environment not found. Please create one first."
    exit 1
fi

source venv/bin/activate

# Install Python dependencies
print_status "Installing Python voice control dependencies..."
pip install --upgrade pip
pip install pyttsx3 SpeechRecognition openai pyaudio

# Test voice control initialization
print_status "Testing voice control initialization..."
python3 -c "
import pyttsx3
import speech_recognition as sr
print('✅ pyttsx3 (text-to-speech) installed successfully')
print('✅ SpeechRecognition installed successfully')

# Test TTS engine
try:
    engine = pyttsx3.init()
    print('✅ TTS engine initialized successfully')
    engine.stop()
except Exception as e:
    print(f'⚠️  TTS engine warning: {e}')

# Test microphone
try:
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print('✅ Microphone access successful')
except Exception as e:
    print(f'⚠️  Microphone warning: {e}')
"

# Configure audio for USB devices
print_status "Configuring audio for USB devices..."

# Create ALSA configuration if it doesn't exist
if [[ ! -f ~/.asoundrc ]]; then
    print_status "Creating ALSA configuration for USB audio..."
    cat > ~/.asoundrc << EOF
# USB Audio Configuration for Bible Clock
pcm.!default {
    type pulse
}
ctl.!default {
    type pulse
}

# USB Audio Card Setup
pcm.usbcard {
    type hw
    card 1
}

ctl.usbcard {
    type hw
    card 1
}
EOF
fi

# Set USB audio as default if available
print_status "Checking USB audio devices..."
if aplay -l | grep -q "USB Audio"; then
    print_status "USB Audio device found"
else
    print_warning "No USB Audio device detected. Please ensure your USB microphone/speakers are connected."
fi

# Test audio setup
print_status "Testing audio setup..."
echo "Testing speaker output (you should hear a tone)..."
timeout 3 speaker-test -t sine -f 1000 -l 1 2>/dev/null || print_warning "Speaker test failed"

print_status "Voice control setup complete!"
print_status "You can now:"
print_status "1. Restart the Bible Clock service: sudo systemctl restart bible-clock.service"
print_status "2. Check voice control status in the web interface"
print_status "3. Test voice commands with 'Bible Clock, help'"

echo ""
print_status "If voice recognition still shows as offline, check the Audio/AI Settings page for configuration options."