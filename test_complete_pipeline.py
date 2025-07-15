#!/usr/bin/env python3
"""
Test complete voice pipeline: Speech -> ChatGPT -> Piper TTS
"""

import speech_recognition as sr
import openai
import subprocess
import tempfile
import wave
import os
from pathlib import Path

def test_complete_pipeline():
    print("🔄 Testing complete voice pipeline...")
    print("=" * 50)
    
    # Set up OpenAI API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OPENAI_API_KEY found in environment variables")
        print("   Add it to your .env file or export OPENAI_API_KEY=your_key")
        return False
    
    openai.api_key = api_key
    
    try:
        # Step 1: Speech to text
        print("1. 🎤 Converting speech to text...")
        r = sr.Recognizer()
        
        if not os.path.exists('speech_test.wav'):
            print("   ❌ speech_test.wav not found. Please record first:")
            print("   arecord -f S16_LE -r 16000 -c 1 -d 3 speech_test.wav")
            return False
        
        with wave.open('speech_test.wav', 'rb') as audio_file:
            audio_data = sr.AudioData(
                audio_file.readframes(audio_file.getnframes()),
                audio_file.getframerate(), 
                audio_file.getsampwidth()
            )
        
        text = r.recognize_google(audio_data)
        print(f"   ✅ You said: {text}")
        
        # Step 2: Send to ChatGPT
        print("2. 🤖 Sending to ChatGPT...")
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=[
                {
                    'role': 'system', 
                    'content': 'You are a helpful Bible study assistant. Provide thoughtful, concise responses about the Bible, Christianity, and faith. Keep responses under 100 words.'
                },
                {'role': 'user', 'content': text}
            ],
            max_tokens=100,
            temperature=0.7
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"   ✅ ChatGPT response: {answer}")
        
        # Step 3: Convert to speech with Piper
        print("3. 🎙️ Converting to speech with Piper...")
        model_path = Path.home() / '.local' / 'share' / 'piper' / 'voices' / 'en_US-amy-medium.onnx'
        
        if not model_path.exists():
            print(f"   ❌ Piper model not found: {model_path}")
            print("   Run: python3 install_piper_tts.py")
            return False
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        result = subprocess.run([
            'piper', 
            '--model', str(model_path), 
            '--output_file', temp_path
        ], input=answer, text=True, capture_output=True)
        
        if result.returncode == 0:
            print("4. 🔊 Playing response...")
            subprocess.run(['aplay', temp_path], check=True)
            print("✅ Complete pipeline successful!")
            
            # Clean up
            try:
                os.unlink(temp_path)
            except:
                pass
            
            return True
        else:
            print(f"   ❌ Piper TTS failed: {result.stderr}")
            return False
            
    except sr.UnknownValueError:
        print("   ❌ Could not understand the audio")
        return False
    except sr.RequestError as e:
        print(f"   ❌ Speech recognition error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Pipeline failed: {e}")
        return False

if __name__ == "__main__":
    test_complete_pipeline()