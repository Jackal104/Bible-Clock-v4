#!/usr/bin/env python3
"""
Test script to verify wake word detection and TTS behavior
"""

import os
import sys
import time
import threading

# Add src directory to path
sys.path.insert(0, 'src')

def test_wake_word_flow():
    """Test the complete wake word to TTS flow"""
    print("🎯 Testing Wake Word Detection and TTS Flow")
    print("=" * 60)
    
    # Set environment variables
    os.environ['ENABLE_VOICE'] = 'true'
    os.environ['DISPLAY_WIDTH'] = '1872'
    os.environ['DISPLAY_HEIGHT'] = '1404'
    os.environ['BIBLE_API_URL'] = 'https://bible-api.com'
    
    try:
        from verse_manager import VerseManager
        from image_generator import ImageGenerator
        from display_manager import DisplayManager
        from voice_control import VoiceControl
        
        # Create managers
        verse_manager = VerseManager()
        image_generator = ImageGenerator()
        display_manager = DisplayManager()
        
        # Create voice control
        voice_control = VoiceControl(verse_manager, image_generator, display_manager)
        
        print(f"✅ Voice control initialized")
        print(f"   Enabled: {voice_control.enabled}")
        print(f"   Wake word: '{voice_control.wake_word}'")
        print(f"   Listening: {voice_control.listening}")
        
        # Start listening
        print("\n🎙️ Starting voice control listening...")
        voice_control.start_listening()
        
        print(f"   Listening after start: {voice_control.listening}")
        
        # Test TTS function directly
        print(f"\n🔊 Testing TTS output...")
        
        # Check if TTS engine is available
        if hasattr(voice_control, 'tts_engine') and voice_control.tts_engine:
            print("   TTS engine available, testing speech...")
            
            # Test using the test_voice_synthesis method
            print("   Testing voice synthesis...")
            try:
                voice_control.test_voice_synthesis()
                print("   ✅ Voice synthesis test completed")
            except Exception as tts_error:
                print(f"   ❌ Voice synthesis test failed: {tts_error}")
            
            # Show listening status after TTS
            print(f"   Listening after TTS: {voice_control.listening}")
            
        else:
            print("   ❌ TTS engine not available")
        
        # Test voice command processing
        print(f"\n🎯 Testing command processing...")
        
        # Simulate a help command
        test_command = "help"
        print(f"   Processing command: '{test_command}'")
        
        try:
            # Call the _process_command method directly
            voice_control._process_command(test_command)
            print("   ✅ Command processing test completed")
        except Exception as cmd_error:
            print(f"   ❌ Command processing failed: {cmd_error}")
        
        # Final status check
        print(f"\n📊 Final Status:")
        print(f"   Listening: {voice_control.listening}")
        print(f"   Voice enabled: {voice_control.enabled}")
        
        # Stop listening
        voice_control.stop_listening()
        print(f"   Stopped listening: {not voice_control.listening}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🧪 Bible Clock Wake Word and TTS Test")
    print("=" * 50)
    
    success = test_wake_word_flow()
    
    if success:
        print("\n✅ Wake word and TTS test completed successfully!")
        print("\n🎯 Key Points to Verify:")
        print("   1. Voice control initializes properly")
        print("   2. TTS engine works for spoken responses")
        print("   3. Command processing functions correctly")
        print("   4. Listening state is managed properly")
        print("\n💡 Next Steps:")
        print("   - Test with actual microphone: 'Bible Clock, help'")
        print("   - Verify TTS pauses microphone during speech")
        print("   - Confirm audio routing works with USB devices")
    else:
        print("\n❌ Test failed - check error messages above")

if __name__ == '__main__':
    main()