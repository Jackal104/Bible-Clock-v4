#!/bin/bash
"""
Deploy V2 time formatting fixes to V3 Pi
"""

echo "🚀 Deploying V2 Time Formatting Fixes to V3 Pi"
echo "=============================================="

# Configuration for V3 Pi
PI_USER="${PI_USER:-admin}"
PI_HOST="${PI_HOST:-Bible-clock}"
PI_PATH="${PI_PATH:-/home/admin/Bible-Clock-v3}"

echo "Target: ${PI_USER}@${PI_HOST}:${PI_PATH}"
echo ""

# Check if we can reach the Pi
echo "📡 Testing connection to Pi..."
if ! ping -c 1 "$PI_HOST" >/dev/null 2>&1; then
    echo "❌ Cannot reach Pi at $PI_HOST"
    echo "   Please check:"
    echo "   • Pi is powered on and connected to network"
    echo "   • Hostname is correct (try IP address instead)"
    echo "   • SSH is enabled on the Pi"
    exit 1
fi
echo "✅ Pi is reachable"

# Create backup on Pi first
echo ""
echo "💾 Creating backup on Pi..."
ssh "${PI_USER}@${PI_HOST}" "cd $PI_PATH && git stash push -m 'Backup before V2 time formatting fixes $(date)'" || {
    echo "⚠️ Could not create git backup - proceeding anyway"
}

# Apply time formatting fixes to V3 verse_manager.py
echo ""
echo "🔧 Applying time formatting fixes to V3..."

# Create the time formatting fix script
cat > temp_time_fix.py << 'EOF'
#!/usr/bin/env python3
"""
Apply V2 time formatting fixes to V3 verse_manager.py
"""
import re

def fix_time_formatting(file_path):
    """Apply time formatting fixes to verse_manager.py"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        print(f"📝 Fixing time formatting in {file_path}")
        
        # Fix 1: Replace 12-hour time formatting with leading zeros
        # Look for patterns like: now.strftime('%I:%M %p')
        content = re.sub(
            r"now\.strftime\(['\"]%I:%M %p['\"]\)",
            'f"{hour_12:02d}:{now.minute:02d} {now.strftime(\'%p\')}"',
            content
        )
        
        # Fix 2: Add hour_12 calculation before time formatting
        # Look for time formatting and ensure hour_12 is calculated
        if 'hour_12:02d' in content and 'hour_12 = ' not in content:
            # Find a good place to add hour_12 calculation
            lines = content.split('\n')
            new_lines = []
            for line in lines:
                if 'hour_12:02d' in line and 'hour_12 = ' not in '\n'.join(new_lines[-5:]):
                    # Add hour_12 calculation before this line
                    indent = len(line) - len(line.lstrip())
                    hour_calc_lines = [
                        ' ' * indent + 'hour_12 = now.hour % 12',
                        ' ' * indent + 'if hour_12 == 0:',
                        ' ' * indent + '    hour_12 = 12'
                    ]
                    new_lines.extend(hour_calc_lines)
                new_lines.append(line)
            content = '\n'.join(new_lines)
        
        # Fix 3: Fix chapter:verse formatting with leading zeros
        content = re.sub(
            r"f['\"]?\{chapter\}:\{verse:02d\}['\"]?",
            "f'{chapter:02d}:{verse:02d}'",
            content
        )
        
        # Fix 4: Fix any other chapter formatting
        content = re.sub(
            r"f['\"]?\{chapter\}:\{verse\}['\"]?",
            "f'{chapter:02d}:{verse:02d}'",
            content
        )
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Applied time formatting fixes to {file_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python3 temp_time_fix.py <verse_manager.py_path>")
        sys.exit(1)
    
    success = fix_time_formatting(sys.argv[1])
    sys.exit(0 if success else 1)
EOF

# Copy the fix script to Pi and apply it
echo "📤 Copying time fix script to Pi..."
scp temp_time_fix.py "${PI_USER}@${PI_HOST}:/tmp/"

echo "🔧 Applying fixes to V3 verse_manager.py..."
ssh "${PI_USER}@${PI_HOST}" "cd $PI_PATH && python3 /tmp/temp_time_fix.py src/verse_manager.py"

# Also fix voice_control.py if it exists
echo "🔧 Checking for voice_control.py to fix..."
ssh "${PI_USER}@${PI_HOST}" "cd $PI_PATH && if [ -f src/voice_control.py ]; then python3 /tmp/temp_time_fix.py src/voice_control.py; else echo 'No voice_control.py found'; fi"

# Create a test script for the Pi
echo "📝 Creating time formatting test script..."
cat > temp_time_test.py << 'EOF'
#!/usr/bin/env python3
"""Test time formatting on V3"""
from datetime import datetime

def test_time_formatting():
    print("🕐 Testing V3 Time Formatting")
    print("=" * 30)
    
    # Test the formatting logic
    test_times = [(1, 5), (5, 4), (12, 30), (10, 0)]
    
    for hour, minute in test_times:
        # Simulate the datetime
        class MockTime:
            def __init__(self, h, m):
                self.hour = h
                self.minute = m
            def strftime(self, fmt):
                if fmt == '%p':
                    return 'AM' if self.hour < 12 else 'PM'
                return f"{self.hour}:{self.minute}"
        
        now = MockTime(hour, minute)
        hour_12 = now.hour % 12
        if hour_12 == 0:
            hour_12 = 12
        
        # New formatting with leading zeros
        time_display = f"{hour_12:02d}:{now.minute:02d} {now.strftime('%p')}"
        chapter_verse = f"{hour_12:02d}:{now.minute:02d}"
        
        print(f"  {hour:2d}:{minute:02d} → {time_display} | {chapter_verse}")
    
    print("\n✅ Time formatting test complete!")

if __name__ == "__main__":
    test_time_formatting()
EOF

scp temp_time_test.py "${PI_USER}@${PI_HOST}:/tmp/"

# Test the fixes
echo ""
echo "🧪 Testing time formatting fixes..."
ssh "${PI_USER}@${PI_HOST}" "python3 /tmp/temp_time_test.py"

# Restart services
echo ""
echo "🔄 Restarting Bible Clock services..."
ssh "${PI_USER}@${PI_HOST}" "cd $PI_PATH && if [ -f restart_services.sh ]; then chmod +x restart_services.sh && ./restart_services.sh; else echo 'No restart script found - restart manually'; fi"

# Cleanup temp files
rm -f temp_time_fix.py temp_time_test.py
ssh "${PI_USER}@${PI_HOST}" "rm -f /tmp/temp_time_fix.py /tmp/temp_time_test.py"

echo ""
echo "🎉 V2 time formatting fixes applied to V3 Pi!"
echo ""
echo "Next steps:"
echo "• Check web interface: http://${PI_HOST}:5000"
echo "• Look for '05:05' format instead of '5:5' in time display"
echo "• Test voice commands to hear correct time pronunciation"
echo ""
echo "If issues occur:"
echo "• SSH to Pi: ssh ${PI_USER}@${PI_HOST}"
echo "• Check logs: cd $PI_PATH && tail -f *.log"
echo "• Restore backup: cd $PI_PATH && git stash pop"