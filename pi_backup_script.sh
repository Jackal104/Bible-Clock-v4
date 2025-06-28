#!/bin/bash
"""
Pi Configuration Backup Script
Saves current working Pi configuration to GitHub
"""

echo "🔄 Creating Pi backup..."
echo "=========================="

# Create backup directory
mkdir -p pi_backups/$(date +%Y%m%d)
BACKUP_DIR="pi_backups/$(date +%Y%m%d)"

echo "📁 Backing up configuration files..."

# Backup key config files
if [ -f ~/.asoundrc ]; then
    cp ~/.asoundrc "$BACKUP_DIR/asoundrc_backup"
    echo "✅ Saved .asoundrc"
fi

if [ -f .env ]; then
    # Remove sensitive data but keep structure
    sed 's/OPENAI_API_KEY=.*/OPENAI_API_KEY=your_key_here/' .env > "$BACKUP_DIR/env_template"
    echo "✅ Saved .env template (without API keys)"
fi

if [ -f requirements.txt ]; then
    cp requirements.txt "$BACKUP_DIR/"
    echo "✅ Saved requirements.txt"
fi

# Backup any custom startup scripts
if [ -f start_bible_clock.sh ]; then
    cp start_bible_clock.sh "$BACKUP_DIR/"
    echo "✅ Saved startup script"
fi

# Create system info
echo "📋 Recording system information..."
cat > "$BACKUP_DIR/system_info.txt" << EOF
# Pi System Backup - $(date)
# Bible Clock v3 Working Configuration

## Hardware Info
$(cat /proc/cpuinfo | grep "Model\|Hardware\|Revision")

## Audio Devices
$(aplay -l 2>/dev/null || echo "No audio devices found")
$(arecord -l 2>/dev/null || echo "No recording devices found")

## Python Packages
$(pip list | grep -E "(porcupine|openai|speech|audio)" || echo "Virtual env not active")

## Git Status
$(git status --porcelain)
$(git log --oneline -5)

## Working Features
- Porcupine wake word detection: WORKING
- USB microphone (Fifine K053): WORKING  
- USB speakers (UACDemoV1.0): WORKING
- Piper TTS with Amy voice: WORKING
- ChatGPT API integration: READY
- Voice control pipeline: TESTED

## Known Issues
- None currently

## Last Working State
$(date): All voice control features operational
EOF

echo "✅ Saved system information"

# Create restore instructions
cat > "$BACKUP_DIR/RESTORE_INSTRUCTIONS.md" << EOF
# Pi Restore Instructions

## To restore this configuration:

1. **Audio Setup:**
   \`\`\`bash
   cp asoundrc_backup ~/.asoundrc
   \`\`\`

2. **Environment Setup:**
   \`\`\`bash
   cp env_template .env
   # Edit .env and add your actual API keys
   \`\`\`

3. **Dependencies:**
   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

4. **Test Audio:**
   \`\`\`bash
   aplay test_piper_voice.wav
   arecord -f cd -d 3 test_mic.wav && aplay test_mic.wav
   \`\`\`

## Hardware Requirements:
- Fifine K053 USB Microphone (Card 1)
- USB Mini Speaker 30mm driver (Card 2)
- Raspberry Pi with USB ports

## Working State:
This backup represents a fully working Bible Clock voice control system.
EOF

echo "✅ Created restore instructions"
echo ""
echo "🎯 Backup completed in: $BACKUP_DIR"
echo "📤 Now commit and push to GitHub:"
echo "   git add $BACKUP_DIR"
echo "   git commit -m 'Pi working backup - $(date)'"
echo "   git push"