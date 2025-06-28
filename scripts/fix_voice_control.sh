#!/bin/bash

echo "🔧 Fixing Voice Control Initialization..."

# Check if we're in the right directory
if [[ ! -f "main.py" ]]; then
    echo "❌ Please run this script from the Bible-Clock-v3 directory"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

echo "🔍 Checking main.py voice control arguments..."

# Check how main.py handles voice control
python3 -c "
import argparse
import sys

# Simulate the argument parser from main.py
parser = argparse.ArgumentParser()
parser.add_argument('--disable-voice', action='store_true', help='Disable voice control')
parser.add_argument('--enable-voice', action='store_true', help='Force enable voice control')

# Test with no arguments (default behavior)
args = parser.parse_args([])
print(f'Default - disable_voice: {args.disable_voice}, enable_voice: {args.enable_voice}')

# Test with enable-voice
args = parser.parse_args(['--enable-voice'])
print(f'With --enable-voice - disable_voice: {args.disable_voice}, enable_voice: {args.enable_voice}')
"

echo ""
echo "🔧 Testing voice control initialization with forced enable..."

python3 -c "
import sys
import os
sys.path.insert(0, 'src')

# Set all required environment variables
os.environ['DISPLAY_WIDTH'] = '1872'
os.environ['DISPLAY_HEIGHT'] = '1404'
os.environ['BIBLE_API_URL'] = 'https://bible-api.com'

print('Environment variables set:')
print(f'  DISPLAY_WIDTH: {os.environ.get(\"DISPLAY_WIDTH\")}')
print(f'  DISPLAY_HEIGHT: {os.environ.get(\"DISPLAY_HEIGHT\")}')
print(f'  BIBLE_API_URL: {os.environ.get(\"BIBLE_API_URL\")}')

try:
    from verse_manager import VerseManager
    from image_generator import ImageGenerator
    from display_manager import DisplayManager
    from voice_control import VoiceControl

    print('✅ All classes imported successfully')
    
    # Create managers
    verse_manager = VerseManager()
    image_generator = ImageGenerator()
    display_manager = DisplayManager()
    
    print('✅ Managers created successfully')
    
    # Try to create voice control directly
    try:
        voice_control = VoiceControl(verse_manager, display_manager)
        print('✅ VoiceControl created successfully!')
        
        # Test if it has the necessary attributes
        if hasattr(voice_control, 'tts_engine'):
            print('✅ TTS engine available')
        if hasattr(voice_control, 'recognizer'):
            print('✅ Speech recognizer available')
        if hasattr(voice_control, 'listening'):
            print(f'✅ Listening status: {voice_control.listening}')
            
    except Exception as ve:
        print(f'❌ VoiceControl creation failed: {ve}')
        import traceback
        traceback.print_exc()
        
except Exception as e:
    print(f'❌ Import/setup failed: {e}')
    import traceback
    traceback.print_exc()
"

echo ""
echo "🔧 Checking service manager voice control logic..."

# Check the service manager source code for voice control initialization
if [[ -f "src/service_manager.py" ]]; then
    echo "Service manager voice control initialization logic:"
    grep -A 10 -B 5 "voice_control" src/service_manager.py | head -20
else
    echo "❌ service_manager.py not found"
fi

echo ""
echo "💡 Potential fixes:"
echo "1. Restart Bible Clock with --enable-voice flag"
echo "2. Check if voice control is disabled by default in service manager"
echo "3. Force voice control initialization in the service"

echo ""
echo "🔧 To fix this, try restarting with voice enabled:"
echo "sudo systemctl stop bible-clock.service"
echo "# Then manually run: python main.py --enable-voice"