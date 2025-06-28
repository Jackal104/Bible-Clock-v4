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
