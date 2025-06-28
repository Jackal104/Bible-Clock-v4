#!/bin/bash
# Bible Clock v3.0 - Hostname Setup Script
# Configures 'bible-clock' hostname resolution for web interface access

set -e

echo "📖 Bible Clock - Hostname Setup"
echo "================================"
echo ""

# Check if running as root or with sudo capabilities
if [[ $EUID -eq 0 ]]; then
    SUDO=""
elif sudo -n true 2>/dev/null; then
    SUDO="sudo"
else
    echo "❌ This script requires sudo privileges to modify system files"
    echo "Please run with: sudo $0"
    exit 1
fi

# Get current directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "📁 Project directory: $PROJECT_DIR"
echo ""

# Configure hostname resolution in /etc/hosts
echo "🔧 Configuring hostname resolution..."

# Check if bible-clock entry already exists
if grep -q "bible-clock" /etc/hosts; then
    echo "ℹ️  'bible-clock' hostname already configured in /etc/hosts"
else
    # Add bible-clock hostname pointing to localhost
    echo "127.0.0.1    bible-clock" | $SUDO tee -a /etc/hosts > /dev/null
    echo "✅ Added 'bible-clock' hostname to /etc/hosts"
fi

# Set WEB_HOST environment variable in .env
echo ""
echo "⚙️  Updating configuration..."

ENV_FILE="$PROJECT_DIR/.env"
if [ -f "$ENV_FILE" ]; then
    # Check if WEB_HOST is already set
    if grep -q "^WEB_HOST=" "$ENV_FILE"; then
        # Update existing WEB_HOST
        sed -i 's/^WEB_HOST=.*/WEB_HOST=bible-clock/' "$ENV_FILE"
        echo "✅ Updated WEB_HOST=bible-clock in .env"
    else
        # Add WEB_HOST setting
        echo "" >> "$ENV_FILE"
        echo "# Web Interface Hostname" >> "$ENV_FILE"
        echo "WEB_HOST=bible-clock" >> "$ENV_FILE"
        echo "✅ Added WEB_HOST=bible-clock to .env"
    fi
else
    echo "⚠️  .env file not found. Creating basic configuration..."
    cat > "$ENV_FILE" << EOF
# Bible Clock v3.0 Configuration
# Web Interface Hostname
WEB_HOST=bible-clock
WEB_PORT=5000
EOF
    echo "✅ Created .env with hostname configuration"
fi

echo ""
echo "🎉 Hostname setup completed!"
echo ""
echo "📋 Configuration Summary:"
echo "• Added 'bible-clock' hostname to /etc/hosts (127.0.0.1)"
echo "• Set WEB_HOST=bible-clock in .env file"
echo ""
echo "🌐 Web interface will be accessible at:"
echo "   http://bible-clock:5000"
echo "   http://localhost:5000"
echo "   http://127.0.0.1:5000"
echo ""
echo "📚 To test the configuration:"
echo "1. Start Bible Clock: python3 main.py"
echo "2. Open browser to: http://bible-clock:5000"
echo ""
echo "💡 To revert this change:"
echo "   sudo sed -i '/bible-clock/d' /etc/hosts"
echo "   sed -i 's/WEB_HOST=bible-clock/WEB_HOST=0.0.0.0/' \"$ENV_FILE\""