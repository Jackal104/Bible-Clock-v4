#!/usr/bin/env python3
"""
Test Piper TTS only
"""

import subprocess
import tempfile
import os
from pathlib import Path

def test_piper():
    """Test Piper TTS"""
    print("🎙️ Testing Piper TTS...")
    
    try:
        model_path = Path.home() / ".local" / "share" / "piper" / "voices" / "en_US-amy-medium.onnx"
        
        if not model_path.exists():
            print(f"   ❌ Model not found: {model_path}")
            return False
        
        test_text = "Bible Clock voice control is ready with ChatGPT and natural Amy voice. Say Bible Clock help to learn commands."
        
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_path = temp_file.name
        
        result = subprocess.run([
            './piper/piper',
            '--model', str(model_path),
            '--output_file', temp_path
        ], input=test_text, text=True, capture_output=True)
        
        if result.returncode == 0:
            file_size = os.path.getsize(temp_path)
            print(f"   ✅ Generated {file_size} byte audio file")
            print(f"   ✅ Audio saved to: {temp_path}")
            print(f"   📝 Text: {test_text}")
            return True
        else:
            print(f"   ❌ Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🎙️ Bible Clock Piper TTS Test")
    print("=" * 40)
    
    if test_piper():
        print("\n✅ Piper TTS test successful!")
        print("   Your voice system is ready for deployment on Pi")
    else:
        print("\n❌ Piper TTS test failed")

if __name__ == "__main__":
    main()