#!/usr/bin/env python3
"""
Simple pipeline test without audio playback
"""

import os
from openai import OpenAI
import subprocess
import tempfile
from pathlib import Path

def test_chatgpt():
    """Test ChatGPT API"""
    print("🤖 Testing ChatGPT...")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("   ❌ No API key found")
        return None
    
    try:
        client = OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful Bible study assistant."},
                {"role": "user", "content": "What does John 3:16 say?"}
            ],
            max_tokens=100
        )
        
        answer = response.choices[0].message.content.strip()
        print(f"   ✅ Response: {answer[:100]}...")
        return answer
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def test_piper(text):
    """Test Piper TTS"""
    print("🎙️ Testing Piper TTS...")
    
    try:
        model_path = Path.home() / ".local" / "share" / "piper" / "voices" / "en_US-amy-medium.onnx"
        
        if not model_path.exists():
            print(f"   ❌ Model not found: {model_path}")
            return False
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        result = subprocess.run([
            './piper/piper',
            '--model', str(model_path),
            '--output_file', temp_path
        ], input=text, text=True, capture_output=True)
        
        if result.returncode == 0:
            file_size = os.path.getsize(temp_path)
            print(f"   ✅ Generated {file_size} byte audio file: {temp_path}")
            return True
        else:
            print(f"   ❌ Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("📋 Bible Clock Pipeline Test")
    print("=" * 40)
    
    # Test ChatGPT
    response = test_chatgpt()
    if not response:
        print("❌ ChatGPT test failed")
        return
    
    # Test Piper TTS
    if test_piper(response):
        print("\n✅ Pipeline test successful!")
        print("   - ChatGPT: Working")
        print("   - Piper TTS: Working")
        print("   - Audio files generated successfully")
    else:
        print("\n❌ Piper TTS test failed")

if __name__ == "__main__":
    main()