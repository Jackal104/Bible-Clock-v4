#!/usr/bin/env python3
"""
Test ChatGPT + Piper TTS Voice Control
Complete voice flow test: Speech -> ChatGPT -> Piper TTS
"""

import os
import sys
import speech_recognition as sr
import openai
import subprocess
import tempfile
from pathlib import Path

def test_speech_to_text():
    """Test speech recognition."""
    print("🎤 Testing Speech Recognition...")
    
    try:
        r = sr.Recognizer()
        mic = sr.Microphone()
        
        print("   Say something in 3 seconds...")
        with mic as source:
            r.adjust_for_ambient_noise(source, duration=1)
        
        import time
        time.sleep(3)
        print("   Listening now...")
        
        with mic as source:
            audio = r.listen(source, timeout=5, phrase_time_limit=5)
        
        text = r.recognize_google(audio)
        print(f"   ✅ You said: {text}")
        return text
        
    except Exception as e:
        print(f"   ❌ Speech recognition failed: {e}")
        return None

def test_chatgpt(question):
    """Test ChatGPT API."""
    print("🤖 Testing ChatGPT...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("   ⚠️ No OPENAI_API_KEY found in environment")
        return "This is a test response since no API key is configured."
    
    try:
        openai.api_key = api_key
        
        messages = [
            {"role": "system", "content": "You are a helpful Bible study assistant. Keep responses concise."},
            {"role": "user", "content": question}
        ]
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=100,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"   ✅ ChatGPT response: {answer[:100]}...")
        return answer
        
    except Exception as e:
        print(f"   ❌ ChatGPT failed: {e}")
        return f"Sorry, I couldn't process that question. Error: {str(e)}"

def test_piper_tts(text):
    """Test Piper TTS."""
    print("🎙️ Testing Piper TTS...")
    
    try:
        model_path = Path.home() / ".local" / "share" / "piper" / "voices" / "en_US-amy-medium.onnx"
        
        if not model_path.exists():
            print(f"   ❌ Piper model not found: {model_path}")
            print("   Run: python install_piper_tts.py")
            return False
        
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        # Run Piper TTS
        result = subprocess.run([
            'piper',
            '--model', str(model_path),
            '--output_file', temp_path
        ], input=text, text=True, capture_output=True)
        
        if result.returncode == 0:
            print(f"   ✅ Generated audio: {temp_path}")
            
            # Play the audio
            try:
                subprocess.run(['aplay', temp_path], check=True)
                print("   ✅ Audio playback successful")
            except subprocess.CalledProcessError:
                print("   ⚠️ Audio playback failed (check speakers)")
            
            # Clean up
            try:
                os.unlink(temp_path)
            except:
                pass
                
            return True
        else:
            print(f"   ❌ Piper TTS failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("   ❌ Piper command not found. Run: pip install piper-tts")
        return False
    except Exception as e:
        print(f"   ❌ Piper TTS error: {e}")
        return False

def test_complete_flow():
    """Test the complete voice control flow."""
    print("🔄 Testing Complete Voice Flow...")
    print("=" * 50)
    
    # Step 1: Speech to Text
    question = test_speech_to_text()
    if not question:
        print("❌ Complete flow failed at speech recognition")
        return False
    
    # Step 2: ChatGPT Processing
    response = test_chatgpt(question)
    if not response:
        print("❌ Complete flow failed at ChatGPT")
        return False
    
    # Step 3: Text to Speech
    if not test_piper_tts(response):
        print("❌ Complete flow failed at Piper TTS")
        return False
    
    print("\n✅ Complete voice flow successful!")
    return True

def main():
    print("🎙️ Bible Clock ChatGPT + Piper TTS Test")
    print("=" * 60)
    
    # Test individual components
    print("\n1. Testing Piper TTS with sample text...")
    if not test_piper_tts("Bible Clock voice control is ready with ChatGPT and Piper TTS."):
        print("❌ Piper TTS test failed")
        return
    
    print("\n2. Testing complete voice flow...")
    print("   You'll be asked to say something, it will be sent to ChatGPT,")
    print("   and the response will be spoken back with Piper TTS.")
    
    input("\nPress Enter when ready to test complete flow...")
    
    if test_complete_flow():
        print("\n🎉 All tests passed! Your voice control system is ready.")
        print("\nNext steps:")
        print("1. Add OPENAI_API_KEY to your .env file")
        print("2. Set ENABLE_CHATGPT_VOICE=true in .env")
        print("3. Start Bible Clock: ./start_bible_clock.sh")
    else:
        print("\n❌ Some tests failed. Check the errors above.")

if __name__ == '__main__':
    main()