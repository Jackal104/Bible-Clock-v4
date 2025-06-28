#!/bin/bash
# Quick ReSpeaker HAT microphone test commands

echo "🎤 Quick ReSpeaker HAT Microphone Test"
echo "======================================"
echo

echo "1️⃣  Checking if ReSpeaker HAT is detected..."
echo "📋 Available sound cards:"
cat /proc/asound/cards
echo

echo "2️⃣  Checking ALSA recording devices..."
echo "📥 Recording devices:"
arecord -l
echo

echo "3️⃣  Testing microphone recording (5 seconds)..."
echo "🔴 Recording... speak into the microphone!"
arecord -D hw:1,0 -f cd -t wav -d 5 test_quick.wav 2>/dev/null || \
arecord -f cd -t wav -d 5 test_quick.wav 2>/dev/null
echo "⏹️  Recording complete"
echo

echo "4️⃣  Playing back recording..."
echo "🔊 Playing back..."
aplay test_quick.wav 2>/dev/null
echo "✅ Playback complete"
echo

echo "5️⃣  Checking ReSpeaker LED status..."
if [ -d "/sys/class/leds" ]; then
    echo "💡 Available LEDs:"
    ls /sys/class/leds/ | grep -i seeed || echo "   No ReSpeaker LEDs found"
else
    echo "   LED control not available"
fi
echo

echo "6️⃣  Testing volume levels..."
echo "📊 Current ALSA mixer settings:"
if command -v amixer &> /dev/null; then
    amixer scontrols | head -5
    echo "   (Use 'alsamixer' to adjust levels)"
else
    echo "   amixer not available"
fi
echo

echo "🎉 Quick test complete!"
echo "📋 Results:"
echo "- If you heard your voice played back, microphone is working ✅"
echo "- If ReSpeaker appears in sound cards, HAT is detected ✅"
echo "- Run './test_microphone.py' for detailed testing"
echo "- Check test_quick.wav file was created"

ls -la test_quick.wav 2>/dev/null && echo "✅ Audio file created successfully" || echo "❌ Audio file not created"