#!/bin/bash
"""
Deploy Bible Clock updates to Raspberry Pi
"""

echo "🚀 Deploying Bible Clock Updates to Pi"
echo "======================================"

# Configuration
PI_USER="${PI_USER:-pi}"
PI_HOST="${PI_HOST:-raspberrypi.local}"
PI_PATH="${PI_PATH:-/home/pi/Bible-Clockv2}"

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
ssh "${PI_USER}@${PI_HOST}" "cd $PI_PATH && git stash push -m 'Backup before update $(date)'" || {
    echo "⚠️ Could not create git backup (may not be needed)"
}

# Sync updated files
echo ""
echo "📤 Syncing updated files..."
rsync -avz --progress \
    --exclude='.git/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='venv/' \
    --exclude='test_*.py' \
    ./ "${PI_USER}@${PI_HOST}:${PI_PATH}/"

if [ $? -ne 0 ]; then
    echo "❌ File sync failed"
    exit 1
fi
echo "✅ Files synced successfully"

# Restart services on Pi
echo ""
echo "🔄 Restarting services on Pi..."
ssh "${PI_USER}@${PI_HOST}" "cd $PI_PATH && chmod +x restart_services.sh && ./restart_services.sh" || {
    echo "⚠️ Service restart may have failed - check Pi manually"
}

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Next steps:"
echo "• Check the web interface: http://${PI_HOST}:5000"
echo "• Test time formatting in the live preview"
echo "• Test voice commands if audio is working"
echo "• Look for '05:05' format instead of '5:5'"
echo ""
echo "If issues occur:"
echo "• SSH to Pi: ssh ${PI_USER}@${PI_HOST}"
echo "• Check logs: cd $PI_PATH && ./check_logs.sh"
echo "• Restore backup: cd $PI_PATH && git stash pop"