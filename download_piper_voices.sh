#!/bin/bash
"""
Download Multiple Piper TTS Voices for Bible Clock
High-quality neural voices for natural speech
"""

echo "🎤 Downloading Piper TTS Voices..."
echo "=================================="

# Create voices directory
mkdir -p ~/.local/share/piper/voices
cd ~/.local/share/piper/voices

echo "📁 Voice directory: $(pwd)"
echo ""

# Function to download voice
download_voice() {
    local voice_name="$1"
    local voice_path="$2"
    
    echo "⬇️ Downloading $voice_name..."
    
    # Download model file
    if wget -O "${voice_name}.onnx" "https://huggingface.co/rhasspy/piper-voices/resolve/main/${voice_path}/${voice_name}.onnx"; then
        echo "   ✅ Model downloaded"
    else
        echo "   ❌ Model download failed"
        return 1
    fi
    
    # Download config file
    if wget -O "${voice_name}.onnx.json" "https://huggingface.co/rhasspy/piper-voices/resolve/main/${voice_path}/${voice_name}.onnx.json"; then
        echo "   ✅ Config downloaded"
    else
        echo "   ❌ Config download failed"
        return 1
    fi
    
    echo "   🎯 $voice_name ready!"
    echo ""
}

echo "🔄 Downloading recommended voices for Bible reading..."
echo ""

# Amy - Natural female voice (medium quality)
download_voice "en_US-amy-medium" "en/en_US/amy/medium"

# Kristin - Clear female voice (medium quality) 
download_voice "en_US-kristin-medium" "en/en_US/kristin/medium"

# Ryan - Professional male voice (medium quality)
download_voice "en_US-ryan-medium" "en/en_US/ryan/medium"

# Joe - Deep male voice (medium quality)
download_voice "en_US-joe-medium" "en/en_US/joe/medium"

# Kimberly - Warm female voice (medium quality)
download_voice "en_US-kimberly-medium" "en/en_US/kimberly/medium"

echo "📊 Voice Download Summary:"
echo "========================="
ls -lh *.onnx 2>/dev/null | while read line; do
    echo "✅ $(echo $line | awk '{print $9, $5}')"
done

echo ""
echo "🧪 Testing voices..."
echo "==================="

# Test each voice
for voice in en_US-amy-medium en_US-kristin-medium en_US-ryan-medium en_US-joe-medium en_US-kimberly-medium; do
    if [ -f "${voice}.onnx" ]; then
        echo "🎙️ Testing $voice..."
        test_text="For God so loved the world that he gave his one and only Son."
        
        if echo "$test_text" | piper --model "${voice}.onnx" --output_file "test_${voice}.wav" 2>/dev/null; then
            file_size=$(stat -c%s "test_${voice}.wav" 2>/dev/null || echo "0")
            echo "   ✅ Generated ${file_size} bytes"
            
            # Clean up test file
            rm -f "test_${voice}.wav"
        else
            echo "   ❌ Test failed"
        fi
    else
        echo "❌ $voice not found"
    fi
done

echo ""
echo "🎯 Voice Setup Complete!"
echo "======================="
echo ""
echo "📋 Available Voices:"
echo "• en_US-amy-medium     - Natural female (recommended)"
echo "• en_US-kristin-medium - Clear female" 
echo "• en_US-ryan-medium    - Professional male"
echo "• en_US-joe-medium     - Deep male"
echo "• en_US-kimberly-medium - Warm female"
echo ""
echo "🔧 To change voice in Bible Clock:"
echo "   Edit .env: PIPER_VOICE_MODEL=en_US-ryan-medium.onnx"
echo ""
echo "🧪 Test a voice:"
echo "   echo 'Bible verse test' | piper --model ~/.local/share/piper/voices/en_US-ryan-medium.onnx --output_file test.wav && aplay test.wav"