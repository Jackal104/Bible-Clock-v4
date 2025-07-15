#!/bin/bash
# Fix Bible Clock time synchronization on boot

echo "🕐 Fixing Bible Clock time synchronization..."

# Backup original service file
sudo cp /etc/systemd/system/bible-clock.service /etc/systemd/system/bible-clock.service.backup

# Create updated service file
cat << 'EOF' | sudo tee /etc/systemd/system/bible-clock.service > /dev/null
[Unit]
Description=Bible Clock E-ink Display Service
After=network.target systemd-timesyncd.service
Wants=network.target systemd-timesyncd.service
Requires=systemd-timesyncd.service

[Service]
Type=simple
User=admin
Group=admin
WorkingDirectory=/home/admin/Bible-Clock-v4
Environment="PATH=/home/admin/Bible-Clock-v4/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
EnvironmentFile=/home/admin/Bible-Clock-v4/.env
ExecStart=/bin/bash /home/admin/Bible-Clock-v4/start_bible_clock.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=false
ProtectHome=false

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and restart service
echo "🔄 Reloading systemd configuration..."
sudo systemctl daemon-reload

echo "✅ Bible Clock service updated to wait for time synchronization"
echo "🔄 Restart the service to apply changes:"
echo "   sudo systemctl restart bible-clock"
echo ""
echo "📋 Changes made:"
echo "   - Added dependency on systemd-timesyncd.service"
echo "   - Bible Clock will now wait for NTP sync before starting"
echo "   - Service will only start after system time is synchronized"