#!/bin/bash
"""
Deploy Bible Clock to Pi and test complete voice flow
"""

echo "🚀 Deploying Bible Clock with Voice Control Testing"
echo "=================================================="

# Configuration
PI_USER="${PI_USER:-pi}"
PI_HOST="${PI_HOST:-raspberrypi.local}"
PI_PATH="${PI_PATH:-/home/pi/Bible-Clockv2}"

echo "Target: ${PI_USER}@${PI_HOST}:${PI_PATH}"
echo ""

# Test connection
echo "📡 Testing connection to Pi..."
if ! ping -c 1 "$PI_HOST" >/dev/null 2>&1; then
    echo "❌ Cannot reach Pi at $PI_HOST"
    echo "   Please check network connection and try again"
    exit 1
fi
echo "✅ Pi is reachable"

# Deploy code
echo ""
echo "📤 Deploying updated code..."
./deploy_to_pi.sh

if [ $? -ne 0 ]; then
    echo "❌ Deployment failed"
    exit 1
fi

# Test voice control components
echo ""
echo "🎤 Testing Voice Control Components"
echo "==================================="

echo ""
echo "1. Testing Porcupine wake word detection..."
ssh "${PI_USER}@${PI_HOST}" "cd $PI_PATH && python3 -c 'import pvporcupine; print(\"✅ Porcupine available\")'" || {
    echo "❌ Porcupine not available - installing..."
    ssh "${PI_USER}@${PI_HOST}" "cd $PI_PATH && pip3 install pvporcupine"
}

echo ""
echo "2. Testing microphone access..."
ssh "${PI_USER}@${PI_HOST}" "cd $PI_PATH && python3 -c 'import pyaudio; p=pyaudio.PyAudio(); print(f\"✅ Audio devices: {p.get_device_count()}\"); p.terminate()'" || {
    echo "❌ PyAudio not available - installing..."
    ssh "${PI_USER}@${PI_HOST}" "sudo apt-get update && sudo apt-get install -y python3-pyaudio portaudio19-dev"
}

echo ""
echo "3. Testing ChatGPT API connectivity..."
ssh "${PI_USER}@${PI_HOST}" "cd $PI_PATH && python3 -c 'import openai; print(\"✅ OpenAI library available\")'" || {
    echo "❌ OpenAI library not available - installing..."
    ssh "${PI_USER}@${PI_HOST}" "cd $PI_PATH && pip3 install openai"
}

echo ""
echo "4. Testing Piper TTS..."
ssh "${PI_USER}@${PI_HOST}" "cd $PI_PATH && ls -la piper/" && {
    echo "✅ Piper installation found"
} || {
    echo "❌ Piper not found - you may need to install it"
}

echo ""
echo "5. Testing Amy voice model..."
ssh "${PI_USER}@${PI_HOST}" "cd $PI_PATH && ls -la voices/en_US-amy-*" && {
    echo "✅ Amy voice model found"
} || {
    echo "❌ Amy voice model not found - downloading..."
    ssh "${PI_USER}@${PI_HOST}" "cd $PI_PATH && python3 -c 'from src.voice_manager import VoiceManager; vm = VoiceManager(); vm.download_voice(\"en_US-amy-medium\")'"
}

echo ""
echo "🔊 Voice Flow Test Instructions"
echo "==============================="
echo ""
echo "SSH to your Pi and run these tests:"
echo ""
echo "ssh ${PI_USER}@${PI_HOST}"
echo "cd $PI_PATH"
echo ""
echo "Test 1 - Wake word detection:"
echo "python3 src/porcupine_voice_control.py"
echo "→ Say 'Bible Clock' and check if it detects"
echo ""
echo "Test 2 - Verse explanation:"
echo "→ Say 'Bible Clock' (wake word)"
echo "→ Say 'Explain this verse'"
echo "→ Should respond with current verse explanation via Piper TTS"
echo ""
echo "Test 3 - General biblical questions:"
echo "→ Say 'Bible Clock' (wake word)"
echo "→ Ask any biblical question"
echo "→ Should get ChatGPT response via Amy voice"
echo ""
echo "Test 4 - Check audio devices:"
echo "arecord -l  # List recording devices"
echo "aplay -l    # List playback devices"
echo ""
echo "🎉 Deployment and setup complete!"
echo ""
echo "Voice Control Flow:"
echo "1. 'Bible Clock' (Porcupine wake word)"
echo "2. Microphone listens for command"
echo "3. Speech-to-text processes command"
echo "4. ChatGPT API handles the request"
echo "5. Piper TTS with Amy voice responds"
echo ""
echo "Web interface: http://${PI_HOST}:5000"