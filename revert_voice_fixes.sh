#!/bin/bash
# Script to revert voice control fixes if they cause issues

echo "Reverting voice control fixes..."

# Check if backup files exist
if [[ -f "src/porcupine_voice_control.py.backup" ]]; then
    echo "Restoring porcupine_voice_control.py from backup..."
    cp src/porcupine_voice_control.py.backup src/porcupine_voice_control.py
    echo "✓ porcupine_voice_control.py restored"
else
    echo "⚠ No backup found for porcupine_voice_control.py"
fi

if [[ -f "src/voice_control.py.backup" ]]; then
    echo "Restoring voice_control.py from backup..."
    cp src/voice_control.py.backup src/voice_control.py
    echo "✓ voice_control.py restored"
else
    echo "⚠ No backup found for voice_control.py"
fi

echo "Reversion complete. Restart the Bible Clock service to apply changes."
echo "To restart: sudo systemctl restart bibleclock (if using systemd)"
echo "Or stop and restart the application manually."