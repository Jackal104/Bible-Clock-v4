#!/bin/bash
# Install Bible Clock Weekly Cleanup Service
# This script sets up the systemd service and timer for automated cleanup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}Bible Clock Weekly Cleanup Service Installer${NC}"
echo "=================================================="

# Check if running as root or with sudo
if [[ $EUID -eq 0 ]]; then
    echo -e "${YELLOW}Warning: Running as root. Service will be installed system-wide.${NC}"
    INSTALL_USER="admin"
else
    INSTALL_USER="$USER"
    echo -e "${YELLOW}Running as user: $INSTALL_USER${NC}"
fi

# Verify files exist
if [[ ! -f "$SCRIPT_DIR/bible-clock-cleanup.service" ]]; then
    echo -e "${RED}Error: bible-clock-cleanup.service not found${NC}"
    exit 1
fi

if [[ ! -f "$SCRIPT_DIR/bible-clock-cleanup.timer" ]]; then
    echo -e "${RED}Error: bible-clock-cleanup.timer not found${NC}"
    exit 1
fi

if [[ ! -f "$SCRIPT_DIR/weekly_cleanup.py" ]]; then
    echo -e "${RED}Error: weekly_cleanup.py not found${NC}"
    exit 1
fi

# Create logs directory if it doesn't exist
echo "Creating logs directory..."
mkdir -p "$PROJECT_DIR/logs"

# Make cleanup script executable
echo "Making cleanup script executable..."
chmod +x "$SCRIPT_DIR/weekly_cleanup.py"

# Copy systemd files to system directory
echo "Installing systemd service and timer files..."

if [[ $EUID -eq 0 ]]; then
    # Running as root
    cp "$SCRIPT_DIR/bible-clock-cleanup.service" /etc/systemd/system/
    cp "$SCRIPT_DIR/bible-clock-cleanup.timer" /etc/systemd/system/
else
    # Running as user, need sudo
    echo "Copying service files (requires sudo)..."
    sudo cp "$SCRIPT_DIR/bible-clock-cleanup.service" /etc/systemd/system/
    sudo cp "$SCRIPT_DIR/bible-clock-cleanup.timer" /etc/systemd/system/
fi

# Update service file with correct user if needed
if [[ "$INSTALL_USER" != "admin" ]]; then
    echo "Updating service file for user: $INSTALL_USER"
    if [[ $EUID -eq 0 ]]; then
        sed -i "s/User=admin/User=$INSTALL_USER/g" /etc/systemd/system/bible-clock-cleanup.service
        sed -i "s/Group=admin/Group=$INSTALL_USER/g" /etc/systemd/system/bible-clock-cleanup.service
        sed -i "s|/home/admin/|/home/$INSTALL_USER/|g" /etc/systemd/system/bible-clock-cleanup.service
    else
        sudo sed -i "s/User=admin/User=$INSTALL_USER/g" /etc/systemd/system/bible-clock-cleanup.service
        sudo sed -i "s/Group=admin/Group=$INSTALL_USER/g" /etc/systemd/system/bible-clock-cleanup.service
        sudo sed -i "s|/home/admin/|/home/$INSTALL_USER/|g" /etc/systemd/system/bible-clock-cleanup.service
    fi
fi

# Reload systemd
echo "Reloading systemd daemon..."
if [[ $EUID -eq 0 ]]; then
    systemctl daemon-reload
else
    sudo systemctl daemon-reload
fi

# Enable and start the timer
echo "Enabling and starting the cleanup timer..."
if [[ $EUID -eq 0 ]]; then
    systemctl enable bible-clock-cleanup.timer
    systemctl start bible-clock-cleanup.timer
else
    sudo systemctl enable bible-clock-cleanup.timer
    sudo systemctl start bible-clock-cleanup.timer
fi

# Show status
echo "Checking timer status..."
if [[ $EUID -eq 0 ]]; then
    systemctl status bible-clock-cleanup.timer --no-pager -l
else
    sudo systemctl status bible-clock-cleanup.timer --no-pager -l
fi

echo ""
echo -e "${GREEN}Installation completed successfully!${NC}"
echo ""
echo "The cleanup service is now scheduled to run:"
echo "  - Every Sunday at 3:00 AM (± 30 minutes)"
echo "  - 10 minutes after system boot"
echo ""
echo "You can:"
echo "  - Test the cleanup manually: python3 $SCRIPT_DIR/weekly_cleanup.py --dry-run"
echo "  - Run cleanup immediately: sudo systemctl start bible-clock-cleanup.service"
echo "  - Check timer status: sudo systemctl status bible-clock-cleanup.timer"
echo "  - View cleanup logs: tail -f $PROJECT_DIR/logs/cleanup.log"
echo "  - Disable service: sudo systemctl disable bible-clock-cleanup.timer"
echo ""
echo "Configuration file: $SCRIPT_DIR/cleanup_config.json"