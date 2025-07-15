#!/usr/bin/env python3
"""
Direct test of OpenAI TTS API using requests library to bypass OpenAI client issues.
"""

import os
import requests
import subprocess
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_tts_direct():
    """Test OpenAI TTS using direct HTTP requests."""
    
    api_key = os.getenv('OPENAI_API_KEY', '').replace('\n', '').replace('\r', '').replace(' ', '')
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not set")
        return False
    
    print(f"✅ OpenAI API key found (first 10 chars): {api_key[:10]}...")
    
    # Direct API call to OpenAI TTS
    url = "https://api.openai.com/v1/audio/speech"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "tts-1",
        "voice": "nova",
        "input": "Hello, this is a test of OpenAI TTS Nova voice using direct HTTP request.",
        "response_format": "mp3"
    }
    
    print("🔊 Making direct HTTP request to OpenAI TTS...")
    
    try:
        # Make request with longer timeout
        response = requests.post(
            url, 
            headers=headers, 
            json=data, 
            timeout=120,  # 2 minute timeout
            stream=True   # Stream the response
        )
        
        if response.status_code == 200:
            print("✅ OpenAI TTS request successful!")
            
            # Save to temporary file
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                for chunk in response.iter_content(chunk_size=8192):
                    tmp.write(chunk)
                tmp_path = tmp.name
            
            print(f"🔊 Audio saved to: {tmp_path}")
            
            # Try to play with aplay (convert from mp3 to wav first if needed)
            print("🔊 Testing playback...")
            try:
                # Method 1: Try ffplay directly with mp3
                result = subprocess.run([
                    "ffplay", "-nodisp", "-autoexit", "-volume", "50",
                    tmp_path
                ], capture_output=True, timeout=30)
                
                if result.returncode == 0:
                    print("✅ Audio playback successful with ffplay!")
                    return True
                else:
                    print(f"❌ ffplay failed: {result.stderr.decode()}")
                    
            except subprocess.TimeoutExpired:
                print("⏰ Audio playback timed out")
            except Exception as e:
                print(f"❌ Audio playback failed: {e}")
            
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
                    
        else:
            print(f"❌ OpenAI API request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 2 minutes")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Direct OpenAI TTS HTTP Test")
    print("=" * 40)
    
    success = test_openai_tts_direct()
    
    print("\n" + "=" * 40)
    if success:
        print("✅ Direct OpenAI TTS test PASSED")
    else:
        print("❌ Direct OpenAI TTS test FAILED")
        print("💡 This suggests a network connectivity issue to OpenAI's TTS endpoint")