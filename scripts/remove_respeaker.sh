#!/bin/bash
# Remove ReSpeaker HAT configuration and prepare for USB audio

echo "🗑️  Removing ReSpeaker HAT configuration..."
echo "=========================================="

# Backup current boot config
sudo cp /boot/config.txt /boot/config.txt.backup
echo "✅ Backed up /boot/config.txt"

# Remove ReSpeaker HAT overlay from boot config
sudo sed -i '/dtoverlay=seeed-2mic-voicecard/d' /boot/config.txt
echo "✅ Removed ReSpeaker HAT overlay"

# Remove I2S if only used for ReSpeaker (keep if needed for other devices)
echo "⚠️  I2S interface left enabled (may be needed for e-ink display)"

# Remove ALSA configuration for ReSpeaker
if [ -f ~/.asoundrc ]; then
    mv ~/.asoundrc ~/.asoundrc.respeaker.backup
    echo "✅ Backed up and removed ReSpeaker ALSA config"
fi

# Remove PulseAudio configuration for ReSpeaker
if [ -f ~/.pulse/default.pa ]; then
    mv ~/.pulse/default.pa ~/.pulse/default.pa.respeaker.backup
    echo "✅ Backed up and removed ReSpeaker PulseAudio config"
fi

# Kill any running PulseAudio processes
pulseaudio --kill 2>/dev/null || true
echo "✅ Stopped PulseAudio"

echo ""
echo "🎵 ReSpeaker HAT configuration removed!"
echo "📋 Next steps:"
echo "   1. Reboot to apply changes: sudo reboot"
echo "   2. Connect USB microphone and speaker"
echo "   3. Run USB audio setup script (coming tomorrow)"
echo ""
echo "💾 Backups created:"
echo "   - /boot/config.txt.backup"
echo "   - ~/.asoundrc.respeaker.backup"
echo "   - ~/.pulse/default.pa.respeaker.backup"