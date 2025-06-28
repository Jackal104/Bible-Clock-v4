# 🛡️ Pi Backup Instructions

## Quick Backup (Recommended)

**On your Pi, run this to create a backup branch:**
```bash
cd ~/Bible-Clock-v3

# Create backup branch with current working state
git checkout -b pi-working-backup-$(date +%Y%m%d)

# Add all current files (including any local changes)
git add -A

# Commit the working state
git commit -m "Pi working backup - Porcupine + Piper TTS + ChatGPT working $(date)"

# Push backup branch to GitHub
git push -u origin pi-working-backup-$(date +%Y%m%d)

# Return to main branch
git checkout main
```

## Detailed Configuration Backup

**If you want to backup specific config files:**
```bash
# Run the backup script
./pi_backup_script.sh

# Then commit the backup
git add pi_backups/
git commit -m "Pi configuration backup - $(date)"
git push
```

## What Gets Backed Up

### Working State Backup:
- ✅ All source code and current changes
- ✅ Working voice control implementation  
- ✅ Porcupine wake word detection
- ✅ Piper TTS with Amy voice
- ✅ ChatGPT integration ready
- ✅ USB audio configuration

### Config Files Backup:
- `.asoundrc` - Audio device configuration
- `.env` template - Environment variables (without secrets)
- `requirements.txt` - Python dependencies
- `start_bible_clock.sh` - Startup scripts
- System information and hardware details

## Recovery Process

**To restore from backup branch:**
```bash
# Switch to backup branch
git checkout pi-working-backup-20250622  # or your backup date

# Your Pi is now back to the working state
```

**To restore specific configs:**
```bash
# Follow instructions in pi_backups/YYYYMMDD/RESTORE_INSTRUCTIONS.md
```

## Backup Verification

**Test these work before upgrading:**
```bash
# Test microphone
arecord -f cd -d 3 test_mic.wav

# Test speakers  
aplay test_mic.wav

# Test Piper TTS
echo "Backup test" | piper --model ~/.local/share/piper/voices/en_US-amy-medium.onnx --output_file backup_test.wav
aplay backup_test.wav

# Test wake word (if Bible Clock is running)
# Say "Bible Clock help"
```

## Safety Notes

🔒 **API keys and secrets are NOT backed up to GitHub for security**
📝 **Keep a separate secure note of your API keys**
🎯 **Test the backup branch before major updates**
💾 **Consider making regular backup branches for major milestones**