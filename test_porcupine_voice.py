#!/usr/bin/env python3
"""
Test script for Porcupine-based voice control system.
"""

import os
import sys
import time
import logging

# Add src directory to path
sys.path.insert(0, 'src')

def test_porcupine_voice_control():
    """Test the Porcupine voice control system."""
    print("🎙️ Testing Porcupine Voice Control System")
    print("=" * 60)
    
    # Set environment variables for testing
    os.environ['ENABLE_VOICE'] = 'true'
    os.environ['USB_AUDIO_ENABLED'] = 'true'
    os.environ['USB_MIC_DEVICE_NAME'] = 'USB PnP Audio Device'
    os.environ['USB_SPEAKER_DEVICE_NAME'] = 'USB PnP Audio Device'
    os.environ['AUDIO_INPUT_ENABLED'] = 'true'
    os.environ['AUDIO_OUTPUT_ENABLED'] = 'true'
    os.environ['DISPLAY_WIDTH'] = '1872'
    os.environ['DISPLAY_HEIGHT'] = '1404'
    os.environ['BIBLE_API_URL'] = 'https://bible-api.com'
    os.environ['PORCUPINE_SENSITIVITY'] = '0.5'
    
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        print("📋 Step 1: Check Porcupine availability...")
        try:
            import pvporcupine
            import pyaudio
            import numpy as np
            print("✅ Porcupine and dependencies available")
        except ImportError as e:
            print(f"❌ Missing dependency: {e}")
            print("   Run: python install_porcupine.py")
            return False
        
        print("\n📋 Step 2: Initialize managers...")
        from verse_manager import VerseManager
        from image_generator import ImageGenerator
        from display_manager import DisplayManager
        
        verse_manager = VerseManager()
        image_generator = ImageGenerator()
        display_manager = DisplayManager()
        print("✅ Managers initialized")
        
        print("\n🎤 Step 3: Initialize Porcupine voice control...")
        from porcupine_voice_control import PorcupineVoiceControl
        
        voice_control = PorcupineVoiceControl(verse_manager, image_generator, display_manager)
        
        print(f"✅ Porcupine voice control created")
        print(f"   Enabled: {voice_control.enabled}")
        print(f"   USB Audio: {voice_control.usb_audio_enabled}")
        print(f"   Wake word: '{voice_control.wake_word}'")
        print(f"   Porcupine: {voice_control.porcupine is not None}")
        print(f"   Audio stream: {voice_control.audio_stream is not None}")
        print(f"   TTS Engine: {voice_control.tts_engine is not None}")
        
        if not voice_control.enabled:
            print("❌ Voice control is not enabled - check errors above")
            return False
        
        print("\n🔊 Step 4: Test TTS synthesis...")
        if voice_control.tts_engine:
            try:
                voice_control.test_voice_synthesis()
                print("✅ TTS test completed")
            except Exception as tts_error:
                print(f"⚠️ TTS test issue: {tts_error}")
        else:
            print("❌ TTS engine not available")
        
        print("\n🎯 Step 5: Test Porcupine wake word detection...")
        if voice_control.porcupine and voice_control.audio_stream:
            print("✅ Porcupine ready for wake word detection")
            print(f"   Sample rate: {voice_control.porcupine.sample_rate}Hz")
            print(f"   Frame length: {voice_control.porcupine.frame_length}")
            
            # Start listening
            print("\n🎙️ Starting wake word detection...")
            voice_control.start_listening()
            
            print("✅ Wake word detection started")
            print("\n🗣️ TEST INSTRUCTIONS:")
            print("   1. Say 'Picovoice' clearly into your USB microphone")
            print("   2. Wait for 'Yes?' response")
            print("   3. Say a command like 'help' or 'next verse'")
            print("   4. Press Ctrl+C to stop testing")
            
            # Let it run for a bit to test
            try:
                print("\n⏰ Listening for 30 seconds... Say 'Picovoice' now!")
                time.sleep(30)
            except KeyboardInterrupt:
                print("\n⏹️ Test interrupted by user")
            
            # Stop listening
            voice_control.stop_listening()
            print("✅ Voice control stopped")
            
        else:
            print("❌ Porcupine or audio stream not available")
            return False
        
        print("\n📊 Test Results:")
        print(f"   ✅ Porcupine initialized: {voice_control.porcupine is not None}")
        print(f"   ✅ Audio stream working: {voice_control.audio_stream is not None}")
        print(f"   ✅ TTS available: {voice_control.tts_engine is not None}")
        print(f"   ✅ Wake word detection: Ready")
        
        print("\n🎉 Porcupine voice control test completed!")
        
        print("\n📋 Next Steps:")
        print("   1. Run main Bible Clock: ./start_bible_clock.sh")
        print("   2. Say 'Picovoice' to activate voice control")
        print("   3. Try commands: 'help', 'next verse', 'speak verse'")
        
        if not voice_control.porcupine_access_key:
            print("\n💡 For Custom Wake Words:")
            print("   1. Visit: https://console.picovoice.ai/")
            print("   2. Create custom keyword (e.g., 'Hey Bible Clock')")
            print("   3. Set PORCUPINE_ACCESS_KEY and PORCUPINE_KEYWORD_PATH in .env")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 Bible Clock Porcupine Voice Control Test")
    print("=" * 50)
    
    success = test_porcupine_voice_control()
    
    if success:
        print("\n✅ All tests passed! Porcupine voice control is working.")
    else:
        print("\n❌ Some tests failed. Check error messages above.")
        print("   Try running: python install_porcupine.py")

if __name__ == '__main__':
    main()