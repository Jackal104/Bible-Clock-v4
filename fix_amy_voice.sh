#!/bin/bash
"""
Quick fix for Amy voice download on Pi
Fixes the wget line break issue
"""

echo "🔧 Fixing Amy voice download..."
echo "==============================="

# Create directory
mkdir -p ~/.local/share/piper/voices
cd ~/.local/share/piper/voices

echo "📁 Working in: $(pwd)"

# Download Amy voice (fixed commands)
echo "⬇️ Downloading Amy voice model..."
wget -O "en_US-amy-medium.onnx" "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx"

echo "⬇️ Downloading Amy voice config..."
wget -O "en_US-amy-medium.onnx.json" "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/amy/medium/en_US-amy-medium.onnx.json"

# Verify downloads
if [ -f "en_US-amy-medium.onnx" ] && [ -f "en_US-amy-medium.onnx.json" ]; then
    echo "✅ Amy voice downloaded successfully!"
    echo "   Model: $(ls -lh en_US-amy-medium.onnx | awk '{print $5}')"
    echo "   Config: $(ls -lh en_US-amy-medium.onnx.json | awk '{print $5}')"
    
    # Test the voice
    echo "🧪 Testing Amy voice..."
    if echo "Bible Clock voice test with Amy" | piper --model "en_US-amy-medium.onnx" --output_file "test_amy.wav" 2>/dev/null; then
        echo "✅ Amy voice test successful!"
        rm -f test_amy.wav
    else
        echo "⚠️ Voice test failed (but files downloaded correctly)"
    fi
else
    echo "❌ Download failed"
    exit 1
fi

echo ""
echo "🎯 Amy voice is ready!"
echo "💡 Run the full voice download script for more options:"
echo "   ./download_piper_voices.sh"