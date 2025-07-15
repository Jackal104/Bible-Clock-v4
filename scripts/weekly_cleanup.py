#!/usr/bin/env python3
"""
Bible Clock Weekly Cleanup Service
Automatically cleans log files, temporary files, and maintains disk space.
Preserves Bible translations and essential data.
"""

import os
import sys
import json
import glob
import time
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path

class BibleClockCleaner:
    def __init__(self, config_path="/home/admin/Bible-Clock-v4/scripts/cleanup_config.json"):
        self.config_path = config_path
        self.load_config()
        self.setup_logging()
        self.project_root = Path("/home/admin/Bible-Clock-v4")
        
    def load_config(self):
        """Load cleanup configuration."""
        default_config = {
            "log_retention_days": 7,
            "max_log_size_mb": 10,
            "temp_file_retention_hours": 24,
            "debug_file_retention_hours": 2,
            "audio_test_retention_hours": 6,
            "python_cache_cleanup": True,
            "preserve_patterns": [
                "data/translations/*.json",
                "images/**/*.png",
                "src/**/*.py",
                "*.md",
                "requirements*.txt",
                "piper/**/*"
            ],
            "cleanup_log_path": "/home/admin/Bible-Clock-v4/logs/cleanup.log",
            "max_cleanup_log_size_mb": 5,
            "dry_run": False
        }
        
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            else:
                # Create default config file
                os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(default_config, f, indent=2)
                    
            self.config = default_config
            
        except Exception as e:
            print(f"Error loading config, using defaults: {e}")
            self.config = default_config
    
    def setup_logging(self):
        """Setup logging for cleanup operations."""
        log_dir = os.path.dirname(self.config.get("cleanup_log_path", "/tmp/cleanup.log"))
        os.makedirs(log_dir, exist_ok=True)
        
        # Setup rotating log handler
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config["cleanup_log_path"]),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Rotate cleanup log if it's too large
        self._rotate_cleanup_log()
    
    def _rotate_cleanup_log(self):
        """Rotate the cleanup log if it's too large."""
        log_path = self.config["cleanup_log_path"]
        max_size = self.config["max_cleanup_log_size_mb"] * 1024 * 1024
        
        if os.path.exists(log_path) and os.path.getsize(log_path) > max_size:
            backup_path = f"{log_path}.old"
            if os.path.exists(backup_path):
                os.remove(backup_path)
            os.rename(log_path, backup_path)
    
    def get_file_age_hours(self, file_path):
        """Get age of file in hours."""
        try:
            mtime = os.path.getmtime(file_path)
            age_seconds = time.time() - mtime
            return age_seconds / 3600  # Convert to hours
        except OSError:
            return 0
    
    def safe_remove(self, file_path, reason="cleanup"):
        """Safely remove a file with logging."""
        try:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                if self.config["dry_run"]:
                    self.logger.info(f"[DRY RUN] Would remove {file_path} ({size:,} bytes) - {reason}")
                    return size
                else:
                    os.remove(file_path)
                    self.logger.info(f"Removed {file_path} ({size:,} bytes) - {reason}")
                    return size
            return 0
        except Exception as e:
            self.logger.error(f"Failed to remove {file_path}: {e}")
            return 0
    
    def rotate_log_file(self, log_path):
        """Rotate a log file by truncating or archiving."""
        if not os.path.exists(log_path):
            return 0
            
        size = os.path.getsize(log_path)
        max_size = self.config["max_log_size_mb"] * 1024 * 1024
        retention_days = self.config["log_retention_days"]
        
        # Check if log is too old
        age_hours = self.get_file_age_hours(log_path)
        if age_hours > (retention_days * 24):
            return self.safe_remove(log_path, f"log older than {retention_days} days")
        
        # Check if log is too large
        if size > max_size:
            if self.config["dry_run"]:
                self.logger.info(f"[DRY RUN] Would rotate large log {log_path} ({size:,} bytes)")
                return 0
            else:
                # Create compressed backup
                backup_path = f"{log_path}.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                shutil.copy2(log_path, backup_path)
                
                # Truncate original
                with open(log_path, 'w') as f:
                    f.write(f"# Log rotated at {datetime.now().isoformat()}\n")
                
                self.logger.info(f"Rotated log {log_path} (was {size:,} bytes), backup: {backup_path}")
                return size
        
        return 0
    
    def cleanup_logs(self):
        """Clean up and rotate log files."""
        self.logger.info("Starting log cleanup...")
        total_cleaned = 0
        
        # Bible Clock log files
        log_patterns = [
            "*.log",
            "logs/*.log",
            "*.log.*"  # rotated logs
        ]
        
        for pattern in log_patterns:
            for log_file in glob.glob(str(self.project_root / pattern)):
                # Skip our own cleanup log
                if log_file == self.config["cleanup_log_path"]:
                    continue
                    
                total_cleaned += self.rotate_log_file(log_file)
        
        self.logger.info(f"Log cleanup completed. Space freed: {total_cleaned:,} bytes")
        return total_cleaned
    
    def cleanup_temporary_files(self):
        """Clean up temporary files and caches."""
        self.logger.info("Starting temporary file cleanup...")
        total_cleaned = 0
        retention_hours = self.config["temp_file_retention_hours"]
        
        # Temporary file patterns
        temp_patterns = [
            "current_display.png",
            "*.tmp",
            "*.temp",
            "temp_*",
            ".env.backup",
            "*.backup"
        ]
        
        for pattern in temp_patterns:
            for temp_file in glob.glob(str(self.project_root / pattern)):
                age_hours = self.get_file_age_hours(temp_file)
                if age_hours > retention_hours:
                    total_cleaned += self.safe_remove(temp_file, f"temp file older than {retention_hours}h")
        
        # Clean up Python cache
        if self.config["python_cache_cleanup"]:
            cache_cleaned = self.cleanup_python_cache()
            total_cleaned += cache_cleaned
        
        self.logger.info(f"Temporary file cleanup completed. Space freed: {total_cleaned:,} bytes")
        return total_cleaned
    
    def cleanup_debug_files(self):
        """Clean up debug files that might be recreated."""
        self.logger.info("Starting debug file cleanup...")
        total_cleaned = 0
        retention_hours = self.config["debug_file_retention_hours"]
        
        debug_patterns = [
            "debug_*.png",
            "debug_*.py", 
            "test_*.png"
        ]
        
        for pattern in debug_patterns:
            for debug_file in glob.glob(str(self.project_root / pattern)):
                age_hours = self.get_file_age_hours(debug_file)
                if age_hours > retention_hours:
                    total_cleaned += self.safe_remove(debug_file, f"debug file older than {retention_hours}h")
        
        self.logger.info(f"Debug file cleanup completed. Space freed: {total_cleaned:,} bytes")
        return total_cleaned
    
    def cleanup_audio_test_files(self):
        """Clean up audio test files."""
        self.logger.info("Starting audio test file cleanup...")
        total_cleaned = 0
        retention_hours = self.config["audio_test_retention_hours"]
        
        audio_patterns = [
            "test*.wav",
            "mic_test*.wav", 
            "*_test.wav",
            "speech_test*.wav"
        ]
        
        for pattern in audio_patterns:
            for audio_file in glob.glob(str(self.project_root / pattern)):
                age_hours = self.get_file_age_hours(audio_file)
                if age_hours > retention_hours:
                    total_cleaned += self.safe_remove(audio_file, f"audio test file older than {retention_hours}h")
        
        self.logger.info(f"Audio test file cleanup completed. Space freed: {total_cleaned:,} bytes")
        return total_cleaned
    
    def cleanup_python_cache(self):
        """Clean up Python cache directories."""
        total_cleaned = 0
        
        # Find __pycache__ directories (excluding venv)
        for cache_dir in self.project_root.rglob("__pycache__"):
            if "venv" not in str(cache_dir):
                try:
                    if self.config["dry_run"]:
                        size = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())
                        self.logger.info(f"[DRY RUN] Would remove cache dir {cache_dir} (~{size:,} bytes)")
                        total_cleaned += size
                    else:
                        size = sum(f.stat().st_size for f in cache_dir.rglob("*") if f.is_file())
                        shutil.rmtree(cache_dir)
                        self.logger.info(f"Removed cache dir {cache_dir} ({size:,} bytes)")
                        total_cleaned += size
                except Exception as e:
                    self.logger.error(f"Failed to remove cache dir {cache_dir}: {e}")
        
        return total_cleaned
    
    def get_disk_usage(self):
        """Get current disk usage information."""
        try:
            total, used, free = shutil.disk_usage(self.project_root)
            project_size = sum(f.stat().st_size for f in self.project_root.rglob("*") if f.is_file())
            
            return {
                "total_disk_gb": total / (1024**3),
                "used_disk_gb": used / (1024**3), 
                "free_disk_gb": free / (1024**3),
                "project_size_mb": project_size / (1024**2),
                "disk_usage_percent": (used / total) * 100
            }
        except Exception as e:
            self.logger.error(f"Failed to get disk usage: {e}")
            return {}
    
    def run_cleanup(self):
        """Run the complete cleanup process."""
        start_time = datetime.now()
        self.logger.info(f"=== Bible Clock Weekly Cleanup Started ===")
        self.logger.info(f"Mode: {'DRY RUN' if self.config['dry_run'] else 'ACTIVE'}")
        
        # Get initial disk usage
        initial_usage = self.get_disk_usage()
        if initial_usage:
            self.logger.info(f"Initial disk usage: {initial_usage['disk_usage_percent']:.1f}% "
                           f"({initial_usage['used_disk_gb']:.1f}GB / {initial_usage['total_disk_gb']:.1f}GB)")
            self.logger.info(f"Project size: {initial_usage['project_size_mb']:.1f}MB")
        
        total_space_freed = 0
        
        try:
            # Run cleanup operations
            total_space_freed += self.cleanup_logs()
            total_space_freed += self.cleanup_temporary_files()
            total_space_freed += self.cleanup_debug_files()
            total_space_freed += self.cleanup_audio_test_files()
            
            # Get final disk usage
            final_usage = self.get_disk_usage()
            
            # Log summary
            duration = datetime.now() - start_time
            self.logger.info(f"=== Cleanup Completed ===")
            self.logger.info(f"Duration: {duration.total_seconds():.1f} seconds")
            self.logger.info(f"Total space freed: {total_space_freed:,} bytes ({total_space_freed/(1024**2):.1f}MB)")
            
            if final_usage:
                self.logger.info(f"Final disk usage: {final_usage['disk_usage_percent']:.1f}% "
                               f"({final_usage['used_disk_gb']:.1f}GB / {final_usage['total_disk_gb']:.1f}GB)")
                self.logger.info(f"Final project size: {final_usage['project_size_mb']:.1f}MB")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return False

def main():
    """Main entry point."""
    cleaner = BibleClockCleaner()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--dry-run":
            cleaner.config["dry_run"] = True
        elif sys.argv[1] == "--help":
            print("Bible Clock Weekly Cleanup Service")
            print("Usage:")
            print("  python weekly_cleanup.py            # Run cleanup")
            print("  python weekly_cleanup.py --dry-run  # Test cleanup (no changes)")
            print("  python weekly_cleanup.py --help     # Show this help")
            return
    
    success = cleaner.run_cleanup()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()