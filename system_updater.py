#!/usr/bin/env python3
"""
Bible Clock System Updater
Automatic weekly updates with rollback capability and version management
"""

import os
import sys
import subprocess
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import psutil

# Configure logging
log_file = Path.home() / 'bible-clock-updater.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BibleClockUpdater:
    def __init__(self):
        self.repo_url = "https://github.com/Jackal104/Bible-Clockv2.git"
        self.project_dir = Path.cwd()
        self.backup_dir = Path.home() / "bible-clock-backups"
        self.config_file = self.project_dir / "updater_config.json"
        self.requirements_locked = self.project_dir / "requirements-locked.txt"
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        
        # Load configuration
        self.config = self._load_config()
    
    def _load_config(self):
        """Load updater configuration."""
        default_config = {
            "auto_update_enabled": True,
            "update_frequency_days": 7,
            "last_update_check": None,
            "last_successful_update": None,
            "backup_retention_days": 30,
            "pre_update_hooks": [],
            "post_update_hooks": [],
            "critical_files": [
                ".env",
                "bible_clock_voice_modern.py",
                "requirements-locked.txt"
            ]
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file) as f:
                    config = json.load(f)
                # Merge with defaults
                for key, value in default_config.items():
                    if key not in config:
                        config[key] = value
                return config
            except Exception as e:
                logger.error(f"Error loading config: {e}")
        
        return default_config
    
    def _save_config(self):
        """Save updater configuration."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def check_for_updates(self):
        """Check if updates are available."""
        try:
            # Fetch latest changes
            result = subprocess.run(['git', 'fetch', 'origin'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"Git fetch failed: {result.stderr}")
                return False
            
            # Check if we're behind
            result = subprocess.run(['git', 'rev-list', '--count', 'HEAD..origin/main'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                commits_behind = int(result.stdout.strip())
                if commits_behind > 0:
                    logger.info(f"Updates available: {commits_behind} commits behind")
                    return True
                else:
                    logger.info("No updates available")
                    return False
            else:
                logger.error(f"Error checking updates: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
            return False
    
    def create_backup(self):
        """Create a backup of the current system."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}"
            
            logger.info(f"Creating backup: {backup_path}")
            
            # Copy critical files and directories
            backup_path.mkdir()
            
            # Backup critical files
            for file_pattern in self.config["critical_files"]:
                for file_path in self.project_dir.glob(file_pattern):
                    if file_path.is_file():
                        shutil.copy2(file_path, backup_path)
                        logger.info(f"Backed up: {file_path.name}")
            
            # Backup src directory
            src_dir = self.project_dir / "src"
            if src_dir.exists():
                shutil.copytree(src_dir, backup_path / "src")
                logger.info("Backed up src directory")
            
            # Backup voice models if they exist
            voices_dir = Path.home() / ".local/share/piper/voices"
            if voices_dir.exists():
                backup_voices = backup_path / "voices"
                shutil.copytree(voices_dir, backup_voices)
                logger.info("Backed up voice models")
            
            # Save system info
            system_info = {
                "timestamp": timestamp,
                "python_version": sys.version,
                "pip_freeze": subprocess.run(['pip', 'freeze'], 
                                           capture_output=True, text=True).stdout,
                "git_commit": subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                           capture_output=True, text=True).stdout.strip(),
                "system_load": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else "N/A",
                "disk_usage": shutil.disk_usage(self.project_dir)._asdict()
            }
            
            with open(backup_path / "system_info.json", 'w') as f:
                json.dump(system_info, f, indent=2, default=str)
            
            logger.info(f"Backup created successfully: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            return None
    
    def update_system(self):
        """Update the system with rollback capability."""
        try:
            logger.info("Starting system update...")
            
            # Create backup first
            backup_path = self.create_backup()
            if not backup_path:
                logger.error("Backup failed, aborting update")
                return False
            
            # Store current commit for rollback
            current_commit = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                          capture_output=True, text=True).stdout.strip()
            
            try:
                # Pull latest changes
                result = subprocess.run(['git', 'pull', 'origin', 'main'], 
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"Git pull failed: {result.stderr}")
                
                logger.info("Code updated successfully")
                
                # Update dependencies with locked versions
                if self.requirements_locked.exists():
                    logger.info("Updating dependencies...")
                    result = subprocess.run([sys.executable, '-m', 'pip', 'install', 
                                           '-r', str(self.requirements_locked)], 
                                          capture_output=True, text=True)
                    if result.returncode != 0:
                        logger.warning(f"Some dependencies failed to update: {result.stderr}")
                    else:
                        logger.info("Dependencies updated successfully")
                
                # Run post-update hooks
                self._run_hooks(self.config["post_update_hooks"])
                
                # Test the system
                if self._test_system():
                    logger.info("System update completed successfully")
                    self.config["last_successful_update"] = datetime.now().isoformat()
                    self._save_config()
                    
                    # Clean old backups
                    self._cleanup_old_backups()
                    return True
                else:
                    logger.error("System test failed, rolling back...")
                    self._rollback(current_commit)
                    return False
                    
            except Exception as e:
                logger.error(f"Update failed: {e}")
                logger.info("Rolling back to previous version...")
                self._rollback(current_commit)
                return False
                
        except Exception as e:
            logger.error(f"Update process failed: {e}")
            return False
    
    def _rollback(self, commit_hash):
        """Rollback to a previous commit."""
        try:
            logger.info(f"Rolling back to commit: {commit_hash}")
            result = subprocess.run(['git', 'reset', '--hard', commit_hash], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Rollback completed successfully")
                return True
            else:
                logger.error(f"Rollback failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Rollback error: {e}")
            return False
    
    def _test_system(self):
        """Test system functionality after update."""
        try:
            logger.info("Testing system functionality...")
            
            # Test Python imports
            test_imports = [
                "src.verse_manager",
                "speech_recognition",
                "openai"
            ]
            
            for module in test_imports:
                try:
                    __import__(module)
                    logger.info(f"✅ Import test passed: {module}")
                except ImportError as e:
                    logger.error(f"❌ Import test failed: {module} - {e}")
                    return False
            
            # Test voice control initialization
            try:
                from bible_clock_voice_modern import ModernBibleClockVoice
                voice_system = ModernBibleClockVoice()
                if voice_system.enabled:
                    logger.info("✅ Voice control initialization test passed")
                else:
                    logger.warning("⚠️ Voice control disabled but no errors")
            except Exception as e:
                logger.error(f"❌ Voice control test failed: {e}")
                return False
            
            logger.info("All system tests passed")
            return True
            
        except Exception as e:
            logger.error(f"System test error: {e}")
            return False
    
    def _run_hooks(self, hooks):
        """Run custom hooks."""
        for hook in hooks:
            try:
                logger.info(f"Running hook: {hook}")
                result = subprocess.run(hook, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"Hook completed: {hook}")
                else:
                    logger.warning(f"Hook failed: {hook} - {result.stderr}")
            except Exception as e:
                logger.error(f"Hook error: {hook} - {e}")
    
    def _cleanup_old_backups(self):
        """Clean up old backups."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config["backup_retention_days"])
            
            for backup_dir in self.backup_dir.glob("backup_*"):
                if backup_dir.is_dir():
                    # Extract timestamp from directory name
                    timestamp_str = backup_dir.name.replace("backup_", "")
                    try:
                        backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                        if backup_date < cutoff_date:
                            shutil.rmtree(backup_dir)
                            logger.info(f"Cleaned up old backup: {backup_dir.name}")
                    except ValueError:
                        # Skip directories with invalid timestamp format
                        continue
                        
        except Exception as e:
            logger.error(f"Backup cleanup error: {e}")
    
    def should_update(self):
        """Check if an update should be performed."""
        if not self.config["auto_update_enabled"]:
            return False
        
        last_check = self.config.get("last_update_check")
        if not last_check:
            return True
        
        last_check_date = datetime.fromisoformat(last_check)
        days_since_check = (datetime.now() - last_check_date).days
        
        return days_since_check >= self.config["update_frequency_days"]
    
    def run_update_check(self):
        """Run the complete update check and update process."""
        logger.info("Starting update check...")
        
        # Update last check time
        self.config["last_update_check"] = datetime.now().isoformat()
        self._save_config()
        
        if not self.should_update():
            logger.info("Update not needed at this time")
            return True
        
        if self.check_for_updates():
            logger.info("Updates available, starting update process...")
            return self.update_system()
        else:
            logger.info("No updates available")
            return True

def main():
    """Main function for the updater."""
    print("🔄 Bible Clock System Updater")
    print("=" * 40)
    
    updater = BibleClockUpdater()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "check":
            print("Checking for updates...")
            if updater.check_for_updates():
                print("✅ Updates available")
                sys.exit(0)
            else:
                print("✅ No updates available")
                sys.exit(1)
                
        elif command == "update":
            print("Starting update process...")
            if updater.update_system():
                print("✅ Update completed successfully")
                sys.exit(0)
            else:
                print("❌ Update failed")
                sys.exit(1)
                
        elif command == "backup":
            print("Creating backup...")
            backup_path = updater.create_backup()
            if backup_path:
                print(f"✅ Backup created: {backup_path}")
                sys.exit(0)
            else:
                print("❌ Backup failed")
                sys.exit(1)
                
        elif command == "status":
            config = updater.config
            print(f"Auto-update enabled: {config['auto_update_enabled']}")
            print(f"Update frequency: {config['update_frequency_days']} days")
            print(f"Last check: {config.get('last_update_check', 'Never')}")
            print(f"Last update: {config.get('last_successful_update', 'Never')}")
            sys.exit(0)
            
        else:
            print(f"Unknown command: {command}")
            print("Available commands: check, update, backup, status")
            sys.exit(1)
    else:
        # Run automatic update check
        if updater.run_update_check():
            print("✅ Update check completed")
            sys.exit(0)
        else:
            print("❌ Update check failed")
            sys.exit(1)

if __name__ == "__main__":
    main()