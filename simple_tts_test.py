#!/usr/bin/env python3
"""
Simple test to check OpenAI TTS functionality using existing voice_assistant.py
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_openai_tts():
    """Test OpenAI TTS using the existing VoiceAssistant class."""
    
    # Check if OpenAI API key exists
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key:
        logger.error("❌ OPENAI_API_KEY environment variable not set")
        return False
    
    logger.info(f"✅ OpenAI API key found (first 10 chars): {api_key[:10]}...")
    
    try:
        # Import the voice assistant
        from voice_assistant import VoiceAssistant
        
        # Create voice assistant instance
        logger.info("🔊 Creating VoiceAssistant instance...")
        va = VoiceAssistant()
        
        # Test text
        test_text = "Hello, this is a test of the OpenAI TTS Nova voice."
        logger.info(f"🔊 Testing text: {test_text}")
        
        # Test OpenAI TTS directly
        logger.info("🔊 Testing OpenAI TTS streaming...")
        va._play_openai_tts_stream(test_text)
        
        logger.info("✅ OpenAI TTS test completed")
        return True
        
    except ImportError as e:
        logger.error(f"❌ Failed to import VoiceAssistant: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ OpenAI TTS test failed: {e}")
        return False

def check_audio_setup():
    """Check audio device configuration."""
    logger.info("🔍 Checking audio setup...")
    
    try:
        import subprocess
        result = subprocess.run(["aplay", "-l"], capture_output=True, text=True)
        logger.info("Available audio devices:")
        print(result.stdout)
        
        # Test if USB speaker device exists
        if "card 2" in result.stdout:
            logger.info("✅ USB speaker (card 2) detected")
        else:
            logger.warning("⚠️  USB speaker (card 2) not found")
            
    except Exception as e:
        logger.error(f"❌ Audio device check failed: {e}")

if __name__ == "__main__":
    print("🧪 Simple OpenAI TTS Test")
    print("=" * 40)
    
    # Check audio setup first
    check_audio_setup()
    
    print("\n🔊 Testing OpenAI TTS...")
    success = test_openai_tts()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ OpenAI TTS test PASSED")
    else:
        print("❌ OpenAI TTS test FAILED")
        print("💡 Check:")
        print("   - OpenAI API key is set correctly")
        print("   - Audio devices are properly configured")
        print("   - USB speakers are connected and working")