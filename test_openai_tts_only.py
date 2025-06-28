#!/usr/bin/env python3
"""
Simple test script to isolate OpenAI TTS Nova voice issues.
Tests OpenAI TTS without the full voice assistant complexity.
"""

import os
import subprocess
import tempfile
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_tts():
    """Test OpenAI TTS Nova voice with direct aplay streaming."""
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY', '')
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not set")
        return False
    
    print(f"✅ OpenAI API key found (first 10 chars): {api_key[:10]}...")
    
    # Initialize OpenAI client
    try:
        client = OpenAI(api_key=api_key)
        print("✅ OpenAI client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize OpenAI client: {e}")
        return False
    
    # Test text
    test_text = "Hello, this is a test of the OpenAI TTS Nova voice. Can you hear me clearly?"
    print(f"🔊 Testing text: {test_text}")
    
    try:
        # Generate speech using OpenAI TTS API
        print("🔊 Requesting OpenAI TTS...")
        response = client.audio.speech.create(
            model="tts-1",
            voice="nova",  # High-quality ChatGPT-like voice
            input=test_text,
            response_format="wav"  # WAV format for immediate streaming
        )
        print("✅ OpenAI TTS response received")
        
        # Test USB speaker device configuration
        usb_speaker_device = 'plughw:2,0'
        print(f"🔊 Using USB speaker device: {usb_speaker_device}")
        
        # Method 1: Direct aplay streaming (current implementation)
        print("🔊 Testing direct aplay streaming...")
        try:
            aplay_process = subprocess.Popen([
                "aplay", 
                "-D", usb_speaker_device,
                "-f", "S16_LE",  # 16-bit little endian
                "-r", "24000",   # OpenAI TTS default sample rate
                "-c", "1",       # Mono
                "--buffer-size=512",  # Small buffer for low latency
                "-"  # Read from stdin
            ], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            
            stdout, stderr = aplay_process.communicate(input=response.content)
            
            if aplay_process.returncode == 0:
                print("✅ Direct aplay streaming SUCCESS")
                return True
            else:
                print(f"❌ Direct aplay failed: {stderr.decode()}")
        
        except Exception as e:
            print(f"❌ Direct aplay exception: {e}")
        
        # Method 2: Fallback with ffplay
        print("🔊 Testing ffplay fallback...")
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(response.content)
                tmp_path = tmp.name
            
            result = subprocess.run([
                "ffplay", "-nodisp", "-autoexit", 
                "-af", "aformat=sample_rates=48000",
                tmp_path
            ], capture_output=True, text=True)
            
            os.unlink(tmp_path)
            
            if result.returncode == 0:
                print("✅ ffplay fallback SUCCESS")
                return True
            else:
                print(f"❌ ffplay failed: {result.stderr}")
        
        except Exception as e:
            print(f"❌ ffplay exception: {e}")
            
        # Method 3: Test with default audio device
        print("🔊 Testing with default audio device...")
        try:
            aplay_process = subprocess.Popen([
                "aplay", 
                "-f", "S16_LE",
                "-r", "24000",
                "-c", "1",
                "-"
            ], stdin=subprocess.PIPE, stderr=subprocess.PIPE)
            
            stdout, stderr = aplay_process.communicate(input=response.content)
            
            if aplay_process.returncode == 0:
                print("✅ Default device aplay SUCCESS")
                return True
            else:
                print(f"❌ Default aplay failed: {stderr.decode()}")
        
        except Exception as e:
            print(f"❌ Default aplay exception: {e}")
        
    except Exception as e:
        print(f"❌ OpenAI TTS request failed: {e}")
        return False
    
    return False

def check_audio_devices():
    """Check available audio devices."""
    print("\n🔍 Checking audio devices...")
    
    try:
        result = subprocess.run(["aplay", "-l"], capture_output=True, text=True)
        print("Available playback devices:")
        print(result.stdout)
    except Exception as e:
        print(f"❌ Could not list audio devices: {e}")

if __name__ == "__main__":
    print("🧪 OpenAI TTS Nova Voice Test")
    print("=" * 40)
    
    check_audio_devices()
    
    print("\n🔊 Testing OpenAI TTS...")
    success = test_openai_tts()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ OpenAI TTS Nova voice test PASSED")
    else:
        print("❌ OpenAI TTS Nova voice test FAILED")