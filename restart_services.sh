#!/bin/bash
"""
Restart Bible Clock services to apply code changes
"""

echo "🔄 Restarting Bible Clock services..."
echo "===================================="

# Stop all Bible Clock processes
echo "📛 Stopping existing processes..."
sudo pkill -f "bible_clock" 2>/dev/null || echo "   No bible_clock processes found"
sudo pkill -f "python.*app.py" 2>/dev/null || echo "   No web server processes found"
sudo pkill -f "porcupine_voice" 2>/dev/null || echo "   No voice control processes found"

# Wait a moment for clean shutdown
sleep 2

echo "✅ Processes stopped"

# Check if we have a systemd service
if systemctl is-active --quiet bible-clock 2>/dev/null; then
    echo "🔄 Restarting systemd service..."
    sudo systemctl restart bible-clock
    echo "✅ Systemd service restarted"
elif [ -f "./start_bible_clock.sh" ]; then
    echo "🔄 Starting Bible Clock manually..."
    ./start_bible_clock.sh &
    echo "✅ Bible Clock started"
else
    echo "⚠️ No startup script found. Please start Bible Clock manually."
fi

# Wait a moment for services to start
sleep 3

echo ""
echo "🧪 Testing services..."
echo "===================="

# Check if web server is running
if curl -s http://localhost:5000 >/dev/null 2>&1; then
    echo "✅ Web server is running on port 5000"
else
    echo "❌ Web server not responding on port 5000"
fi

# Check processes
if pgrep -f "python.*app.py" >/dev/null; then
    echo "✅ Web interface process is running"
else
    echo "❌ Web interface process not found"
fi

if pgrep -f "bible_clock\|porcupine" >/dev/null; then
    echo "✅ Bible Clock main process is running"
else
    echo "❌ Bible Clock main process not found"
fi

echo ""
echo "🎯 Service restart complete!"
echo "Access your Bible Clock at: http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo "Test the time formatting fix:"
echo "• Check the live preview in the web interface"
echo "• Look for '05:05' format instead of '5:5'"
echo "• Say 'Bible Clock, what time is it' to test voice"