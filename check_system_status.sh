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
