#!/usr/bin/env python3
"""
Install Piper TTS and ChatGPT integration for Bible Clock
High-quality neural voice synthesis with AI Bible Q&A
"""

import subprocess
import sys
import os
import urllib.request
import json
from pathlib import Path

def install_piper_tts():
    """Install Piper TTS package."""
    print("📦 Installing Piper TTS...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "piper-tts"])
        print("✅ Piper TTS installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install Piper TTS: {e}")
        return False

def install_openai():
    """Install OpenAI package for ChatGPT integration."""
    print("📦 Installing OpenAI API...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openai"])
        print("✅ OpenAI API installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install OpenAI: {e}")
        return False

def download_piper_voice():
    """Download high-quality English voice model."""
    print("🎤 Downloading Piper voice model...")
    
    # Create voices directory
    voices_dir = Path.home() / ".local" / "share" / "piper" / "voices"
    voices_dir.mkdir(parents=True, exist_ok=True)
    
    # Amy voice model URLs
    model_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx"
    config_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json"
    
    model_path = voices_dir / "en_US-amy-medium.onnx"
    config_path = voices_dir / "en_US-amy-medium.onnx.json"
    
    try:
        # Download model file
        if not model_path.exists():
            print("   Downloading voice model...")
            urllib.request.urlretrieve(model_url, model_path)
            print(f"   ✅ Downloaded: {model_path}")
        else:
            print(f"   ✅ Model already exists: {model_path}")
        
        # Download config file
        if not config_path.exists():
            print("   Downloading voice config...")
            urllib.request.urlretrieve(config_url, config_path)
            print(f"   ✅ Downloaded: {config_path}")
        else:
            print(f"   ✅ Config already exists: {config_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to download voice model: {e}")
        return False

def test_piper_voice():
    """Test Piper TTS with downloaded voice."""
    print("🧪 Testing Piper TTS...")
    
    model_path = Path.home() / ".local" / "share" / "piper" / "voices" / "en_US-amy-medium.onnx"
    
    if not model_path.exists():
        print("❌ Voice model not found")
        return False
    
    try:
        # Test text
        test_text = "Bible Clock voice control is ready. Say Bible Clock help to learn commands."
        output_file = "test_piper_voice.wav"
        
        # Run Piper TTS
        result = subprocess.run([
            'piper',
            '--model', str(model_path),
            '--output_file', output_file
        ], input=test_text, text=True, capture_output=True)
        
        if result.returncode == 0:
            print(f"✅ Piper TTS test successful: {output_file}")
            
            # Test playback
            try:
                subprocess.run(['aplay', output_file], check=True)
                print("✅ Audio playback successful")
            except subprocess.CalledProcessError:
                print("⚠️ Audio playback failed (check speakers)")
            
            return True
        else:
            print(f"❌ Piper TTS failed: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("❌ Piper command not found. Make sure piper-tts is installed correctly.")
        return False
    except Exception as e:
        print(f"❌ Piper test failed: {e}")
        return False

def create_env_template():
    """Add ChatGPT settings to .env template."""
    env_additions = """
# ChatGPT Integration Settings
OPENAI_API_KEY=
CHATGPT_MODEL=gpt-3.5-turbo
CHATGPT_MAX_TOKENS=150
CHATGPT_TEMPERATURE=0.7

# Piper TTS Settings
PIPER_VOICE_MODEL=en_US-amy-medium.onnx
PIPER_VOICE_SPEED=1.0
PIPER_VOICE_VOLUME=0.9
"""
    
    print("📝 Updating .env template with ChatGPT settings...")
    
    # Check if .env exists
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            existing_env = f.read()
        
        # Add ChatGPT settings if not present
        if 'OPENAI_API_KEY' not in existing_env:
            print("   Adding ChatGPT settings to existing .env...")
            with open('.env', 'a') as f:
                f.write('\n' + env_additions)
            print("✅ ChatGPT settings added to .env")
        else:
            print("   ChatGPT settings already in .env")
    else:
        # Create new .env with full template
        with open('.env.template', 'w') as f:
            f.write(env_additions)
        print("✅ .env.template created with ChatGPT settings")

def show_usage_instructions():
    """Show usage instructions for Piper TTS + ChatGPT."""
    print("\n🎯 Piper TTS + ChatGPT Setup Complete!")
    print("=" * 60)
    
    print("\n📋 Configuration:")
    print("1. **Add your OpenAI API key to .env:**")
    print("   OPENAI_API_KEY=your_api_key_here")
    print("   Get one at: https://platform.openai.com/api-keys")
    print()
    print("2. **Voice Model:**")
    print("   Location: ~/.local/share/piper/voices/en_US-amy-medium.onnx")
    print("   Quality: Neural, female voice (Amy)")
    print()
    print("3. **Usage:**")
    print("   - Say 'Bible Clock' to activate")
    print("   - Ask Bible questions: 'What does John 3:16 say?'")
    print("   - Get explanations: 'What is the meaning of love in the Bible?'")
    print("   - Voice commands: 'help', 'next verse', 'previous verse'")
    print()
    print("4. **Test Commands:**")
    print("   echo 'Hello from Piper' | piper --model ~/.local/share/piper/voices/en_US-amy-medium.onnx --output_file test.wav && aplay test.wav")

def main():
    print("🎙️ Bible Clock Piper TTS + ChatGPT Setup")
    print("=" * 60)
    
    # Install Piper TTS
    if not install_piper_tts():
        print("❌ Setup failed - could not install Piper TTS")
        return False
    
    # Install OpenAI API
    if not install_openai():
        print("❌ Setup failed - could not install OpenAI")
        return False
    
    # Download voice model
    if not download_piper_voice():
        print("❌ Setup failed - could not download voice model")
        return False
    
    # Test Piper TTS
    if not test_piper_voice():
        print("❌ Setup failed - Piper TTS test failed")
        return False
    
    # Create .env template
    create_env_template()
    
    # Show usage instructions
    show_usage_instructions()
    
    print("\n✅ Piper TTS + ChatGPT setup completed successfully!")
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)