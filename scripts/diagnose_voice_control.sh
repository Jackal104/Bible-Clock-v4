#!/bin/bash

echo "🔍 Bible Clock Voice Control Diagnostics"
echo "========================================"

# Check if we're in the right directory
if [[ ! -f "main.py" ]]; then
    echo "❌ Please run this script from the Bible-Clock-v3 directory"
    exit 1
fi

echo ""
echo "📦 Checking Python Dependencies:"
source venv/bin/activate

python3 -c "
import sys
try:
    import pyttsx3
    print('✅ pyttsx3: Available')
except ImportError:
    print('❌ pyttsx3: Missing')

try:
    import speech_recognition as sr
    print('✅ SpeechRecognition: Available')
except ImportError:
    print('❌ SpeechRecognition: Missing')

try:
    import openai
    print('✅ openai: Available')
except ImportError:
    print('❌ openai: Missing (optional)')

try:
    import pyaudio
    print('✅ pyaudio: Available')
except ImportError:
    print('❌ pyaudio: Missing')
"

echo ""
echo "🎤 Testing Voice Control Initialization:"
python3 -c "
import sys
sys.path.insert(0, 'src')

try:
    from voice_control import VoiceControl
    print('✅ VoiceControl class imported successfully')
    
    # Try to initialize with dummy objects
    class DummyVerseManager:
        def get_current_verse(self):
            return {'verse': 'Test verse', 'reference': 'Test 1:1'}
    
    class DummyDisplayManager:
        def display_image(self, image, force_refresh=False):
            pass
    
    verse_manager = DummyVerseManager()
    display_manager = DummyDisplayManager()
    
    try:
        voice_control = VoiceControl(verse_manager, display_manager)
        print('✅ VoiceControl initialized successfully')
        
        # Check if TTS is working
        if hasattr(voice_control, 'tts_engine') and voice_control.tts_engine:
            print('✅ TTS engine is available')
        else:
            print('❌ TTS engine failed to initialize')
            
        # Check if speech recognition is working  
        if hasattr(voice_control, 'recognizer'):
            print('✅ Speech recognizer is available')
        else:
            print('❌ Speech recognizer failed to initialize')
            
    except Exception as e:
        print(f'❌ VoiceControl initialization failed: {e}')
        import traceback
        traceback.print_exc()
        
except ImportError as e:
    print(f'❌ Failed to import VoiceControl: {e}')
"

echo ""
echo "🔊 Checking Audio Devices:"
echo "Playback devices:"
aplay -l

echo ""
echo "Recording devices:"
arecord -l

echo ""
echo "🎯 Testing Microphone Access:"
python3 -c "
import speech_recognition as sr
try:
    r = sr.Recognizer()
    mic_list = sr.Microphone.list_microphone_names()
    print(f'Available microphones: {len(mic_list)}')
    for i, name in enumerate(mic_list):
        print(f'  {i}: {name}')
        
    # Test default microphone
    with sr.Microphone() as source:
        print('✅ Default microphone accessible')
        r.adjust_for_ambient_noise(source, duration=1)
        print('✅ Ambient noise adjustment completed')
        
except Exception as e:
    print(f'❌ Microphone test failed: {e}')
"

echo ""
echo "🔧 Checking Service Manager:"
python3 -c "
import sys
sys.path.insert(0, 'src')

try:
    from service_manager import ServiceManager
    from verse_manager import VerseManager
    from image_generator import ImageGenerator
    from display_manager import DisplayManager
    
    print('✅ All manager classes imported')
    
    # Check if voice control is enabled in service manager
    verse_manager = VerseManager()
    image_generator = ImageGenerator()
    display_manager = DisplayManager()
    
    service_manager = ServiceManager(
        verse_manager=verse_manager,
        image_generator=image_generator,
        display_manager=display_manager,
        voice_control=None,  # This should be initialized automatically
        web_interface=False
    )
    
    if hasattr(service_manager, 'voice_control') and service_manager.voice_control:
        print('✅ Voice control is initialized in service manager')
    else:
        print('❌ Voice control is NOT initialized in service manager')
        print('   This is likely why the web interface shows offline')
        
except Exception as e:
    print(f'❌ Service manager test failed: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "📋 Environment Variables:"
echo "SIMULATION_MODE: ${SIMULATION_MODE:-not set}"
echo "WEB_ONLY: ${WEB_ONLY:-not set}"  
echo "DISABLE_VOICE: ${DISABLE_VOICE:-not set}"

echo ""
echo "🔍 Checking Service Logs:"
echo "Recent Bible Clock service logs:"
sudo journalctl -u bible-clock.service --lines=10 --no-pager

echo ""
echo "✅ Diagnosis Complete!"
echo ""
echo "💡 Recommendations:"
echo "1. If voice control is not initialized in service manager, check main.py arguments"
echo "2. If microphone test failed, check USB audio device permissions"
echo "3. If TTS engine failed, try: sudo apt-get install espeak-data"
echo "4. Check service logs for specific error messages"