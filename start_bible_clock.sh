#!/bin/bash
# Bible Clock v3.0 - Startup Script
# Activates virtual environment and starts Bible Clock

set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "📖 Starting Bible Clock v3.0..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run the setup script first: ./scripts/setup_bible_clock.sh"
    exit 1
fi

# Activate virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "❌ main.py not found!"
    echo "Please ensure you're in the Bible-Clockv2 directory"
    exit 1
fi

# Set environment variables for voice control
export ENABLE_VOICE=true
export DISPLAY_WIDTH=1872
export DISPLAY_HEIGHT=1404
export BIBLE_API_URL=https://bible-api.com
export DISPLAY_MIRROR=true
export DISPLAY_PHYSICAL_ROTATION=0
export FORCE_REFRESH_INTERVAL=60

# Start Bible Clock with voice control enabled
echo "🚀 Launching Bible Clock with voice control..."
python main.py --enable-voice