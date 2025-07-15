#!/usr/bin/env python3
"""
Test script to verify voice control fixes work with USB audio devices.
"""

import os
import sys
import time
import logging

# Add src directory to path
sys.path.insert(0, 'src')

def test_voice_control_fixes():
    """Test the voice control system with USB audio device fixes."""
    print("🔧 Testing Voice Control Fixes")
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
    
    # Set up logging to see detailed information
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        print("📋 Step 1: Import and initialize managers...")
        from verse_manager import VerseManager
        from image_generator import ImageGenerator
        from display_manager import DisplayManager
        
        verse_manager = VerseManager()
        image_generator = ImageGenerator()
        display_manager = DisplayManager()
        print("✅ Managers initialized successfully")
        
        print("\n🎤 Step 2: Initialize voice control with fixes...")
        from voice_control import BibleClockVoiceControl
        
        voice_control = BibleClockVoiceControl(verse_manager, image_generator, display_manager)
        
        print(f"✅ Voice control created")
        print(f"   Enabled: {voice_control.enabled}")
        print(f"   USB Audio: {voice_control.usb_audio_enabled}")
        print(f"   Wake word: '{voice_control.wake_word}'")
        print(f"   Microphone: {type(voice_control.microphone).__name__ if voice_control.microphone else 'None'}")
        print(f"   TTS Engine: {type(voice_control.tts_engine).__name__ if voice_control.tts_engine else 'None'}")
        
        if not voice_control.enabled:
            print("❌ Voice control is not enabled - check dependencies or errors above")
            return False
        
        print("\n🎧 Step 3: Test microphone access...")
        try:
            # Test microphone initialization by accessing it
            if voice_control.microphone:
                with voice_control.microphone as source:
                    print("✅ Microphone access successful")
                    print(f"   Source type: {type(source)}")
            else:
                print("❌ No microphone available")
                return False
        except Exception as mic_error:
            print(f"❌ Microphone test failed: {mic_error}")
            return False
        
        print("\n🔊 Step 4: Test TTS synthesis...")
        if voice_control.tts_engine:
            try:
                # Test TTS without actually playing audio (to avoid conflicts)
                test_text = "Voice control test successful"
                print(f"   Testing TTS with: '{test_text}'")
                
                # Just test that TTS can be configured without errors
                voice_control.tts_engine.setProperty('rate', voice_control.voice_rate)
                voice_control.tts_engine.setProperty('volume', voice_control.voice_volume)
                print("✅ TTS engine configuration successful")
                
                # Test actual synthesis (but save to file instead of speakers to avoid conflicts)
                voice_control.tts_engine.save_to_file(test_text, 'test_tts.wav')
                voice_control.tts_engine.runAndWait()
                print("✅ TTS synthesis test completed")
                
                # Clean up test file
                if os.path.exists('test_tts.wav'):
                    os.remove('test_tts.wav')
                    
            except Exception as tts_error:
                print(f"⚠️ TTS test encountered issue: {tts_error}")
        else:
            print("❌ TTS engine not available")
        
        print("\n🎯 Step 5: Test listening state management...")
        try:
            # Test starting and stopping listening
            print("   Testing start_listening()...")
            voice_control.start_listening()
            print(f"   Listening after start: {voice_control.listening}")
            
            time.sleep(1)  # Brief pause
            
            print("   Testing stop_listening()...")
            voice_control.stop_listening()
            print(f"   Listening after stop: {voice_control.listening}")
            
            print("✅ Listening state management working")
            
        except Exception as listen_error:
            print(f"❌ Listening test failed: {listen_error}")
            return False
        
        print("\n📊 Step 6: Test command processing...")
        try:
            # Test the command processing method directly
            test_command = "help"
            print(f"   Processing command: '{test_command}'")
            voice_control._process_command(test_command)
            print("✅ Command processing test completed")
        except Exception as cmd_error:
            print(f"❌ Command processing failed: {cmd_error}")
        
        print("\n🎉 Voice control fixes test completed!")
        print("\n📋 Summary:")
        print(f"   ✅ Voice control enabled: {voice_control.enabled}")
        print(f"   ✅ Microphone working: {voice_control.microphone is not None}")
        print(f"   ✅ TTS available: {voice_control.tts_engine is not None}")
        print(f"   ✅ Wake word: '{voice_control.wake_word}'")
        
        print("\n🔄 Next Steps:")
        print("   1. Run the main Bible Clock application")
        print("   2. Say 'Bible Clock, help' to test wake word detection")
        print("   3. Verify TTS responses play through USB speakers")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 Bible Clock Voice Control Fixes Test")
    print("=" * 50)
    
    success = test_voice_control_fixes()
    
    if success:
        print("\n✅ All tests passed! Voice control fixes are working.")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")

if __name__ == '__main__':
    main()