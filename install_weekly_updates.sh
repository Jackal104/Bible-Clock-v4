#!/bin/bash
# Install Weekly Automatic Updates for Bible Clock
# Sets up cron job and systemd service for reliable updates

echo "🔄 Installing Bible Clock Weekly Update System"
echo "=============================================="

# Get the current directory
BIBLE_CLOCK_DIR="$(pwd)"
USER_NAME="$(whoami)"

echo "📁 Bible Clock directory: $BIBLE_CLOCK_DIR"
echo "👤 User: $USER_NAME"

# Make scripts executable
chmod +x system_updater.py
chmod +x bible_clock_voice_modern.py

# Create systemd service for updates
echo "📝 Creating systemd service..."
sudo tee /etc/systemd/system/bible-clock-updater.service > /dev/null << EOF
[Unit]
Description=Bible Clock System Updater
After=network.target

[Service]
Type=oneshot
User=$USER_NAME
WorkingDirectory=$BIBLE_CLOCK_DIR
Environment=PATH=$BIBLE_CLOCK_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
ExecStart=$BIBLE_CLOCK_DIR/venv/bin/python $BIBLE_CLOCK_DIR/system_updater.py
StandardOutput=journal
StandardError=journal
EOF

# Create systemd timer for weekly updates
echo "⏰ Creating weekly timer..."
sudo tee /etc/systemd/system/bible-clock-updater.timer > /dev/null << EOF
[Unit]
Description=Run Bible Clock updater weekly
Requires=bible-clock-updater.service

[Timer]
# Run every Sunday at 3:00 AM
OnCalendar=Sun *-*-* 03:00:00
# Run immediately if the system was off during the scheduled time
Persistent=true
# Add some randomization to avoid all systems updating at once
RandomizedDelaySec=1800

[Install]
WantedBy=timers.target
EOF

# Reload systemd and enable timer
echo "🔧 Enabling systemd timer..."
sudo systemctl daemon-reload
sudo systemctl enable bible-clock-updater.timer
sudo systemctl start bible-clock-updater.timer

# Create manual update script
echo "📜 Creating manual update script..."
cat > manual_update.sh << 'EOF'
#!/bin/bash
echo "🔄 Manual Bible Clock Update"
echo "=========================="

cd "$(dirname "$0")"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Run updater
python3 system_updater.py update

echo "Update process completed."
EOF

chmod +x manual_update.sh

# Create status check script
echo "📊 Creating status check script..."
cat > check_system_status.sh << 'EOF'
#!/bin/bash
echo "📊 Bible Clock System Status"
echo "=========================="

cd "$(dirname "$0")"

# Check git status
echo "📁 Git Status:"
git status --porcelain

# Check last update
echo -e "\n⏰ Update Status:"
if [ -d "venv" ]; then
    source venv/bin/activate
fi
python3 system_updater.py status

# Check systemd timer
echo -e "\n🕐 Timer Status:"
sudo systemctl status bible-clock-updater.timer --no-pager -l

# Check system health
echo -e "\n💚 System Health:"
echo "Disk usage: $(df -h . | tail -1 | awk '{print $5}') used"
echo "Memory usage: $(free -h | grep '^Mem:' | awk '{print $3"/"$2}')"
echo "Load average: $(uptime | awk -F'load average:' '{print $2}')"

# Check voice control dependencies
echo -e "\n🎤 Voice Control Dependencies:"
python3 -c "
try:
    import speech_recognition; print('✅ speech_recognition')
except: print('❌ speech_recognition')
try:
    import openai; print('✅ openai')
except: print('❌ openai')
try:
    import pyaudio; print('✅ pyaudio')
except: print('❌ pyaudio')
"
EOF

chmod +x check_system_status.sh

# Create update configuration
echo "⚙️ Creating update configuration..."
python3 -c "
import json
config = {
    'auto_update_enabled': True,
    'update_frequency_days': 7,
    'backup_retention_days': 30,
    'post_update_hooks': [
        'systemctl --user restart bible-clock.service 2>/dev/null || true'
    ],
    'critical_files': [
        '.env',
        'bible_clock_voice_modern.py',
        'requirements-locked.txt',
        'src/**/*.py'
    ]
}
with open('updater_config.json', 'w') as f:
    json.dump(config, f, indent=2)
print('✅ Configuration created')
"

# Test the system
echo "🧪 Testing update system..."
if [ -d "venv" ]; then
    source venv/bin/activate
fi

python3 system_updater.py status

echo ""
echo "✅ Weekly Update System Installation Complete!"
echo "=============================================="
echo ""
echo "📋 What was installed:"
echo "• Systemd service: bible-clock-updater.service"
echo "• Weekly timer: bible-clock-updater.timer (Sundays at 3 AM)"
echo "• Manual update script: ./manual_update.sh"
echo "• Status checker: ./check_system_status.sh"
echo "• Backup system with 30-day retention"
echo "• Version-locked dependencies"
echo ""
echo "🎮 Usage Commands:"
echo "• Check status: ./check_system_status.sh"
echo "• Manual update: ./manual_update.sh"
echo "• View timer: sudo systemctl status bible-clock-updater.timer"
echo "• View logs: sudo journalctl -u bible-clock-updater.service"
echo ""
echo "🔧 The system will automatically:"
echo "• Check for updates every Sunday at 3 AM"
echo "• Create backups before updates"
echo "• Rollback if updates fail"
echo "• Clean up old backups after 30 days"
echo "• Maintain version compatibility"
echo ""
echo "✅ Your Bible Clock will stay up-to-date automatically!"