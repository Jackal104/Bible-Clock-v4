#!/usr/bin/env python3
"""
Debug script to check voice control status on Raspberry Pi
"""

import os
import sys
import time

# Add src directory to path
sys.path.insert(0, 'src')

def check_audio_devices():
    """Check available audio devices"""
    print("🎤 Audio Device Check:")
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        
        print(f"Available audio devices:")
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            print(f"  Device {i}: {info['name']} - Inputs: {info['maxInputChannels']}, Outputs: {info['maxOutputChannels']}")
        
        pa.terminate()
    except Exception as e:
        print(f"❌ Audio device check failed: {e}")

def check_voice_dependencies():
    """Check if voice control dependencies are available"""
    print("\n📦 Dependency Check:")
    
    try:
        import speech_recognition as sr
        print("✅ speech_recognition available")
    except ImportError as e:
        print(f"❌ speech_recognition not available: {e}")
        return False
    
    try:
        import pyttsx3
        print("✅ pyttsx3 available")
    except ImportError as e:
        print(f"❌ pyttsx3 not available: {e}")
        return False
    
    try:
        import pyaudio
        print("✅ pyaudio available")
    except ImportError as e:
        print(f"❌ pyaudio not available: {e}")
        return False
    
    return True

def test_voice_control_creation():
    """Test creating voice control instance"""
    print("\n🎙️ Voice Control Instance Test:")
    
    # Set required environment variables
    os.environ['ENABLE_VOICE'] = 'true'
    os.environ['DISPLAY_WIDTH'] = '1872'
    os.environ['DISPLAY_HEIGHT'] = '1404'
    os.environ['BIBLE_API_URL'] = 'https://bible-api.com'
    
    try:
        from verse_manager import VerseManager
        from image_generator import ImageGenerator
        from display_manager import DisplayManager
        from voice_control import VoiceControl
        
        print("✅ All classes imported successfully")
        
        # Create managers
        verse_manager = VerseManager()
        image_generator = ImageGenerator()
        display_manager = DisplayManager()
        
        print("✅ Managers created successfully")
        
        # Create voice control
        voice_control = VoiceControl(verse_manager, image_generator, display_manager)
        print("✅ VoiceControl created successfully!")
        
        # Check status
        print(f"Voice control enabled: {voice_control.enabled}")
        print(f"Listening status: {voice_control.listening}")
        print(f"Wake word: {voice_control.wake_word}")
        
        # Try to start listening
        print("\n🚀 Testing start_listening()...")
        voice_control.start_listening()
        
        # Wait a moment and check status again
        time.sleep(2)
        print(f"Listening status after start: {voice_control.listening}")
        
        # Get full status
        status = voice_control.get_voice_status()
        print(f"\nFull status: {status}")
        
        # Stop listening
        voice_control.stop_listening()
        print("✅ Voice control stopped")
        
        return True
        
    except Exception as e:
        print(f"❌ Voice control test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_service_voice_control():
    """Check voice control through the service manager API"""
    print("\n🌐 Service API Test:")
    
    try:
        import requests
        response = requests.get('http://localhost:5000/api/voice/status', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Response: {data}")
            
            if data.get('success'):
                voice_data = data.get('data', {})
                print(f"Voice enabled: {voice_data.get('enabled')}")
                print(f"Voice listening: {voice_data.get('listening')}")
                print(f"Wake word: {voice_data.get('wake_word')}")
            else:
                print(f"❌ API returned error: {data}")
        else:
            print(f"❌ API request failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Service API test failed: {e}")

def main():
    print("🔍 Bible Clock Voice Control Debug")
    print("=" * 50)
    
    # Check audio devices
    check_audio_devices()
    
    # Check dependencies
    if not check_voice_dependencies():
        print("\n❌ Missing dependencies. Please install with:")
        print("pip install pyttsx3 SpeechRecognition pyaudio")
        return
    
    # Test voice control creation
    if not test_voice_control_creation():
        print("\n❌ Voice control creation failed")
        return
    
    # Test service API
    check_service_voice_control()
    
    print("\n✅ Debug complete!")

if __name__ == '__main__':
    main()